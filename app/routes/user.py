from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from firebase_admin import firestore
from typing import List

from app.models.shared import UserType
from app.routes.admin import admin_router

router = APIRouter()
db = firestore.client()

@admin_router.get("/all-users", tags=["Ca Management"])
async def get_all_users():
    try:
        users = []

        # Admins
        admins_ref = db.collection("admins")
        for doc in admins_ref.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["userType"] = UserType.ADMIN
            users.append(data)

        # Employers
        employers_ref = db.collection("employer")
        for doc in employers_ref.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["userType"] = UserType.EMPLOYER
            users.append(data)

        # Candidates
        candidates_ref = db.collection("candidates")
        for doc in candidates_ref.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["userType"] = UserType.CANDIDATE
            users.append(data)

        return JSONResponse(content=users)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")
