from fastapi import HTTPException
from starlette import status
from pydantic import BaseModel
import re


class SignUpSchema(BaseModel):
    email:str
    password:str
    confirm_password:str


class LoginSchema(BaseModel):
    email: str
    password: str


def validate_user_data(user_data: BaseModel):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    if not re.match(pattern, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    return user_data


def confirm_password_validation(user_data: SignUpSchema):
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password mismatch")
    return user_data