from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InterviewModel(BaseModel):
    candidate_email: str = Field(..., description="Candidate's email")
    job_id: str = Field(..., description="Associated job ID")
    company_name: str = Field(..., description="Company conducting the interview")

    interview_stage: str = Field(..., description="Stage name, e.g. 'HR Interview', 'Technical Interview'")
    scheduled_time: datetime = Field(..., description="Date and time for the interview")

    status: str = Field(default="scheduled", description="Interview status: scheduled, completed, cancelled")
    feedback: Optional[str] = Field(default=None, description="Optional feedback after the interview")

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
