# app/auth_routes.py

from fastapi import APIRouter, HTTPException, Request  # Import Request here
from fastapi.responses import JSONResponse
from app.firebase import firebase, auth
from app.models import LoginSchema, SignUpSchema

router = APIRouter()

@router.post("/signup")
async def create_an_account(user_data: SignUpSchema):
    try:
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )
        return JSONResponse(content={"message": f"User account created successfully for user {user.uid}"}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user_data: LoginSchema):
    try:
        user = firebase.auth().sign_in_with_email_and_password(
            user_data.email,
            user_data.password
        )
        return JSONResponse(content={"token": user['idToken']}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ping")
async def validate_token(request: Request):  # Now Request is defined
    jwt = request.headers.get("authorization")
    user = auth.verify_id_token(jwt)
    return user["user_id"]
