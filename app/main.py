"""
Main entry point for the Talent FastAPI application.
Sets up the FastAPI instance, configures CORS, and registers routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routes.auth import router as auth_router
from app.routes.admin import admin_router
from app.routes.candidate import candidate_router
from app.routes.employer import employer_router
from app.routes.mail import mail_router
from app.routes.jobs import router as job_router
from app.routes.matched import router as matched_job_router
from app.routes.mesage import chat_router
from app.routes.careerCoach import career_coach_router

app = FastAPI(
    title="Talent FastAPI",
    description="Talent API",
    docs_url="/",  # Swagger UI at root
)

# --------- CORS ---------
ALLOWED_ORIGINS = [
    "https://api.talent.girlcode.co.za",
    "https://talent-4e063.web.app/"
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow any localhost / 127.0.0.1 / LAN IP with any port in development.
# (Requests must still be http/https and match the regex.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\d{1,3}(?:\.\d{1,3}){3})(:\d+)?$",
    allow_credentials=True,   # set True if you use cookies/Authorization headers
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Routers ---------
app.include_router(auth_router)
app.include_router(job_router)
app.include_router(matched_job_router)
app.include_router(candidate_router, prefix="/candidate", tags=["Candidate"])
app.include_router(employer_router, prefix="/employer", tags=["Employer"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(mail_router, prefix="/mail", tags=["Mail"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(career_coach_router, prefix="/Coach", tags=["Career Coach"])

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
