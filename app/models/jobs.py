from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from enum import Enum

class EmploymentType(str, Enum):
    permanent = "Permanent"
    contract = "Contract"
    freelance = "Freelance"

class Status(str, Enum):
    active = "Live"
    inactive = "Inactive"
    closed = "Closed"
    draft = "Draft"


class JobModel(BaseModel):
    employer_id: str
    title: str
    description: Optional[str] = None
    responsibilities: List[str]
    qualifications: Optional[str] = None
    skills: List[str] = []
    country: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    status: Optional[Status] = Field(None, alias='status')
    employment_type: EmploymentType = Field(None, alias="employmentType")
    experience_level: Optional[str] = Field(None, alias='experienceLevel')
    salary_min: Optional[int] = Field(None, alias='salaryMin')
    salary_max: Optional[int] = Field(None, alias='salaryMax')
    application_close_date: Optional[date] = Field(None, alias='applicationCloseDate')

    class Config:
        allow_population_by_field_name = True
