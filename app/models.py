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

    class Config:
        # pylint: disable=too-few-public-methods
        """
        Configuration for the example schema shown in documentation.
        """
        schema_extra = {
            "example": {
                "password": "password",
                "email": "test@gmail.com"
            }
        }

class LoginSchema(BaseModel):
    """
    Schema for user login requests, containing email and password fields.
    """
    email: str
    password: str

    class Config:
        # pylint: disable=too-few-public-methods
        """
        Configuration for the example schema shown in documentation.
        """
        schema_extra = {
            "example": {
                "password": "password",
                "email": "test@gmail.com"
            }
        }
