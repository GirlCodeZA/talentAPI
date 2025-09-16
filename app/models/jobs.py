from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

from enum import Enum

class EmploymentType(str, Enum):
    permanent = "Permanent"
    contract = "Contract"
    freelance = "Freelance"

class Status(str, Enum):
    active = "Active"
    inactive = "Inactive"
    closed = "Closed"
    draft = "Draft"
    pending = "Pending"
    deleted = "Deleted"


class JobModel(BaseModel):
    employer_id: str
    title: str
    description: Optional[str] = None
    responsibilities: List[str] = []
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
    application_close_date: Optional[datetime] = Field(None, alias='applicationCloseDate')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = False
        orm_mode = True


class JobStatusUpdateSchema(BaseModel):
    job_id: str
    status: Status