from fastapi import APIRouter, Body, HTTPException, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from app.firebase import db
from app.models.employer import EmployerProfile
from app.models.jobs import JobModel
from app.models.matched import MatchedJob, MatchedJobStatus
from collections import defaultdict, Counter
import uuid



router = APIRouter()

@router.post("/matched", tags=["Matched Jobs"])
async def save_matched_job(job_data: MatchedJob = Body(...)):
    try:
        matched_uuid = uuid.uuid4()  # Generate UUID
        job_dict = job_data.dict()
        job_dict["matched_id"] = str(matched_uuid)  # Ensure it's stored as a string
        job_dict["matched_on"] = datetime.utcnow().isoformat()  # Ensure timestamp

        # Save UUID as document ID too (optional, but makes querying easier)
        doc_ref = db.collection("matched_jobs").document(str(matched_uuid))
        doc_ref.set(job_dict)

        return JSONResponse(
            content={"message": "Matched job saved successfully", "matched_id": str(matched_uuid)},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save matched job: {str(e)}"
        )


@router.get("/matched-job-id", tags=["Matched Jobs"])
async def get_matched_id_by_job_id(job_id: str = Query(..., description="Job ID to look up")):
    """
    Get matched job info by job_id, including employer_id from the related job post.
    """
    try:
        # Step 1: Find matched job by job_id
        matched_ref = db.collection("matched_jobs")
        matched_query = matched_ref.where("job_id", "==", job_id).limit(1).stream()

        matched_job = None
        for doc in matched_query:
            matched_job = doc.to_dict()
            break

        if not matched_job:
            raise HTTPException(status_code=404, detail="No matched job found for the given job_id")

        # Step 2: Get job info from jobs collection
        job_doc = db.collection("jobs").document(job_id).get()
        if not job_doc.exists:
            raise HTTPException(status_code=404, detail="Job document not found")

        job_data = job_doc.to_dict()

        # Convert any datetime fields to ISO strings
        def serialize_datetime(value):
            return value.isoformat() if isinstance(value, datetime) else value

        matched_job["matched_on"] = serialize_datetime(matched_job.get("matched_on"))
        job_data["created_at"] = serialize_datetime(job_data.get("created_at"))
        job_data["applicationCloseDate"] = serialize_datetime(job_data.get("applicationCloseDate"))

        return JSONResponse(content={
            "candidate_id": matched_job.get("candidate_id"),
            "fit_score": matched_job.get("fit_score"),
            "job_accepted": matched_job.get("job_accepted"),
            "job_title": matched_job.get("job_title"),
            "skills_matched": matched_job.get("skills_matched", []),
            "employer_id": job_data.get("employer_id"),
            "matched_on": matched_job.get("matched_on"),
            "job_data": job_data
        }, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch matched job and employer info: {str(e)}"
        )

@router.post("/accept-job")
async def apply_to_job(candidate_email: str = Body(...), job_id: str = Body(...)):
    ref = db.collection("matched_jobs").document(job_id)
    ref.update({"status": "accepted"})
    return {"message": "Application successful"}


@router.get("/all-matched-jobs", tags=["Matched Jobs"])
async def get_all_matched_jobs():
    """
    Get all matched jobs (admin/debug/general view).
    """
    try:
        matched_ref = db.collection("matched_jobs")
        query = matched_ref.stream()

        matched_jobs = []
        for doc in query:
            job = doc.to_dict()
            job["id"] = doc.id
            matched_jobs.append(job)

        return JSONResponse(content=matched_jobs, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch all matched jobs: {str(e)}"
        )


@router.get("/job-matches-summary", tags=["Matched Jobs"])
async def job_matches_summary():
    """
    Returns summary of job titles with count of total matched candidates
    and their statuses.
    """
    try:
        matched_ref = db.collection("matched_jobs")
        matched_docs = matched_ref.stream()

        summary = defaultdict(lambda: {
            "total": 0,
            "statuses": {
                "pending": 0,
                "viewed": 0,
                "accepted": 0,
                "Declined": 0,
                "interviewed": 0,
                "offered": 0,
                "rejected": 0,
                "hired": 0
            }
        })

        for doc in matched_docs:
            data = doc.to_dict()
            job_title = data.get("job_title")
            status = data.get("status", "pending")

            if job_title:
                summary[job_title]["total"] += 1
                if status in summary[job_title]["statuses"]:
                    summary[job_title]["statuses"][status] += 1
                else:
                    # Catch unexpected status
                    summary[job_title]["statuses"][status] = 1

        return JSONResponse(content=summary)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating job matches summary: {str(e)}"
        )


@router.patch("/update-job-status", tags=["Matched Jobs"])
async def update_matched_job_status(
        matched_id: str = Query(..., description="Matched job document ID"),
        new_status: MatchedJobStatus = Query(..., description="New status for the matched job")
):
    try:
        ref = db.collection("matched_jobs").document(matched_id)
        doc = ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Matched job not found")

        ref.update({"job_accepted": new_status})

        return JSONResponse(
            content={"message": f"Matched job status updated to {new_status}"},
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update matched job status: {str(e)}"
        )
