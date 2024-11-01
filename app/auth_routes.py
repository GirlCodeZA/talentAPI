"""
Routes for user authentication, including sign-up, login, and token validation.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.firebase import firebase, auth
from app.models import LoginSchema, SignUpSchema

router = APIRouter()

@router.post("/signup")
async def create_an_account(user_data: SignUpSchema):
    """
    Creates a new user account with the provided email and password.
    """
    try:
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )
        return JSONResponse(
            content={"message": f"User account created successfully for user {user.uid}"},
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login")
async def login(user_data: LoginSchema):
    """
    Authenticates a user and returns a token upon successful login.
    """
    try:
        user = firebase.auth().sign_in_with_email_and_password(
            user_data.email,
            user_data.password
        )
        return JSONResponse(content={"token": user['idToken']}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/ping")
async def validate_token(request: Request):
    """
    Validates a provided JWT token from the request headers.
    """
    jwt = request.headers.get("authorization")
    user = auth.verify_id_token(jwt)
    return user["user_id"]
