from fastapi import APIRouter, Body, HTTPException, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from app.firebase import db
from app.models.employer import EmployerProfile
from app.models.jobs import JobModel
from app.models.matched import MatchedJob
from collections import defaultdict, Counter


router = APIRouter()

@router.post("/matched", tags=["Matched Jobs"])
async def save_matched_job(job_data: MatchedJob = Body(...)):
    try:
        doc_ref = db.collection("matched_jobs").document()
        job_dict = job_data.dict()
        job_dict["matched_on"] = datetime.utcnow().isoformat()  # ensure timestamp

        doc_ref.set(job_dict)

        return JSONResponse(
            content={"message": "Matched job saved successfully", "id": doc_ref.id},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save matched job: {str(e)}"
        )


# @router.get("/matched-jobs", tags=["Matched Jobs"])
# async def get_matched_jobs(candidate_email: str = Query(..., description="Email of the candidate")):
#     """
#     Get all matched jobs for a specific candidate.
#     """
#     try:
#         matched_ref = db.collection("matched_jobs")
#         query = matched_ref.where("candidate_email", "==", candidate_email).stream()
#
#         matched_jobs = []
#         for doc in query:
#             job = doc.to_dict()
#             job["id"] = doc.id
#             matched_jobs.append(job)
#
#         return JSONResponse(content=matched_jobs, status_code=200)
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to fetch matched jobs: {str(e)}"
#         )


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
