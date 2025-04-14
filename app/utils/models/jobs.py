from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class JobModel(BaseModel):
    title: str
    description: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    skills: List[str] = []
    country: str
    city: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    application_close_date: Optional[date] = None
