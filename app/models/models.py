"""
Defines Pydantic models for user authentication requests.
"""

import re

from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationInfo, RootModel
from typing import Optional, Dict, List

from app.models.shared import UserType, ProfileStatus


class SignUpSchema(BaseModel):
    """
    Schema for user sign-up requests, containing email and password fields.
    """
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    firstName: str
    lastName: str
    userType: UserType = UserType.CANDIDATE
    # Employer only
    contactNumber: Optional[str] = None
    companyName: Optional[str] = None

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
    userType: UserType = UserType.CANDIDATE

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, password: str) -> str:
        """
        Ensures the password meets the required length.
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return password


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ProgressStep(BaseModel):
    done: bool
    percentage: int


class ProgressModel(BaseModel):
    steps: Dict[str, ProgressStep]

    @staticmethod
    def default_steps() -> Dict[str, ProgressStep]:
        return {
            "Basic Information": ProgressStep(done=False, percentage=0),
            "Education": ProgressStep(done=False, percentage=0),
            "Work Experience": ProgressStep(done=False, percentage=0),
            "Job Preference": ProgressStep(done=False, percentage=0),
            "Skills": ProgressStep(done=False, percentage=0),
            "Projects": ProgressStep(done=False, percentage=0),
            "Awards": ProgressStep(done=False, percentage=0)
        }


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
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    description: Optional[str] = None
    idNo: Optional[str] = None
    passport:  Optional[str] = None
    city: Optional[str] = None
    country: str
    role: Optional[str] = None
    category: Optional[str] = None
    urls: Optional[Urls] = None
    updatedAt: Optional[str] = None
    createdAt: Optional[str] = None


class Education(BaseModel):
    """
    Schema for education fields.
    """
    institution: str
    qualification : str
    startDate: str
    endDate: str
    description: str
    fileUrl: Optional[str] = None


class WorkExperience(BaseModel):
    """
    Schema for work experience fields.
    """
    organization: str
    jobTitle: str
    startDate: str
    endDate: Optional[str]
    description: str


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


class Skills(RootModel[List[str]]):
    """A list of skill strings."""
    pass


class Projects(BaseModel):
    """
    Schema for projects fields.
    """
    title: str
    description: str
    github: str


class Awards(BaseModel):
    """
    Schema for awards fields.
    """
    title: str
    description: str
    date: str


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
    progress: ProgressModel = Field(default_factory=lambda: ProgressModel(steps=ProgressModel.default_steps()))


class Account(BaseModel):
    """
    Schema for account-related settings.
    """
    activelyLooking: Optional[bool] = False
    hideFromCompanies: Optional[List[str]] = Field(default_factory=list)


class StatusUpdateSchema(BaseModel):
    email: str
    status: ProfileStatus


class ResumeRequest(BaseModel):
    email: str

