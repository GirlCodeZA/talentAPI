from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, date
from app.firebase import db
from app.models.jobs import JobModel

router = APIRouter()

@router.post("/jobs", tags=["Jobs"])
async def create_job(job_data: JobModel = Body(...)):
    try:
        doc_ref = db.collection("jobs").document()
        job_dict = job_data.dict()

        # Add the generated ID to the job data
        job_dict["job_id"] = doc_ref.id

        # Convert date to datetime
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

@router.get("/jobs", tags=["Jobs"])
async def get_jobs():
    try:
        jobs_ref = db.collection("jobs")
        docs = jobs_ref.stream()

        jobs = []
        for doc in docs:
            job_data = doc.to_dict()

            # Convert any datetime fields to ISO strings
            for key, value in job_data.items():
                if isinstance(value, datetime):
                    job_data[key] = value.isoformat()

            job_data["job_id"] = doc.id  # Ensure job_id is included
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
