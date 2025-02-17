from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Body, status
from fastapi.responses import JSONResponse
from firebase_admin import auth

from app.firebase import db
from app.firebase import firebase
from app.models import LoginSchema, SignUpSchema

router = APIRouter()
@router.post("/signup")
async def create_an_account(
        user_data: SignUpSchema = Body(
            ...,
            example={
                "email": "user@example.com",
                "password": "your_password",
                "confirm_password": "your_password",
                "name": "John",
                "lastName": "Doe"
            }
        )
):
    """
    Creates a new user account with the provided email and password,
    and stores user data in Firestore with default progress steps.
    """
    try:
        # Step 1: Create a new user in Firebase Authentication
        user = auth.create_user(email=user_data.email, password= user_data.password)
        return JSONResponse(content={
            "message": f"Account created successfully. User ID: {user.uid}"},
            status_code=status.HTTP_201_CREATED)
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account already exists for email {user_data.email}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


        # Step 2: Get current timestamp in ISO 8601 format
        created_at = datetime.utcnow().isoformat()

        # Step 3: Default progress steps
        progress_steps_default = {
            "Basic Information": {"done": False, "percentage": 0},
            "Education": {"done": False, "percentage": 0},
            "Work Experience": {"done": False, "percentage": 0},
            "Job Preference": {"done": False, "percentage": 0},
            "Skills": {"done": False, "percentage": 0},
            "Projects": {"done": False, "percentage": 0},
            "Awards": {"done": False, "percentage": 0}
        }

        # Debug log for progress steps
        print("Default progress steps:", progress_steps_default)

        # Step 4: Save the user data and progress steps in Firestore
        user_ref = db.collection("candidate").document(user.uid)
        user_data_to_store = {
            "email": user_data.email,
            "name": user_data.name,
            "lastName": user_data.lastName,
            "status": "PENDING",  # Use default status for sign up
            "createdAt": created_at,
            "progressSteps": progress_steps_default
        }

        # Debug log for final user data
        print("User data to store:", user_data_to_store)

        user_ref.set(user_data_to_store)

        return JSONResponse(
            content={"message": f"User account created successfully for user {user.uid}"},
            status_code=201
        )
    except Exception as e:
        print("Error during signup:", str(e))  # Log the error for debugging
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login")
async def login(user_data: LoginSchema = Body(..., example={
    "email": "user@example.com",
    "password": "your_password"
})):
    """
    Authenticates a user and returns a token upon successful login.
    Args:
        user_data (LoginSchema): The user data for login.
    Returns:
        JSONResponse: A response containing the authentication token.
    """

    try:
        user = firebase.auth().sign_in_with_email_and_password(
            user_data.email,
            user_data.password
        )
        token = user['idToken']
        return JSONResponse(content={"token": user['idToken']}, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        ) from e


@router.post("/ping")
async def validate_token(request: Request):
    """
    Validates a provided JWT token from the request headers.

    Args:
        request (Request): The request object containing the JWT token.

    Returns:
        dict: A dictionary containing the user ID if the token is valid.
    """
    jwt = request.headers.get("authorization")
    if not jwt:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        user = auth.verify_id_token(jwt)
        return {"user_id": user["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


