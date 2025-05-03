
from fastapi import APIRouter, Body, HTTPException, status, Request
from fastapi.responses import JSONResponse
from datetime import datetime, date
from app.firebase import db
from app.models.jobs import JobModel
from typing import Optional


router = APIRouter()

@router.post("/jobs", tags=["Jobs"])
async def create_job(
        job_data: JobModel = Body(...),
        request: Request = None  # Assuming request holds user session or token
):
    try:
        # Example of getting the employer UID from headers (customize for your auth)
        employer_uid = request.headers.get("X-User-Uid")  # Or from token/session
        if not employer_uid:
            raise HTTPException(status_code=401, detail="Employer UID missing")

        doc_ref = db.collection("jobs").document()
        job_dict = job_data.dict()

        # Override employer_id from auth instead of trusting client data
        job_dict["employer_id"] = employer_uid
        job_dict["job_id"] = doc_ref.id

        if isinstance(job_dict.get("application_close_date"), date):
            job_dict["application_close_date"] = datetime.combine(
                job_dict["application_close_date"], datetime.min.time()
            )

        job_dict["created_at"] = datetime.utcnow().isoformat()

        doc_ref.set(job_dict)

        return JSONResponse(
            content={"message": "Job created successfully", "id": doc_ref.id},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {str(e)}"
        )


@router.put("/jobs/{job_id}", tags=["Jobs"])
async def update_job(
        job_id: str,
        job_data: JobModel = Body(...),
        request: Request = None
):
    try:
        employer_uid = request.headers.get("X-User-Uid")
        if not employer_uid:
            raise HTTPException(status_code=401, detail="Employer UID missing")

        doc_ref = db.collection("jobs").document(job_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")

        existing_data = doc.to_dict()
        if existing_data.get("employer_id") != employer_uid:
            raise HTTPException(status_code=403, detail="Unauthorized to update this job")

        job_dict = job_data.dict(exclude_unset=True)  # Only include provided fields

        if "application_close_date" in job_dict and isinstance(job_dict["application_close_date"], date):
            job_dict["application_close_date"] = datetime.combine(
                job_dict["application_close_date"], datetime.min.time()
            )

        job_dict["updated_at"] = datetime.utcnow().isoformat()

        doc_ref.update(job_dict)

        return JSONResponse(
            content={"message": "Job updated successfully"},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update job: {str(e)}"
        )


@router.get("/jobs", tags=["Jobs"])
async def get_jobs(limit: int = 50, start_after: Optional[str] = None):
    try:
        jobs_ref = db.collection("jobs").order_by("created_at", direction="DESCENDING").limit(limit)

        if start_after:
            start_doc = db.collection("jobs").document(start_after).get()
            if start_doc.exists:
                jobs_ref = jobs_ref.start_after(start_doc)

        docs = jobs_ref.stream()

        jobs = []
        for doc in docs:
            job_data = doc.to_dict()
            for key, value in job_data.items():
                if isinstance(value, datetime):
                    job_data[key] = value.isoformat()

            job_data["job_id"] = doc.id
            jobs.append(job_data)

        return JSONResponse(
            content={"jobs": jobs},
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve jobs: {str(e)}"
        )



@router.get("/jobs/{job_id}", tags=["Jobs"])
async def get_job_by_id(job_id: str):
    try:
        doc_ref = db.collection("jobs").document(job_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID '{job_id}' not found"
            )

        job_data = doc.to_dict()

        # Convert any datetime fields to ISO format
        for key, value in job_data.items():
            if isinstance(value, datetime):
                job_data[key] = value.isoformat()

        job_data["job_id"] = doc.id  # Ensure job_id is included

        return JSONResponse(
            content=job_data,
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job: {str(e)}"
        )


@router.get("/employer/jobs", tags=["Jobs"])
async def get_jobs_by_employer(employer_id: str):
    try:
        jobs_ref = db.collection("jobs").where("employer_id", "==", employer_id)
        docs = jobs_ref.stream()

        jobs = []
        for doc in docs:
            job_data = doc.to_dict()
            for key, value in job_data.items():
                if isinstance(value, datetime):
                    job_data[key] = value.isoformat()

            job_data["job_id"] = doc.id
            jobs.append(job_data)

        return JSONResponse(
            content={"jobs": jobs},
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve jobs for employer: {str(e)}"
        )
