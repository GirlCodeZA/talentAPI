"""
Defines Pydantic models for user authentication requests.
"""

import re

from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationInfo, StringConstraints, model_validator, root_validator, validator
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
    confirm_password: str
    name: str
    lastName: str
    status: Optional[ProfileStatus] = ProfileStatus.PENDING

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_password, values):
        """
        Ensures password and confirm_password fields match.
        """
        password = values.data.get("password")
        if password and confirm_password != password:
            raise ValueError("Passwords do not match")
        return confirm_password
    
    @field_validator("name" , "lastName")
    @classmethod
    def validate_name(cls, value: str, info):
        #Ensures that the name and last name fields are not empty and only contain alphabetical characters
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
    phone: Annotated[str, StringConstraints(pattern=r"^\+[1-9]\d{1,14}$")]
    country: str
    city: str
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=500)]
    id: Annotated[str, StringConstraints(pattern=r"^\d{13}$")]
    passport: str
    currentRole: str
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
    progress: ProgressModel = ProgressModel()
