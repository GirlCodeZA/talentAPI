from fastapi import APIRouter, Body, Query, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional, Annotated, List, Dict, Any
from collections import defaultdict
from pydantic import BaseModel

import uuid
import math
import re

from app.firebase import db
from app.models.matched import MatchedJob, MatchedJobStatus
from google.api_core.datetime_helpers import DatetimeWithNanoseconds

router = APIRouter()

# ---------------------------
# Utilities
# ---------------------------

def make_json_safe(obj):
    if isinstance(obj, (DatetimeWithNanoseconds, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]
    return obj

def _safe_dict(v) -> dict:
    return v if isinstance(v, dict) else {}

def _safe_list(v) -> list:
    return v if isinstance(v, list) else []

# ---------------------------
# Existing endpoints (kept)
# ---------------------------

@router.post("/matched", tags=["Matched Jobs"])
async def save_matched_job(job_data: MatchedJob = Body(...)):
    try:
        matched_uuid = uuid.uuid4()
        job_dict = job_data.dict()
        job_dict["matched_id"] = str(matched_uuid)
        job_dict["matched_on"] = datetime.utcnow().isoformat()

        db.collection("matched_jobs").document(str(matched_uuid)).set(job_dict)

        return JSONResponse(
            content={"message": "Matched job saved successfully", "matched_id": str(matched_uuid)},
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save matched job: {str(e)}")


@router.get("/matched-job-id", tags=["Matched Jobs"])
async def get_matched_id_by_job_id(job_id: str = Query(..., description="Job ID to look up")):
    try:
        matched_ref = db.collection("matched_jobs")
        matched_query = matched_ref.where("job_id", "==", job_id).limit(1).stream()

        matched_job = None
        for doc in matched_query:
            matched_job = doc.to_dict()
            break

        if not matched_job:
            raise HTTPException(status_code=404, detail="No matched job found for the given job_id")

        job_doc = db.collection("jobs").document(job_id).get()
        if not job_doc.exists:
            raise HTTPException(status_code=404, detail="Job document not found")

        job_data = job_doc.to_dict()

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
        raise HTTPException(status_code=500, detail=f"Failed to fetch matched job and employer info: {str(e)}")


@router.post("/accept-job", tags=["Matched Jobs"])
async def accept_job(matched_id: str = Body(..., embed=True)):
    """
    Accept a matched job by matched_id (document id in matched_jobs).
    Updates the canonical status field: job_accepted -> 'accepted'.
    """
    try:
        ref = db.collection("matched_jobs").document(matched_id)
        if not ref.get().exists:
            raise HTTPException(status_code=404, detail="Matched job not found")

        val = MatchedJobStatus.accepted.value if hasattr(MatchedJobStatus, "accepted") else "accepted"
        ref.update({"job_accepted": val})
        return {"message": "Application successful"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to accept job: {str(e)}")


@router.get("/all-matched-jobs", tags=["Matched Jobs"])
async def get_all_matched_jobs():
    try:
        query = db.collection("matched_jobs").stream()
        matched_jobs = []
        for doc in query:
            job = doc.to_dict()
            job["id"] = doc.id
            matched_jobs.append(make_json_safe(job))
        return JSONResponse(content=matched_jobs, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all matched jobs: {str(e)}")


@router.get("/job-matches-summary", tags=["Matched Jobs"])
async def job_matches_summary():
    try:
        matched_docs = db.collection("matched_jobs").stream()

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
            status_val = data.get("job_accepted", "pending")

            if job_title:
                summary[job_title]["total"] += 1
                summary[job_title]["statuses"][status_val] = summary[job_title]["statuses"].get(status_val, 0) + 1

        return JSONResponse(content=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating job matches summary: {str(e)}")


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
    try:
        ref = db.collection("matched_jobs").where("candidate_id", "==", candidate_id)
        if status_filter is not None:
            ref = ref.where("job_accepted", "==", status_filter.value)

        docs = ref.stream()
        results = []

        for doc in docs:
            matched = doc.to_dict() or {}
            matched["matched_doc_id"] = doc.id

            if include_job and matched.get("job_id"):
                job_doc = db.collection("jobs").document(matched["job_id"]).get()
                if job_doc.exists:
                    job = job_doc.to_dict() or {}
                    matched["job_data"] = job
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch matches for candidate_id: {str(e)}")

# ---------------------------
# AI-ish Matching
# ---------------------------

# Request body schema
class MatchPayload(BaseModel):
    job_title: str
    qualifications: Optional[str] = ""
    skills: List[str] = []
    experience_level: str  # e.g., "0-1 years"
    job_id: Optional[str] = None
    employer_id: Optional[str] = None


class JobSpecModel:
    def __init__(self, job_title: str, qualifications: str, skills: List[str], experience_level: str):
        self.job_title = job_title
        self.qualifications = qualifications or ""
        self.skills = skills or []
        self.experience_level = experience_level

class CandidateModel:
    def __init__(self, candidate_id: str, job_titles: List[str], skills: List[str], experience_years: float, qualifications: str, status: str):
        self.candidate_id = candidate_id
        self.job_titles = job_titles or []
        self.skills = skills or []
        self.experience_years = experience_years or 0.0
        self.qualifications = qualifications or ""
        self.status = status or "inactive"

# --- Scoring helpers ---
_word = re.compile(r"[A-Za-z0-9+.#]+")

def _tokenize(s: str) -> List[str]:
    return [w.lower() for w in _word.findall(s or "")]

def _jaccard(a: List[str], b: List[str]) -> float:
    A, B = set([x.lower() for x in a]), set([x.lower() for x in b])
    if not A and not B:
        return 0.0
    return len(A & B) / len(A | B)

def _title_similarity(job_title: str, cand_titles: List[str]) -> float:
    jt = set(_tokenize(job_title))
    if not cand_titles:
        return 0.0
    return max(_jaccard(list(jt), _tokenize(t)) for t in cand_titles)

def _map_exp_bucket(s: str) -> float:
    s = (s or "").strip().lower()
    if "0-1" in s: return 0.5
    if "1-3" in s: return 2.0
    if "3-5" in s: return 4.0
    if "5"   in s: return 7.0
    return 0.0

def _experience_alignment(job_req_years: float, cand_years: float) -> float:
    if job_req_years == 0:
        return 0.6 if cand_years < 1 else 0.8
    diff = abs(cand_years - job_req_years)
    return max(0.0, 1.0 - (diff / max(1.0, job_req_years)))

def _logistic(x: float) -> float:
    return 1 / (1 + math.exp(-5*(x-0.5)))

def _score_candidate(job: JobSpecModel, cand: CandidateModel) -> Dict[str, Any]:
    W_TITLE = 0.35
    W_SKILLS = 0.40
    W_EXP = 0.20
    W_QUAL = 0.05

    sim_title = _title_similarity(job.job_title, cand.job_titles)
    sim_skills = _jaccard(job.skills, cand.skills)
    req_years = _map_exp_bucket(job.experience_level)
    exp_score = _experience_alignment(req_years, cand.experience_years)

    qual_hits = 0.0
    if job.qualifications:
        jq = _tokenize(job.qualifications)
        cq = _tokenize(cand.qualifications)
        qual_hits = _jaccard(jq, cq)

    raw = (W_TITLE*sim_title + W_SKILLS*sim_skills + W_EXP*exp_score + W_QUAL*qual_hits)
    fit = _logistic(raw)

    matched = sorted(set([s for s in cand.skills if s.lower() in {x.lower() for x in job.skills}]))

    reason_bits = []
    if matched: reason_bits.append(f"Matched skills: {', '.join(matched)}")
    if sim_title >= 0.5: reason_bits.append("Relevant title history")
    if exp_score < 0.5: reason_bits.append("Experience misaligned")

    return {
        "candidate_id": cand.candidate_id,
        "fit_score": f"{round(fit*100):d}%",
        "skills_matched": matched,
        "reason": "; ".join(reason_bits) or "General profile alignment."
    }

def _infer_years_from_label(label: str) -> float:
    return _map_exp_bucket(label)

def _fetch_candidates_from_firestore() -> List[CandidateModel]:
    """
    Maps your Firestore shape.
    """
    out: List[CandidateModel] = []
    docs = db.collection("candidate").stream()
    for d in docs:
        x = d.to_dict() or {}
        uid = x.get("uid", d.id)
        status = x.get("status", "inactive")
        skills = _safe_list(x.get("skills"))
        basic_info = _safe_dict(x.get("basicInfo"))
        job_pref   = _safe_dict(x.get("jobPreference"))
        awards     = _safe_list(x.get("awards"))

        desired_role = basic_info.get("desiredRole") or job_pref.get("desiredRole") or ""
        titles = [desired_role] if desired_role else []
        exp_label = job_pref.get("experience") or "0-1 years"
        exp_years = _infer_years_from_label(exp_label)
        quals = " ".join([a.get("title","") for a in awards if isinstance(a, dict)])

        out.append(CandidateModel(
            candidate_id=uid,
            job_titles=titles,
            skills=skills,
            experience_years=exp_years,
            qualifications=quals,
            status=status
        ))
    return out

# Toggle: also persist top matches into matched_jobs
SAVE_MATCHED = True
TOP_SAVE = 5

@router.post("/match", tags=["AI Matcher"])
async def match_candidates(payload: MatchPayload):
    """
    Scores all active candidates against the provided job spec and returns:
      { status, response, evaluation_table[] }

    If SAVE_MATCHED is True and payload.job_id is provided, persists the top N as matched_jobs.
    """
    try:
        job = JobSpecModel(
            job_title=payload.job_title,
            qualifications=payload.qualifications or "",
            skills=payload.skills or [],
            experience_level=payload.experience_level
        )

        # pull candidates
        all_cands = _fetch_candidates_from_firestore()
        active = [c for c in all_cands if (c.status or "").lower() == "active"]
        if not active:
            return {"status": "SUCCEEDED", "response": "No active candidates found.", "evaluation_table": []}

        rows = [_score_candidate(job, c) for c in active]
        rows.sort(key=lambda r: int(r["fit_score"].rstrip("%")), reverse=True)

        top = rows[:3]
        bullets = []
        for r in top:
            suffix = r["candidate_id"][-5:] if len(r["candidate_id"]) >= 5 else r["candidate_id"]
            bullets.append(f"- {suffix}: {r['fit_score']} ({', '.join(r['skills_matched']) or 'no skill match'})")
        summary = "I've found potential candidates. Top matches:\n" + "\n".join(bullets)

        print('Save matched', SAVE_MATCHED , payload)

        # Optional persistence
        if SAVE_MATCHED and payload.job_id:
            now_iso = datetime.utcnow().isoformat()
            for r in rows[:TOP_SAVE]:
                matched_id = str(uuid.uuid4())
                doc = {
                    "matched_id": matched_id,
                    "matched_on": now_iso,
                    "job_id": payload.job_id,
                    "employer_id": payload.employer_id,
                    "job_title": payload.job_title,
                    "skills_required": payload.skills,
                    "candidate_id": r["candidate_id"],
                    "fit_score": r["fit_score"],
                    "skills_matched": r["skills_matched"],
                    "job_accepted": "pending"
                }
                db.collection("matched_jobs").document(matched_id).set(doc)

        return {
            "status": "SUCCEEDED",
            "response": summary,
            "evaluation_table": rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match candidates: {str(e)}")
