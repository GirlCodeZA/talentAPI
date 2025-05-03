from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MatchedJobStatus(str, Enum):
    PENDING = "pending"
    VIEWED = "viewed"
    INTERVIEWED = "interviewed"
    OFFERED = "offered"
    REJECTED = "rejected"

class MatchedJob(BaseModel):
    candidate_email: str  # For indexing / lookup
    job_id: str
    job_title: str
    company_name: str
    description: Optional[str] = None
    tags: List[str] = []  # Example: ["Fulltime", "Remote", "Junior"]
    salary: Optional[str] = None  # Example: "R10000/pm"
    matched_on: datetime = Field(default_factory=datetime.utcnow)
    status: Optional[str] = MatchedJobStatus.PENDING
    job_accepted: str