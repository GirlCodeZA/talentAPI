from fastapi import APIRouter, UploadFile, File, Body, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from firebase_admin import firestore
import uuid
import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError

from app.models.employer import EmployerProfile
from app.routes.utils import upload_file_to_s3, generate_signed_url
from app.settings import settings
from pydantic import BaseModel, EmailStr

import logging
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

class CompanyInfo(BaseModel):
    companyName: str
    email: EmailStr
    phone: str
    country: str
    city: Optional[str] = None
    description: Optional[str] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    linkedIn: Optional[str] = None
    website: Optional[str] = None
    benefits: Optional[List[str]] = []
    techStack: Optional[List[str]] = []

class JobPost(BaseModel):
    title: str
    description: str
    location: str
    jobType: str
    minSalary: Optional[int] = None
    maxSalary: Optional[int] = None
    skills: Optional[List[str]] = []

@employer_router.put("/update-company-info", tags=["Employer Management"])
async def update_company_info(data: CompanyInfo):
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


@employer_router.get("/get-company-info", tags=["Employer Management"])
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

        logo_key = data.get("logo")
        if logo_key:
            data["logoUrl"] = generate_signed_url(logo_key)

        return JSONResponse(content=data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving company info: {str(e)}")


@employer_router.post("/upload-logo", tags=["Employer Management"])
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

# @employer_router.post("/post-job", tags=["Employer Management"])
# async def post_job(email: str = Query(...), job: JobPost = Body(...)):
#     try:
#         ref = db.collection("employer")
#         query = ref.where("email", "==", email).stream()
#         docs = [doc for doc in query]
#
#         if not docs:
#             raise HTTPException(status_code=404, detail="Employer not found")
#
#         employer_id = docs[0].id
#         jobs_ref = db.collection("employer").document(employer_id).collection("jobs")
#         jobs_ref.add(job.dict())
#
#         return {"message": "Job posted successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to post job: {str(e)}")

# @employer_router.get("/jobs", tags=["Employer Management"])
# async def list_jobs(email: str = Query(...), jobType: Optional[str] = None, location: Optional[str] = None):
#     try:
#         ref = db.collection("employer")
#         query = ref.where("email", "==", email).stream()
#         docs = [doc for doc in query]
#
#         if not docs:
#             raise HTTPException(status_code=404, detail="Employer not found")
#
#         employer_id = docs[0].id
#         jobs_ref = db.collection("employer").document(employer_id).collection("jobs")
#         jobs_query = jobs_ref.stream()
#
#         jobs = []
#         for doc in jobs_query:
#             job = doc.to_dict()
#             if (not jobType or job["jobType"] == jobType) and (not location or job["location"] == location):
#                 jobs.append({"id": doc.id, **job})
#
#         return jobs
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


@employer_router.put("/update-employer-profile", tags=["Employer Management"])
async def update_employer_profile(
        email: str = Query(..., example="company@gmail.com"),
        profile_data: EmployerProfile = Body(...)
):
    try:
        employers_ref = db.collection("employer")
        query = employers_ref.where("email", "==", email).stream()

        employer_docs = [doc for doc in query]
        if not employer_docs:
            raise HTTPException(status_code=404, detail="Employer not found")

        employer_doc = employer_docs[0]
        employer_ref = employers_ref.document(employer_doc.id)

        employer_ref.update(profile_data.dict(exclude_unset=True))

        return JSONResponse(
            content={"message": "Employer profile updated successfully."},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating employer profile: {str(e)}")
