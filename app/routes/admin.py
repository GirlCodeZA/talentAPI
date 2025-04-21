from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from firebase_admin import firestore
from app.utils import get_user_collection

admin_router = APIRouter()
db = firestore.client()

@admin_router.get("/users", tags=["Admin Management"])
async def list_users(
        userType: str = Query(...),
        search: str = Query(None),
        status: str = Query(None)
):
    try:
        ref = get_user_collection(userType, db)
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
async def update_user_status(email: str = Query(...), status: str = Query(...), userType: str = Query(...)):
    try:
        ref = get_user_collection(userType, db)
        query = ref.where("basicInfo.email" if userType == "candidate" else "email", "==", email).stream()

        docs = [doc for doc in query]
        if not docs:
            raise HTTPException(status_code=404, detail=f"{userType.capitalize()} not found")

        ref.document(docs[0].id).update({"status": status})

        return {"message": f"Status for {email} updated to {status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@admin_router.get("/stats", tags=["Admin Management"])
async def get_platform_stats():
    try:
        stats = {}
        for user_type in ["candidate", "employer"]:
            ref = get_user_collection(user_type, db)
            stats[user_type] = len([_ for _ in ref.stream()])

        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
