"""
Main entry point for the Talent FastAPI application.
Sets up the FastAPI instance and registers routes.
"""

from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.admin import admin_router
from app.routes.candidate import candidate_router as candidate_router
from app.routes.employer import employer_router
from app.routes.jobs import router as job_router
from app.routes.matched import router as matched_job_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Talent FastAPI",
    description="Talent API",
    docs_url="/",
)

# Configure CORS
origins = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:8082",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost",
    "http://13.247.71.38"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routes
app.include_router(auth_router)
# app.include_router(candidate_router)
app.include_router(job_router)
app.include_router(matched_job_router)
app.include_router(candidate_router, prefix="/candidate", tags=["Candidate Management"])
app.include_router(employer_router, prefix="/employer", tags=["Employer Management"])
app.include_router(admin_router, prefix="/admin", tags=["Admin Management"])


