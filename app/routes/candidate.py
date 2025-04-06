import uuid
from typing import List

from fastapi import APIRouter, HTTPException, Body, Query, File, UploadFile, Request
from fastapi.responses import JSONResponse
from firebase_admin import firestore

from app.firebase import db, bucket
from app.models import BasicInformation, Education, JobPreference, ProgressModel, ProgressStep, WorkExperience, Skills, \
    Projects

candidate_router = APIRouter()


db = firestore.client()
candidate_router = APIRouter()

@candidate_router.get("/candidate")
async def get_candidate_by_email(email: str = Query(...)):
    try:
        print(f"[INFO] Looking for candidate with email: {email}")

        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("basicInfo.email", "==", email).stream()

        candidate = None
        candidate_id = None

        for doc in query:
            candidate = doc.to_dict()
            candidate_id = doc.id
            break

        if not candidate:
            print(f"[WARN] No candidate found with email: {email}")
            raise HTTPException(status_code=404, detail="Candidate not found")

        default_steps = ProgressModel.default_steps()
        progress_steps_data = candidate.get("progressSteps", {})

        sorted_progress_steps = {
            step: ProgressStep(**progress_steps_data.get(step, default_steps[step])).dict()
            for step in default_steps
        }

        response = {
            "id": candidate_id,
            **candidate,
            "progressSteps": sorted_progress_steps
        }

        return JSONResponse(content=response, status_code=200)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[ERROR] Exception while fetching candidate: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching candidate: {str(e)}"
        )


@candidate_router.post("/update-picture")
async def update_picture(
        candidate_id: str = Query(..., example="candidate123"),
        file: UploadFile = File(...)
):
    """
    Uploads a profile picture to Firebase Storage and links it to the candidate in Firestore.
    """
    try:
        # Step 1: Generate a unique file name
        file_extension = file.filename.split(".")[-1]
        file_name = f"profile-pictures/{candidate_id}-{uuid.uuid4()}.{file_extension}"

        # Step 2: Upload the file to Firebase Storage
        blob = bucket.blob(file_name)
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make the file publicly accessible
        download_url = blob.public_url

        # Step 3: Update the candidate's Firestore record with the profile picture URL
        candidate_ref = db.collection("candidate").document(candidate_id)
        candidate_doc = candidate_ref.get()

        if not candidate_doc.exists:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_ref.update({"profile_picture": download_url})

        return JSONResponse(
            content={
                "message": "Profile picture updated successfully",
                "profile_picture_url": download_url
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading picture: {str(e)}") from e


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


from app.models import Awards  # Import the model if it's defined elsewhere

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
