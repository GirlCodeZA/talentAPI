import os
import json
from fastapi import FastAPI, APIRouter, HTTPException, status, Body
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pydantic import BaseModel, EmailStr
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, EmailStr

import logging

from firebase_admin import auth
from firebase_admin._auth_utils import ResetPasswordExceedLimitError

from app.settings import settings
from app.config import SENDGRID_API_KEY
from app.models.models import ForgotPasswordRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
mail_router = APIRouter()

env = Environment(loader=FileSystemLoader("app/templates"))

class User(BaseModel):
    email: EmailStr
    name: str
    username: str
    password: str

def render_email_template(name: str, username: str, password: str) -> str:
    """Renders the send_password_template.html with Jinja2 placeholders."""
    template = env.get_template("send_password_template.html")
    return template.render(
        name=name,
        username=username,
        password=password
    )

@mail_router.post("/send-welcome-email/", tags=["Mail Management"])
async def send_welcome_email(user: User):
    print("SENDGRID_API_KEY:", SENDGRID_API_KEY)

    # Render HTML email using Jinja2
    email_html = render_email_template(user.name, user.username, user.password)

    message = Mail(
        from_email='nsovom@girlcode.co.za',  # must be verified in SendGrid
        to_emails=user.email,
        subject='Welcome to Our Platform!',
        html_content=email_html
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg_debug_info = {
            "class": str(type(sg)),
            "api_key_present": SENDGRID_API_KEY is not None,
            "base_url": getattr(sg, "host", "Not available"),
        }
        print("DEBUG SG:", json.dumps(sg_debug_info, indent=2))

        response = sg.send(message)
        logger.info("Email sent successfully")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.body}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        return {
            "message": "Email sent",
            "status_code": response.status_code,
            "sendgrid_message_id": response.headers.get("X-Message-Id")
        }

    except Exception as e:
        return {"error": str(e)}

def render_sign_up_welcome_template(name: str) -> str:
    """Renders the send_password_template.html with Jinja2 placeholders."""
    template = env.get_template("sign_up_welcome.html")
    return template.render(
        name=name,
    )

@mail_router.post("/send-sign-up-welcome-email/", tags=["Mail Management"])
async def send_sign_up_welcome_email(email: EmailStr, name: str):
    print("SENDGRID_API_KEY:", SENDGRID_API_KEY)

    email_html = render_sign_up_welcome_template(name)

    message = Mail(
        from_email='nsovom@girlcode.co.za',
        to_emails=email,
        subject='Welcome to Talent!',
        html_content=email_html
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent to {email}, status: {response.status_code}")
        return {
            "message": "Welcome email sent",
            "status_code": response.status_code,
            "sendgrid_message_id": response.headers.get("X-Message-Id")
        }
    except Exception as e:
        return {"error": str(e)}

def render_reset_password_template(reset_link: str, recipient_name: str = "User") -> str:
    """
    Renders the reset_password_email.html with Jinja2 placeholders.
    Template must exist in app/templates/reset_password_email.html
    """
    template = env.get_template("reset_password_email.html")
    return template.render(
        name=recipient_name,
        reset_link=reset_link
    )

@mail_router.post("/forgot-password", tags=["Mail Management"])
async def forgot_password(request: ForgotPasswordRequest = Body(...)):
    logger.info(f"Password reset requested for: {request.email}")

    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=500, detail="SendGrid API Key is missing")

    sender = settings.sender_email or "nsovom@girlcode.co.za"

    try:
        # Generate reset link
        reset_link = auth.generate_password_reset_link(request.email)
        email_html = render_reset_password_template(reset_link)

        message = Mail(
            from_email=sender,
            to_emails=request.email,
            subject="Reset Your Password",
            html_content=email_html
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(f"Password reset email sent to {request.email}")
        return {
            "message": f"Password reset email sent successfully to {request.email}",
            "status_code": response.status_code,
            "sendgrid_message_id": response.headers.get("X-Message-Id")
        }

    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except ResetPasswordExceedLimitError:
        raise HTTPException(
            status_code=429,
            detail="Too many password reset requests. Please try again later."
        )
    except Exception as e:
        logger.error(f"Failed to send reset password email: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send password reset email: {str(e)}")