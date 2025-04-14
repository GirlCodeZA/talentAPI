from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MatchedJob(BaseModel):
    candidate_email: str  # For indexing / lookup
    job_id: str  # Reference to a job posting
    job_title: str
    company_name: str
    description: Optional[str] = None
    tags: List[str] = []  # Example: ["Fulltime", "Remote", "Junior"]
    salary: Optional[str] = None  # Example: "R10000/pm"
    matched_on: datetime = Field(default_factory=datetime.utcnow)
    status: Optional[str] = "pending"  # e.g. "viewed", "interviewed", etc.
    job_accepted: str