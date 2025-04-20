from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

from enum import Enum

class EmploymentType(str, Enum):
    permanent = "Permanent"
    contract = "Contract"
    freelance = "Freelance"


class JobModel(BaseModel):
    title: str
    description: Optional[str] = None
    # responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    skills: List[str] = []
    country: str
    city: Optional[str] = None
    location: Optional[str] = None
    employment_type: EmploymentType = Field(..., alias="employmentType")
    experience_level: Optional[str] = Field(None, alias='experienceLevel')
    salary_min: Optional[int] = Field(None, alias='salaryMin')
    salary_max: Optional[int] = Field(None, alias='salaryMax')
    application_close_date: Optional[date] = Field(None, alias='applicationCloseDate')

    class Config:
        allow_population_by_field_name = True
