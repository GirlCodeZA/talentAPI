"""
Defines Pydantic models for user authentication requests.
"""

import re

from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationInfo, StringConstraints
from enum import Enum
from typing import Optional, Dict, Annotated



class ProfileStatus(str, Enum):
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
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    firstName: str
    lastName: str
    status: Optional[ProfileStatus] = ProfileStatus.PENDING

    @field_validator("firstName", "lastName")
    @classmethod
    def validate_name(cls, value: str, info):
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        if not re.match(r"^[A-Za-z]+$", value):
            raise ValueError(f"{info.field_name} must contain only alphabetic characters")
        return value
            


class LoginSchema(BaseModel):
    """
    Schema for validating user login data.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, password: str) -> str:
        """
        Ensures the password meets the required length.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return password


class ProgressStep(BaseModel):
    done: bool
    percentage: int


class ProgressModel(BaseModel):
    steps: Dict[str, ProgressStep] = {}


class Urls(BaseModel):
    """
    Schema for URLs fields.
    """
    #To Do: Add validations for GitHub & LinkedIn
    linkedIn: str 
    github: str


class BasicInformation(BaseModel):
    """
    Schema for basic information fields.
    """
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    description: str
    idNo: str
    passport:  Optional[str] = None
    city: Optional[str] = None
    country: str
    city: str
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)]
    id:Optional[Annotated[str, StringConstraints(pattern=r"^\d{13}$")]] = None  #Made optional 
    passport: Optional [str] = None
    currentRole: Optional[str] = None
    category: Optional[str] = None
    category: str
    urls: Urls

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Validates phone numbers following the E.164 format."""
        if not re.match(r"^\+[1-9]\d{1,14}$", value):
            raise ValueError("Invalid phone number format. Must be in E.164 format(e.g, +267673811767.")
        return value
    
    @field_validator ("passport")
    @classmethod
    def validate_passport(cls, value: str) -> str:
        """ Validates passport numbers (common length: 6-9 Alphanumeric characters)."""
        if not re.match(r"^[A-Za-z0-9]{6,9}$", value):
            raise ValueError("Invalid passport number. It must be 6-9 alphanumeric characters.")
        return value



class Education(BaseModel):
    """
    Schema for education fields.
    """
    institution: str
    degree: str
    course: str
    startDate: str
    endDate: str
    description: str
    fileUrl: Optional[str] = None


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
    type: str
    minSalary: int
    maxSalary: int
    workLocation: str
    relocate: str
    desiredRole: str
    experience: str
    idealJob: str


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
    progress: ProgressModel = ProgressModel()
