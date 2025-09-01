from fastapi import APIRouter, UploadFile, File, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from firebase_admin import firestore
import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError

from app.models.employer import EmployerProfile
from app.utils.s3_helpers import upload_file_to_s3, generate_signed_url
from app.settings import settings
from pydantic import BaseModel, EmailStr
from app.models.shared import StatusUpdateSchema

import logging

from app.utils.status_helpers import update_profile_status_by_email

logger = logging.getLogger("uvicorn")

employer_router = APIRouter()
db = firestore.client()

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_key,
    config=Config(signature_version="s3v4", s3={'addressing_style': 'virtual'})
)


class JobPost(BaseModel):
    title: str
    description: str
    location: str
    jobType: str
    minSalary: Optional[int] = None
    maxSalary: Optional[int] = None
    skills: Optional[List[str]] = []


@employer_router.put("/update-company-info", tags=["Employer"])
async def update_company_info(data: EmployerProfile):
    try:
        ref = db.collection("employer")
        query = ref.where("email", "==", data.email).stream()

        employer_docs = [doc for doc in query]
        if not employer_docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        employer_ref = ref.document(employer_docs[0].id)
        employer_ref.update(data.dict())

        return {"message": "Company information updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update company info: {str(e)}")


@employer_router.get("/get-company-info", tags=["Employer"])
async def get_company_info(email: str = Query(...)):
    try:
        logger.info(f"Fetching employer with email: {email}")
        ref = db.collection("employer")
        query = ref.where("email", "==", email.lower()).stream()

        docs = list(query)
        logger.info(f"Found docs: {[doc.id for doc in docs]}")

        if not docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        data = docs[0].to_dict()

        profile_key = data.get("profilePicture")
        if profile_key:
            data["profilePictureSignedUrl"] = generate_signed_url(profile_key)

        return JSONResponse(content=data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving company info: {str(e)}")


@employer_router.post("/upload-logo", tags=["Employer"])
async def upload_logo(email: str = Query(...), file: UploadFile = File(...)):
    try:
        file_url = upload_file_to_s3(file, folder="company-logos")
        file_key = file_url.split(".com/")[-1]

        ref = db.collection("employer")
        query = ref.where("email", "==", email).stream()
        docs = [doc for doc in query]

        if not docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        ref.document(docs[0].id).update({"logo": file_key})

        return {"message": "Logo uploaded successfully", "logoUrl": generate_signed_url(file_key)}

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@employer_router.post("/post-job", tags=["Employer"])
async def post_job(email: str = Query(...), job: JobPost = Body(...)):
    try:
        ref = db.collection("employer")
        query = ref.where("email", "==", email).stream()
        docs = [doc for doc in query]

        if not docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        employer_id = docs[0].id
        jobs_ref = db.collection("employer").document(employer_id).collection("jobs")
        jobs_ref.add(job.dict())

        return {"message": "Job posted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post job: {str(e)}")


@employer_router.get("/jobs", tags=["Employer"])
async def list_jobs(
        email: str = Query(..., description="Employer's email"),
        employer_id: str  = Query(..., description="Employer's email"),
        jobType: Optional[str] = Query(None),
        location: Optional[str] = Query(None)
):
    try:
        ref = db.collection("employer")
        query = ref.where("email", "==", email.lower()).stream()
        docs = list(query)

        if not docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        # employer_id = docs[0].id
        jobs_ref = db.collection("employer").document(employer_id).collection("jobs")
        jobs_query = jobs_ref.stream()

        jobs = []
        for doc in jobs_query:
            job = doc.to_dict()
            if (not jobType or job.get("jobType") == jobType) and (not location or job.get("location") == location):
                jobs.append({"id": doc.id, **job})

        return JSONResponse(content=jobs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


@employer_router.get("/get-all-employers", tags=["Employer"])
async def get_all_employers():
    try:
        employers_ref = db.collection("employer")
        docs = employers_ref.stream()

        employers = []
        for doc in docs:
            data = doc.to_dict()
            logo_key = data.get("logo")
            if logo_key:
                data["logoUrl"] = generate_signed_url(logo_key)
            data["id"] = doc.id
            employers.append(data)

        return JSONResponse(content=employers)
    except Exception as e:
        logger.error(f"Error retrieving all employers: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch employers")


@employer_router.post("/update-picture", tags=["Employer"])
async def upload_image(
        email: str = Query(...),
        file: UploadFile = File(...)
):
    try:
        file_url = upload_file_to_s3(file, folder="profile-pictures")

        file_key = file_url.split(".com/")[-1]

        candidates_ref = db.collection("employer")
        query = candidates_ref.where("email", "==", email).stream()
        candidate_docs = [doc for doc in query]

        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        candidate_ref = candidates_ref.document(candidate_docs[0].id)
        candidate_ref.update({"profilePicture": file_key})

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


@employer_router.put("/update-status", tags=["Employer"])
async def update_employer_status(data: StatusUpdateSchema):
    message = await update_profile_status_by_email("employer", data.email, data.status)
    return {"message": message}


@employer_router.get("/get-employer-uid", tags=["Employer"])
async def get_employer_uid(email: str = Query(...)):
    try:
        ref = db.collection("employer")
        query = ref.where("email", "==", email.lower()).stream()

        docs = list(query)

        if not docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        uid = docs[0].to_dict().get("uid")
        company_name = docs[0].to_dict().get("companyName")
        if not uid:
            raise HTTPException(status_code=404, detail="UID not found for this employer")

        return JSONResponse(content={"uid": uid, "companyName" : company_name})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch UID: {str(e)}")


@employer_router.get("/get-employer-by-id", tags=["Employer"])
async def get_employer_by_id(
        employer_id: str = Query(..., description="Firestore document ID or employer UID")
):
    """
    Fetch employer details using an employer identifier.
    - First tries Firestore document id == employer_id
    - If not found, falls back to where uid == employer_id
    """
    try:
        ref = db.collection("employer")

        # 1) Try by Firestore document id
        doc_snap = ref.document(employer_id).get()
        if doc_snap.exists:
            data = doc_snap.to_dict()
            doc_id = doc_snap.id
        else:
            # 2) Fallback: try by 'uid' field
            query = ref.where("uid", "==", employer_id).limit(1).stream()
            docs = list(query)

            if not docs:
                raise HTTPException(status_code=404, detail="Employer not found")

            data = docs[0].to_dict()
            doc_id = docs[0].id

        # Attach signed URLs if present
        logo_key = data.get("logo")
        if logo_key:
            data["logoUrl"] = generate_signed_url(logo_key)

        profile_key = data.get("profilePicture")
        if profile_key:
            data["profilePictureSignedUrl"] = generate_signed_url(profile_key)

        # Always include the Firestore document id for convenience
        data["id"] = doc_id

        return JSONResponse(content=data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employer details: {str(e)}")
