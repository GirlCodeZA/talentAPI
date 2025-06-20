import uuid
from datetime import datetime
from typing import List

from app.models.employer import EmployerProfile
from app.models.jobs import JobModel
from app.models.matched import MatchedJob
from app.models.models import ProgressModel, ProgressStep, BasicInformation, Education, JobPreference, WorkExperience, \
    Projects, Awards, Account, StatusUpdateSchema, ResumeRequest
from app.utils.candidate_helpers import fetch_candidate_by_email
from app.utils.s3_helpers import generate_signed_url, upload_file_to_s3
from app.settings import settings
import boto3
import io

from botocore.config import Config

from botocore.exceptions import NoCredentialsError

from fastapi import APIRouter, HTTPException, Body, Query, File, UploadFile, Request
from fastapi.responses import JSONResponse, StreamingResponse
from firebase_admin import firestore
from typing import Optional
from reportlab.pdfgen import canvas
from weasyprint import HTML
import logging
logger = logging.getLogger("uvicorn")
from jinja2 import Environment, FileSystemLoader


env = Environment(loader=FileSystemLoader("app/templates"))

from app.firebase import db

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_key,
    config=Config(
        signature_version="s3v4",
        s3={'addressing_style': 'virtual'}
    )
)

db = firestore.client()
candidate_router = APIRouter()

@candidate_router.get("/candidate", tags=["Candidate Management"])
async def get_candidate_by_email(email: str = Query(...)):
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate = None
        candidate_id = None

        for doc in query:
            candidate = doc.to_dict()
            candidate_id = doc.id
            break

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        default_steps = ProgressModel.default_steps()
        progress_steps_data = candidate.get("progressSteps", {})

        sorted_progress_steps = {
            step: ProgressStep(**progress_steps_data.get(step, default_steps[step])).dict()
            for step in default_steps
        }

        file_key = candidate.get("profilePicture")
        if file_key:
            candidate["profilePictureSignedUrl"] = generate_signed_url(file_key)

        response = {
            "id": candidate_id,
            **candidate,
            "progressSteps": sorted_progress_steps
        }

        return JSONResponse(content=response, status_code=200)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching candidate: {str(e)}"
        )

