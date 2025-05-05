from pydantic import BaseModel,EmailStr,Field
from enum import Enum
from typing import Optional
from datetime import datetime


class UserType(str, Enum):
    CANDIDATE = 'candidate',
    EMPLOYER = 'employer',
    ADMIN = 'admin'


class ADMIN(BaseModel):
    userType: Optional[str] = UserType.ADMIN
    isActive: bool = True
    firstName: str
    lastName: str
    email: EmailStr
    phone: Optional[str] = None
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
