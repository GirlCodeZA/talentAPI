from fastapi import APIRouter, Query, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from firebase_admin import firestore
from datetime import datetime
from typing import Optional

from app.models.admin import ADMIN
from app.models.shared import UserType

# from app.auth import get_current_user

admin_router = APIRouter()
db = firestore.client()


# def admin_required(user: User = Depends(get_current_user)):
#     if user.userType != 'admin':
#         raise HTTPException(status_code=403, detail="Admin access required")
#     return user


@admin_router.post("/create-admin", tags=["Admin Management"])
async def create_admin(admin_data: ADMIN = Body(...)):
    try:
        admin_ref = db.collection("admin")
        existing = admin_ref.where("email", "==", admin_data.email).stream()
        existing_docs = [doc for doc in existing]
        if existing_docs:
            raise HTTPException(status_code=400, detail="Admin with this email already exists")

        now_str = datetime.utcnow().isoformat()
        admin_data.createdAt = now_str
        admin_data.updatedAt = now_str
        admin_data.userType = "admin"

        new_ref = admin_ref.document()
        new_ref.set(admin_data.dict())

        return JSONResponse(
            content={"message": "Admin user created successfully", "id": new_ref.id},
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create admin: {str(e)}")



@admin_router.get("/get-admin", tags=["Admin Management"])
async def get_admin(email: str = Query(..., description="Admin email")):
    try:
        admin_ref = db.collection("admin")
        query = admin_ref.where("email", "==", email).stream()
        docs = [doc for doc in query]

        if not docs:
            raise HTTPException(status_code=404, detail="Admin not found")

        admin_data = docs[0].to_dict()
        return JSONResponse(
            content={"id": docs[0].id, **admin_data},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin: {str(e)}")



@admin_router.get("/users", tags=["Admin Management"])
# @admin_router.get("/admin/companies", dependencies=[Depends(admin_required)])
async def list_users(
    userType: str = Query(...),
    search: str = Query(None),
    status: str = Query(None)
):
    try:
        ref = db.collection(userType.lower())
        query = ref.stream()

        users = []
        for doc in query:
            data = doc.to_dict()
            match = True

            if search:
                search_lower = search.lower()
                if userType == "candidate":
                    match = search_lower in data.get("basicInfo", {}).get("firstName", "").lower() or \
                            search_lower in data.get("basicInfo", {}).get("lastName", "").lower() or \
                            search_lower in data.get("basicInfo", {}).get("email", "").lower()
                else:
                    match = search_lower in data.get("companyName", "").lower() or \
                            search_lower in data.get("email", "").lower()

            if status and data.get("status") != status:
                match = False

            if match:
                users.append({"id": doc.id, **data})

        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@admin_router.put("/update-status", tags=["Admin Management"])
async def update_user_status(
    email: str = Query(...),
    status: str = Query(...),
    userType: str = Query(...)
):
    try:
        collection = db.collection(userType.lower())
        key = "basicInfo.email" if userType == "candidate" else "email"
        query = collection.where(key, "==", email).stream()

        docs = [doc for doc in query]
        if not docs:
            raise HTTPException(status_code=404, detail=f"{userType.capitalize()} not found")

        collection.document(docs[0].id).update({"status": status})

        return {"message": f"Status for {email} updated to {status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@admin_router.get("/stats", tags=["Admin Management"])
async def get_platform_stats():
    try:
        stats = {}
        for user_type in ["candidate", "employer"]:
            ref = db.collection(user_type)
            stats[user_type] = len([_ for _ in ref.stream()])
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from enum import Enum
from typing import Optional
from firebase_admin import firestore  # Assuming Firestore is used

admin_router = APIRouter()
db = firestore.client()  # Firestore client instance

class UserType(str, Enum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    CANDIDATE = "candidate"

@admin_router.get("/all-users", tags=["Admin Management"])
async def get_all_users(user_type: Optional[UserType] = Query(None, description="Filter by userType")):
    """
    Retrieve all users. Optionally filter by userType: admin, employer, or candidate.
    """
    try:
        users = []

        user_collections = {
            UserType.ADMIN: "admin",
            UserType.EMPLOYER: "employer",
            UserType.CANDIDATE: "candidate"
        }

        if user_type:
            collections_to_query = [user_type]
        else:
            collections_to_query = list(user_collections.keys())

        for utype in collections_to_query:
            for doc in db.collection(user_collections[utype]).stream():
                data = doc.to_dict()
                data["id"] = doc.id
                data["userType"] = utype
                users.append(data)

        return JSONResponse(content=users)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

