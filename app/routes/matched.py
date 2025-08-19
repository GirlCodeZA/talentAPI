from fastapi import APIRouter, Body, Query, HTTPException, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime
from app.firebase import db
from app.models.matched import MatchedJob, MatchedJobStatus
from collections import defaultdict, Counter
import uuid
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

from typing import Optional, Annotated


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
    try:
        # 1) Fetch matched_job
        matched_ref = db.collection("matched_jobs")
        matched_query = matched_ref.where("job_id", "==", job_id).limit(1).stream()

        matched_job = None
        for doc in matched_query:
            matched_job = doc.to_dict()
            break

        if not matched_job:
            raise HTTPException(status_code=404, detail="No matched job found for the given job_id")

        # 2) Fetch job_data
        job_doc = db.collection("jobs").document(job_id).get()
        if not job_doc.exists:
            raise HTTPException(status_code=404, detail="Job document not found")

        job_data = job_doc.to_dict()

        # 3) Recursively make everything JSON-safe
        def make_json_safe(obj):
            if isinstance(obj, (DatetimeWithNanoseconds, datetime)):
                return obj.isoformat()
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple, set)):
                return [make_json_safe(v) for v in obj]
            return obj

        safe_matched_job = make_json_safe(matched_job)
        safe_job_data   = make_json_safe(job_data)

        return JSONResponse(
            content={
                "candidate_id": safe_matched_job.get("candidate_id"),
                "fit_score": safe_matched_job.get("fit_score"),
                "job_accepted": safe_matched_job.get("job_accepted"),
                "job_title": safe_matched_job.get("job_title"),
                "skills_matched": safe_matched_job.get("skills_matched", []),
                "employer_id": safe_job_data.get("employer_id"),
                "matched_on": safe_matched_job.get("matched_on"),
                "job_data": safe_job_data,
            },
            status_code=200,
        )

    except HTTPException:
        raise
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
        job_id: str = Query(..., description="Job ID (field inside matched_jobs)"),
        new_status: MatchedJobStatus = Query(..., description="New status for the matched job"),
):
    try:
        snaps = db.collection("matched_jobs").where("job_id", "==", job_id).limit(1).get()
        if not snaps:
            raise HTTPException(status_code=404, detail="Matched job not found for this job_id")

        doc_ref = snaps[0].reference
        value = new_status.value if hasattr(new_status, "value") else str(new_status)
        doc_ref.update({"job_accepted": value})

        return {"message": f"Matched job status updated to {value}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update matched job status: {str(e)}")


@router.get("/matched/by-candidate", tags=["Matched Jobs"])
async def get_matched_jobs_by_candidate(
        candidate_id: Annotated[str, Query(description="Candidate ID to look up")],
        status_filter: Annotated[
            Optional[MatchedJobStatus],
            Query(description="Filter by matched job status (maps to job_accepted)")
        ] = None,
        include_job: Annotated[
            bool,
            Query(description="If true, include the job document as job_data")
        ] = True,
):
    """
    Returns all matched_jobs for a candidate_id.
    - Optional: filter by status (compares against the job_accepted field)
    - Optional: include the full job document as `job_data`
    """

    def make_json_safe(obj):
        if isinstance(obj, (DatetimeWithNanoseconds, datetime)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [make_json_safe(v) for v in obj]
        return obj

    try:
        ref = db.collection("matched_jobs").where("candidate_id", "==", candidate_id)

        if status_filter is not None:
            # Already validated enum -> use its value
            ref = ref.where("job_accepted", "==", status_filter.value)

        # If you have an index, you can order:
        # ref = ref.order_by("matched_on", direction=firestore.Query.DESCENDING)

        docs = ref.stream()
        results = []

        for doc in docs:
            matched = doc.to_dict() or {}
            matched["matched_doc_id"] = doc.id

            # Attach canonical job data and override denormalized fields
            if include_job and matched.get("job_id"):
                job_doc = db.collection("jobs").document(matched["job_id"]).get()
                if job_doc.exists:
                    job = job_doc.to_dict() or {}
                    matched["job_data"] = job

                    # Prefer canonical fields from job doc
                    if job.get("title"):
                        matched["job_title"] = job["title"]
                    if job.get("location"):
                        matched["location"] = job["location"]
                    if job.get("description") and not matched.get("job_overview"):
                        matched["job_overview"] = job["description"]

            results.append(make_json_safe(matched))

        if not results:
            raise HTTPException(status_code=404, detail="No matches found for that candidate_id")

        return JSONResponse(content=results, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch matches for candidate_id: {str(e)}"
        )
