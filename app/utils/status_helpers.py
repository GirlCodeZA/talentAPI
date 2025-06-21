from fastapi import HTTPException
from firebase_admin import firestore
from app.models.shared import ProfileStatus

db = firestore.client()

async def update_profile_status_by_email(collection: str, email: str, status: ProfileStatus) -> str:
    try:
        ref = db.collection(collection)

        # Handle nested email field only for candidates
        email_field = "basicInfo.email" if collection == "candidate" else "email"

        query = ref.where(email_field, "==", email).stream()
        doc = next(query, None)

        if not doc:
            raise HTTPException(status_code=404, detail=f"{collection.capitalize()} not found")

        ref.document(doc.id).update({"status": status.value})

        return f"{collection.capitalize()} status updated to '{status.value}' for {email}"

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating {collection} status: {str(e)}")
