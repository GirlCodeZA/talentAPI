"""
Defines Pydantic models for user authentication requests.
"""

from pydantic import BaseModel

class SignUpSchema(BaseModel):
    """
    Schema for user sign-up requests, containing email and password fields.
    """
    password: str
    email: str


class LoginSchema(BaseModel):
    """
    Schema for user login requests, containing email and password fields.
    """
    email: str
    password: str