@candidate_router.put("/status", tags=["Candidate Management"])
async def update_candidate_status(data: StatusUpdateSchema):
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", data.email).stream()

        updated = False
        for doc in query:
            doc_ref = candidates_ref.document(doc.id)
            doc_ref.update({"status": data.status})
            updated = True

        if not updated:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return JSONResponse(
            content={"message": f"Status updated to {data.status} for {data.email}"},
            status_code=200
        )

    except Exception as e:
        print("Error updating candidate status:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

@candidate_router.post("/update-picture", tags=["Candidate Management"])
async def upload_image(
        email: str = Query(...),
        file: UploadFile = File(...)
):
    try:
        file_url = upload_file_to_s3(file, folder="profile-pictures")

        # Extract just the S3 key (for saving in Firestore)
        file_key = file_url.split(".com/")[-1]

        # Update Firestore
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()
        candidate_docs = [doc for doc in query]

        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_ref = candidates_ref.document(candidate_docs[0].id)
        candidate_ref.update({"profilePicture": file_key})

        # Generate signed URL for frontend use
        signed_url = generate_signed_url(file_key)

        return {
            "message": "Profile picture updated successfully",
            "file_key": file_key,
            "profilePictureSignedUrl": signed_url
        }

    except NoCredentialsError:
        return {"error": "Credentials not available"}
    except Exception as e:
        return {"error": str(e)}


@candidate_router.post("/upload-file", tags=["Candidate Management"])
async def upload_education_file(
        email: str = Query(...),
        index: int = Query(...),  # index of the education entry to update
        file: UploadFile = File(...),
        folder: Optional[str] = Query("education-documents")
):
    """
    Upload a file to S3 and attach the fileUrl to the candidate's education[index].
    """
    try:
        # Upload file
        file_url = upload_file_to_s3(file, folder)
        file_key = file_url.split(".com/")[-1]
        logger.info(f"Uploaded file to S3: {file_key}")

        # Update candidate's education[n].fileUrl
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()
        candidate_docs = [doc for doc in query]

        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_data = candidate_doc.to_dict()

        education_list = candidate_data.get("education", [])

        # Auto-extend the list to ensure the index is valid
        while len(education_list) <= index:
            education_list.append({
                "institution": "",
                "degree": "",
                "fileUrl": ""
            })

        # Update fileUrl at the correct index
        education_list[index]["fileUrl"] = file_key

        # Save updated education list
        candidate_ref = candidates_ref.document(candidate_doc.id)
        candidate_ref.update({"education": education_list})

        # Generate signed URL
        signed_url = generate_signed_url(file_key)

        return {
            "message": "Education file uploaded and updated successfully",
            "file_key": file_key,
            "fileUrlSigned": signed_url
        }

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials missing")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



@candidate_router.put("/save-progress", tags=["Candidate Management"])
async def save_progress(
        email: str = Query(..., example="user@example.com"),
        progress_data: ProgressModel = Body(...)
):
    """
    Updates the progressSteps field for a candidate in Firestore by email.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        existing_progress = candidate_doc.to_dict().get("progressSteps", {})

        default_order = [
            "Basic Information",
            "Education",
            "Work Experience",
            "Job Preference",
            "Skills",
            "Projects",
            "Awards"
        ]

        # Make sure all expected steps exist in the current progress
        for step in default_order:
            if step not in existing_progress:
                existing_progress[step] = {"done": False, "percentage": 0}

        # Update only the provided steps
        for step, update_data in progress_data.steps.items():
            if step in existing_progress:
                existing_progress[step].update(update_data.dict())

        candidate_ref.update({"progressSteps": existing_progress})

        return JSONResponse(
            content={
                "message": "Progress steps updated successfully",
                "progressSteps": existing_progress
            },
            status_code=200
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating progress steps: {str(e)}"
        ) from e


@candidate_router.get("/list-candidates", tags=["Candidate Management"])
async def list_candidates():
    candidates = db.collection("candidate").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in candidates]


@candidate_router.put("/update-basic-info", tags=["Candidate Management"])
async def update_basic_information(basic_info: BasicInformation = Body(...)):
    """
    Updates the 'basicInfo' field for a candidate in Firestore by email.
    """
    try:
        candidates_ref = db.collection("candidate").where("basicInfo.email", "==", basic_info.email).stream()

        candidate_doc = None
        candidate_id = None

        for doc in candidates_ref:
            candidate_doc = doc.to_dict()
            candidate_id = doc.id
            break

        if not candidate_doc:
            raise HTTPException(status_code=404, detail=f"Candidate with email {basic_info.email} not found")

        candidate_ref = db.collection("candidate").document(candidate_id)

        candidate_ref.update({
            "basicInfo": basic_info.dict()
        })

        return JSONResponse(
            content={"message": "Basic information updated successfully"},
            status_code=200
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating basic info: {str(e)}"
        )


@candidate_router.put("/education", tags=["Candidate Management"])
async def update_education(
        email: str = Query(..., example="user@example.com"),
        educationList: List[Education] = []
):
    """
    Replaces the education field for a candidate in Firestore by email (idempotent PUT).

    Args:
        email (str): The email of the candidate to update.
        educationList (List[Education]): The full list of education records to save.

    Returns:
        JSONResponse: A response indicating the success or failure of the update.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_education = [edu.dict() for edu in educationList]

        candidate_ref.update({"education": updated_education})

        return JSONResponse(
            content={"message": "Education data updated successfully", "education": updated_education},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating education data: {str(e)}"
        ) from e


@candidate_router.put("/job-preference", tags=["Candidate Management"])
async def update_job_preferences(
        email: str = Query(..., example="user@example.com"),
        jobPreferences: List[JobPreference] = []
):
    """
    Replaces the job preferences for a candidate by email (idempotent).

    Args:
        email (str): The email of the candidate to update.
        jobPreferences (List[JobPreference]): A list of job preference objects to save.

    Returns:
        JSONResponse: A success or failure message.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_preferences = [job.dict() for job in jobPreferences]

        candidate_ref.update({"jobPreference": updated_preferences})

        return JSONResponse(
            content={"message": "Job preferences updated successfully", "jobPreference": updated_preferences},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating job preferences: {str(e)}"
        ) from e


@candidate_router.put("/work-experience", tags=["Candidate Management"])
async def update_work_experience(
        email: str = Query(..., example="user@example.com"),
        workExperienceList: List[WorkExperience] = Body(...)
):
    """
    Replaces the work experience field for a candidate in Firestore by email (idempotent PUT).
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_work_experience = [work.dict() for work in workExperienceList]
        candidate_ref.update({"workExperience": updated_work_experience})

        return JSONResponse(
            content={
                "message": "Work experience data updated successfully",
                "workExperience": updated_work_experience
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating work experience data: {str(e)}"
        )


@candidate_router.put("/skills", tags=["Candidate Management"])
async def update_skills(
        email: str = Query(..., example="user@example.com"),
        skills: List[str] = Body(...)
):
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        candidate_ref.update({"skills": skills})

        return JSONResponse(
            content={"message": "Skills updated successfully", "skills": skills},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating skills: {str(e)}"
        )


@candidate_router.put("/projects", tags=["Candidate Management"])
async def update_projects(
        email: str = Query(..., example="user@example.com"),
        projects: List[Projects] = Body(...)
):
    """
    Replaces the projects field for a candidate in Firestore by email (idempotent PUT).

    Args:
        email (str): The email of the candidate to update.
        projects (List[Projects]): The full list of project records to save.

    Returns:
        JSONResponse: A response indicating the success or failure of the update.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_projects = [project.dict() for project in projects]

        candidate_ref.update({"projects": updated_projects})

        return JSONResponse(
            content={
                "message": "Projects updated successfully",
                "projects": updated_projects
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating projects: {str(e)}"
        ) from e


@candidate_router.put("/awards", tags=["Candidate Management"])
async def update_awards(
        email: str = Query(..., example="user@example.com"),
        awards: List[Awards] = Body(...)
):
    """
    Replaces the awards field for a candidate in Firestore by email (idempotent PUT).

    Args:
        email (str): The email of the candidate to update.
        awards (List[Awards]): A list of award records to save.

    Returns:
        JSONResponse: A response indicating success or failure.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_awards = [award.dict() for award in awards]
        candidate_ref.update({"awards": updated_awards})

        return JSONResponse(
            content={
                "message": "Awards updated successfully",
                "awards": updated_awards
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating awards: {str(e)}"
        ) from e


@candidate_router.put("/awards", tags=["Candidate Management"])
async def update_awards(
        email: str = Query(..., example="user@example.com"),
        awards: List[Awards] = Body(...)
):
    """
    Replaces the awards field for a candidate in Firestore by email (idempotent PUT).

    Args:
        email (str): The email of the candidate to update.
        awards (List[Awards]): A list of award records to save.

    Returns:
        JSONResponse: A response indicating success or failure.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        updated_awards = [award.dict() for award in awards]
        candidate_ref.update({"awards": updated_awards})

        return JSONResponse(
            content={
                "message": "Awards updated successfully",
                "awards": updated_awards
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating awards: {str(e)}"
        ) from e


@candidate_router.put("/account-settings", tags=["Candidate Management"])
async def update_account_settings(
        email: str = Query(...),
        account: Account = Body(...)
):
    """
    Updates account-related settings for the candidate.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()
        candidate_docs = [doc for doc in query]

        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        candidate_ref.update({
            "account": account.dict()
        })

        return JSONResponse(
            content={"message": "Account settings updated successfully."},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@candidate_router.put("/account-settings", tags=["Candidate Management"])
def match_candidates_to_job(job: JobModel, employer: EmployerProfile, candidate_list: list[dict]) -> list[MatchedJob]:
    matched_candidates = []

    for candidate in candidate_list:
        candidate_skills = candidate.get('skills', [])

        # Simple skill match check (can be replaced with more advanced logic)
        skill_match = any(skill in job.skills for skill in candidate_skills)

        if skill_match:
            matched_job = MatchedJob(
                candidate_email=candidate['email'],
                job_id=job.id,
                job_title=job.title,
                company_name=employer.companyName or "Unknown Company",
                description=job.description,
                tags=[
                    job.employment_type.value,
                    job.experience_level or "",
                    "Remote" if job.location == "remote" else "On-site"
                ],
                salary=f"R{job.salary_min} - R{job.salary_max}" if job.salary_min and job.salary_max else None,
                matched_on=datetime.utcnow(),
                status="pending",
                job_accepted="no"  # Default value
            )
            matched_candidates.append(matched_job)

    return matched_candidates


@candidate_router.post("/generate-resume-html-pdf")
def generate_resume(request: ResumeRequest):
    candidate = fetch_candidate_by_email(request.email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    template = env.get_template("resume_template.html")
    html_content = template.render(
        name=f"{candidate['basicInfo'].get('firstName', '')} {candidate['basicInfo'].get('lastName', '')}",
        email=candidate['basicInfo'].get('email', ''),
        role=candidate['basicInfo'].get('role', ''),
        description=candidate['basicInfo'].get('description', ''),
        education=candidate.get('education', []),
        skills=candidate.get('skills', []),
        projects=candidate.get('projects', []),
    )

    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"}
    )

