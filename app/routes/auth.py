from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Body, status
from fastapi.responses import JSONResponse
from firebase_admin import auth

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.settings import settings

from app.config import SENDGRID_API_KEY, SENDER_EMAIL  # your config setup

from app.models.models import SignUpSchema, ProgressModel, LoginSchema, ProfileStatus, UserType, ForgotPasswordRequest
from app.utils.logger import log_error

from app.config import firebase_config
from app.services.auth_service import verify_current_password, update_password
from app.firebase import db
from app.firebase import firebase

from pydantic import EmailStr

import requests

GITHUB_USER_API = "https://api.github.com/user"
GITHUB_EMAILS_API = "https://api.github.com/user/emails"

router = APIRouter()

@router.post("/signup", tags=["Auth"])
async def create_an_account(user_data: SignUpSchema = Body(...)):
    try:
        try:
            auth.get_user_by_email(user_data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please log in or use a different email."
            )
        except auth.UserNotFoundError:
            pass

        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )

        created_at = datetime.utcnow().isoformat()

        data_to_store = {
            "uid": user.uid,
            "status": ProfileStatus.PENDING,
            "createdAt": created_at,
            "userType": user_data.userType,
        }

        if user_data.userType == UserType.CANDIDATE:
            progress_steps_default = ProgressModel.default_steps()
            data_to_store["progressSteps"] = {
                key: step.dict() for key, step in progress_steps_default.items()
            }
            data_to_store["basicInfo"] = {
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "email": user_data.email
            }
            collection = "candidate"

        elif user_data.userType == UserType.EMPLOYER:
            data_to_store.update({
                "firstName": user_data.firstName,
                "lastName": user_data.lastName,
                "email": user_data.email,
                "contactNumber": user_data.contactNumber,
                "companyName": user_data.companyName
            })
            collection = "employer"

        else:
            raise HTTPException(status_code=400, detail="Invalid user type")

        db.collection(collection).document(user.uid).set(data_to_store)

        return JSONResponse(
            content={"message": f"Account created successfully. User ID: {user.uid}"},
            status_code=status.HTTP_201_CREATED
        )

    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please log in or use a different email."
        )
    except Exception as e:
        print("Error during signup:", str(e))
        await log_error("Signup failed", {
            "email": user_data.email,
            "error": str(e),
            "endpoint": "/signup"
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating account: {str(e)}"
        )


@router.post("/login", tags=["Auth"])
async def login(user_data: LoginSchema = Body(...)):
    try:
        user = firebase.auth().sign_in_with_email_and_password(
            user_data.email,
            user_data.password
        )
        token = user['idToken']

        user_type = None
        for utype in ["candidate", "employer","admin"]:
            if utype == "candidate":
                docs = list(db.collection(utype).where("basicInfo.email", "==", user_data.email).stream())
            else:
                docs = list(db.collection(utype).where("email", "==", user_data.email).stream())

            if docs:
                user_type = utype
                break

        if not user_type:
            raise HTTPException(status_code=404, detail="User type not found.")

        return JSONResponse(
            content={
                "token": token,
                "userType": user_type,
                "redirect": f"{user_type.capitalize()}/Dashboard"
            },
            status_code=200
        )

    except Exception as e:
        await log_error("Login failed", {
            "email": user_data.email,
            "error": str(e),
            "endpoint": "/login"
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/send-verification-email", tags=["Auth"])
async def send_verification_email(email: EmailStr):
    try:
        user = auth.get_user_by_email(email)
        link = auth.generate_email_verification_link(email)

        # Ideally: Send link via email service like SendGrid or Mailgun
        print(f"Verification link for {email}: {link}")

        return {"message": "Verification email sent (check your inbox)", "link": link}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/ping", tags=["App Health"])
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



@router.post("/change-password", tags=["Auth"])
async def change_password(
        email: str = Body(...),
        current_password: str = Body(...),
        new_password: str = Body(...)
):
    try:
        api_key = firebase_config["apiKey"]

        _ = verify_current_password(email, current_password, api_key)

        uid = auth.get_user_by_email(email).uid
        update_password(uid, new_password)

        return {"message": "Password updated successfully"}

    except ValueError:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/github-login", tags=["Auth"])
async def github_login(idToken: str = Body(..., embed=True)):
    """
    Verifies the Firebase ID token from GitHub OAuth login
    and returns user details or creates them in Firestore.
    """
    try:
        decoded_token = auth.verify_id_token(idToken)
        uid = decoded_token['uid']
        email = decoded_token.get('email')

        # Check if user already exists in Firestore
        user_ref = db.collection("candidate").document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            # Create a minimal user entry
            created_at = datetime.utcnow().isoformat()
            user_data_to_store = {
                "uid": uid,
                "status": "PENDING",
                "createdAt": created_at,
                "basicInfo": {
                    "email": email,
                    "firstName": "",  # optional: you could pull from decoded_token
                    "lastName": ""
                },
                "progressSteps": ProgressModel.default_steps()
            }
            user_ref.set(user_data_to_store)

        return JSONResponse(content={"message": "GitHub login successful", "uid": uid}, status_code=200)

    except Exception as e:
        print("GitHub login error:", e)
        raise HTTPException(status_code=401, detail="Invalid ID token or user verification failed")


@router.post("/github-login", tags=["Auth"])
async def github_login(accessToken: str = Body(..., embed=True)):
    """
    Verifies GitHub OAuth access token, fetches user data, and returns Firebase custom token.
    """
    try:
        # Get GitHub user info
        headers = {"Authorization": f"Bearer {accessToken}"}
        user_response = requests.get(GITHUB_USER_API, headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        # Get primary email (in case it's not public in `user_data`)
        email_response = requests.get(GITHUB_EMAILS_API, headers=headers)
        email_response.raise_for_status()
        email_data = email_response.json()
        primary_email = next((e["email"] for e in email_data if e.get("primary")), None)

        github_uid = f"github:{user_data['id']}"
        display_name = user_data.get("name") or user_data.get("login")
        email = primary_email or user_data.get("email")

        # Create or get Firebase user
        try:
            user = auth.get_user(github_uid)
        except auth.UserNotFoundError:
            user = auth.create_user(
                uid=github_uid,
                display_name=display_name,
                email=email,
            )

        # Create custom Firebase token
        custom_token = auth.create_custom_token(github_uid)

        # Firestore user setup
        user_ref = db.collection("candidate").document(github_uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            created_at = datetime.utcnow().isoformat()
            user_data_to_store = {
                "uid": github_uid,
                "status": "PENDING",
                "createdAt": created_at,
                "basicInfo": {
                    "email": email,
                    "firstName": display_name.split()[0] if display_name else "",
                    "lastName": " ".join(display_name.split()[1:]) if display_name and len(display_name.split()) > 1 else ""
                },
                "progressSteps": ProgressModel.default_steps()
            }
            user_ref.set(user_data_to_store)

        return JSONResponse(content={"customToken": custom_token.decode('utf-8')}, status_code=200)

    except Exception as e:
        print("GitHub login error:", e)
        raise HTTPException(status_code=401, detail="GitHub login failed.")


@router.post("/forgot-password", tags=["Auth"])
async def forgot_password(request: ForgotPasswordRequest):
    print("SENDGRID_API_KEY =", repr(settings.sendgrid_api_key))

    try:
        # Generate reset link
        reset_link = auth.generate_password_reset_link(request.email)

        # Compose email
        message = Mail(
            from_email=settings.sender_email,
            to_emails=request.email,
            subject="Reset Your Password",
            html_content=f"""
                <p>Hello,</p>
                <p>You requested a password reset. Click the link below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>If you did not request this, please ignore this email.</p>
            """
        )

        # Send email
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        sg.send(message)

        return {"message": "Password reset email sent successfully"}

    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except auth.ResetPasswordExceedLimitError:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests. Please try again later."
        )
    except Exception as e:
        print("Forgot password error:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to send password reset email")


