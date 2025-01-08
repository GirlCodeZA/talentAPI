"""
Defines Pydantic models for user authentication requests.
"""

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

class ProgressStep(BaseModel):
    done: bool
    percentage: int

# Define the main model for progress steps as a dictionary
class ProgressModel(BaseModel):
    steps: Dict[str, ProgressStep]



