import uuid
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MatchedJobStatus(str, Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "Declined"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    # REJECTED = "rejected"
    HIRED = "hired"
    REJECTED_BY_EMPLOYER = "rejected_by_employer"
    REJECTED_BY_CANDIDATE = "rejected_by_candidate"


class MatchedJob(BaseModel):
    matched_id: Optional[uuid.UUID] = Field(None, description="Matched job document ID")
    candidate_id: str
    job_id: str
    job_title: str
    matched_on: datetime = Field(default_factory=datetime.utcnow)
    job_accepted: Optional[MatchedJobStatus] = None
    fit_score: Optional[float] = None
    skills_matched: List[str] = []