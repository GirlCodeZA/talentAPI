from firebase_admin import firestore
from fastapi import HTTPException
from app.firebase import db

def fetch_candidate_by_email(email: str):
    email = email.strip().lower()
    print("Searching for email:", email)

    candidates_ref = db.collection("candidate")
    query = candidates_ref.where("basicInfo.email", "==", email).stream()

    found = False
    for doc in query:
        found = True
        candidate = doc.to_dict()
        candidate["id"] = doc.id
        print("Candidate found:", candidate)
        return candidate

    if not found:
        print("No candidate matched the email.")

    return None

