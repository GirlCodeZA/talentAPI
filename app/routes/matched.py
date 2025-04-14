from fastapi import APIRouter, Body, HTTPException, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from app.firebase import db
from app.utils.models.matched import MatchedJob

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


@router.get("/matched-jobs", tags=["Matched Jobs"])
async def get_matched_jobs(candidate_email: str = Query(..., description="Email of the candidate")):
    """
    Get all matched jobs for a specific candidate.
    """
    try:
        matched_ref = db.collection("matched_jobs")
        query = matched_ref.where("candidate_email", "==", candidate_email).stream()

        matched_jobs = []
        for doc in query:
            job = doc.to_dict()
            job["id"] = doc.id
            matched_jobs.append(job)

        return JSONResponse(content=matched_jobs, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch matched jobs: {str(e)}"
        )


@router.post("/accept-job")
async def apply_to_job(candidate_email: str = Body(...), job_id: str = Body(...)):
    ref = db.collection("matched_jobs").document(job_id)
    ref.update({"status": "accepted"})
    return {"message": "Application successful"}