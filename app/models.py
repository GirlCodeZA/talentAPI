"""
Defines Pydantic models for user authentication requests.
"""

import re
from fastapi import HTTPException, status
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict


class ProfileStatus(Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"
    PENDING = "pending"
    SUSPENDED = "suspended"
    INCOMPLETE = "incomplete"
    VERIFIED = "verified"
    ARCHIVED = "archived"

class SignUpSchema(BaseModel):
    """
    Schema for user sign-up requests, containing email and password fields.
    """
    password: str
    email: str
    name: str
    lastName: str
    status: Optional[str] = "PENDING"


class LoginSchema(BaseModel):
    """
    Schema for user login requests, containing email and password fields.
    """
    email: str
    password: str

    @staticmethod
    def validate_user_data(user_data: BaseModel):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        if not re.match(pattern, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        if len(user_data.password) < 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        return user_data

class ProgressStep(BaseModel):
    done: bool
    percentage: int


class ProgressModel(BaseModel):
    steps: Dict[str, ProgressStep]

class Urls(BaseModel):
    """
    Schema for URLs fields.
    """
    linkedIn: str
    github: str


class BasicInformation(BaseModel):
    """
    Schema for basic information fields.
    """
    firstName: str # get the first name of the candidate
    lastName: str # get the last name of the candidate
    email: str # get the email of the candidate
    phone: str
    id: str
    passport: str
    city: str
    country: str
    role: str
    Urls: Urls

class Education(BaseModel):
    """
    Schema for education fields.
    """
    degree: str
    institution: str
    startYear: int
    endYear: int
    city: str
    country: str

class WorkExperience(BaseModel):
    """
    Schema for work experience fields.
    """
    company: str
    position: str
    startYear: int
    endYear: int
    city: str
    country: str

class JobPreference(BaseModel):
    """
    Schema for job preference fields.
    """
    role: str
    location: str
    type: str
    salary: int

class Skills(BaseModel):
    """
    Schema for skills fields.
    """
    skill: str
    proficiency: str

class Projects(BaseModel):
    """
    Schema for projects fields.
    """
    project: str
    description: str
    startYear: int
    endYear: int

class Awards(BaseModel):
    """
    Schema for awards fields.
    """
    award: str
    description: str
    year: int

class Profile(BaseModel):
    """
    Schema for profile fields.
    """
    basicInformation: BasicInformation
    education: Education
    workExperience: WorkExperience
    jobPreference: JobPreference
    skills: Skills
    projects: Projects
    awards: Awards
    status: ProfileStatus
    progress: ProgressModel




