"""
Main entry point for the Talent FastAPI application.
Sets up the FastAPI instance and registers routes.
"""

from fastapi import FastAPI
from app.auth_routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Talent FastAPI",
    description="Talent API",
    docs_url="/",
)

# Configure CORS
origins = [
    "http://localhost:8081",  # Your frontend's origin
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
