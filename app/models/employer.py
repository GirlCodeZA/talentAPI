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
    TECH = "Tech"
    FINANCE = "Finance"
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    RETAIL = "Retail"
    HOSPITALITY = "Hospitality"
    MANUFACTURING = "Manufacturing"
    CONSTRUCTION = "Construction"
    TRANSPORTATION = "Transportation"
    TELECOMMUNICATIONS = "Telecommunications"
    ENERGY = "Energy"
    MEDIA = "Media"
    ENTERTAINMENT = "Entertainment"
    REAL_ESTATE = "Real Estate"
    NON_PROFIT = "Non-Profit"
    GOVERNMENT = "Government"
    AGRICULTURE = "Agriculture"
    PHARMACEUTICALS = "Pharmaceuticals"
    AUTOMOTIVE = "Automotive"
    AEROSPACE = "Aerospace"
    BIOTECHNOLOGY = "Biotechnology"
    CHEMICALS = "Chemicals"
    CONSUMER_GOODS = "Consumer Goods"
    FOOD_AND_BEVERAGE = "Food and Beverage"
    TEXTILES = "Textiles"
    INSURANCE = "Insurance"
    LEGAL = "Legal"
    MARKETING = "Marketing"
    PUBLIC_RELATIONS = "Public Relations"
    CONSULTING = "Consulting"
    ADVERTISING = "Advertising"
    EVENT_MANAGEMENT = "Event Management"
    TRAVEL_AND_TOURISM = "Travel and Tourism"
    SPORTS = "Sports"
    FASHION = "Fashion"
    OTHER = "Other"


class EmployerProfile(BaseModel):
    uid: Optional[str] = None
    email: EmailStr
    firstName: str
    lastName: str
    status: str = "pending"
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

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
    profilePicture: Optional[str] = None
