"""
Main entry point for the Talent FastAPI application.
Sets up the FastAPI instance and registers routes.
"""

from fastapi import FastAPI
from app.auth_routes import router as auth_router


app = FastAPI(
    title="Talent FastAPI",
    description="Talent API",
    docs_url="/",
)

# Register routes
app.include_router(auth_router)
