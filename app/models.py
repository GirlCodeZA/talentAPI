"""
Defines Pydantic models for user authentication requests.
"""

from pydantic import BaseModel
from enum import Enum

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
    status: ProfileStatus


class LoginSchema(BaseModel):
    """
    Schema for user login requests, containing email and password fields.
    """
    email: str
    password: str



