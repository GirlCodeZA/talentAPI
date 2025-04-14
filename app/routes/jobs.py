from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, date
from app.firebase import db
from app.utils.models.jobs import JobModel

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
