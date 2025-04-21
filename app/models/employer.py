from pydantic import BaseModel, HttpUrl, EmailStr, Field
from typing import List, Optional
from enum import Enum

from app.models.shared import UserType

class CompanySize(str, Enum):
    SMALL = "1-10"
    MEDIUM = "11-50"
    LARGE = "51-200"
    XL = "200+"


class Industry(str, Enum):
    TECH = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    OTHER = "Other"


class EmployerProfile(BaseModel):
    uid: str
    email: EmailStr
    firstName: str
    lastName: str
    status: str = "pending"
    createdAt: Optional[str]

    companyName: Optional[str] = None
    contactNumber: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)

    companySize: Optional[CompanySize] = None
    industry: Optional[Industry] = None

    linkedin: Optional[HttpUrl] = None
    companyWebsite: Optional[HttpUrl] = None

    companyBenefits: Optional[List[str]] = []
    techStack: Optional[List[str]] = []

    userType: str = UserType.EMPLOYER
