from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse
from firebase_admin import auth, firestore
from app.firebase import firebase
from app.models import LoginSchema, SignUpSchema, ProfileStatus

# Initialize Firestore client
db = firestore.client()

router = APIRouter()

@router.post("/signup")
async def create_an_account(user_data: SignUpSchema = Body(..., example={
    "email": "user@example.com",
    "password": "your_password",
    "name": "John",
    "lastName": "Doe"
})):
    """
    Creates a new user account with the provided email and password, and stores user data in Firestore.
    """
    try:
        # Step 1: Create a new user in Firebase Authentication
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )

        # Step 2: Get current timestamp in ISO 8601 format
        created_at = datetime.utcnow().isoformat()

        # Step 3: Save the user data in Firestore
        user_ref = db.collection("candidate").document(user.uid)
        user_ref.set({
            "email": user_data.email,
            "name": user_data.name,
            "lastName": user_data.lastName,
            "status": ProfileStatus.PENDING,
            "createdAt": created_at
        })

        return JSONResponse(
            content={"message": f"User account created successfully for user {user.uid}"},
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login")
async def login(user_data: LoginSchema = Body(..., example={
    "email": "user@example.com",
    "password": "your_password"
})):
    """
    Authenticates a user and returns a token upon successful login.
    """
    try:
        # Firebase authentication login
        user = firebase.auth().sign_in_with_email_and_password(
            user_data.email,
            user_data.password
        )
        return JSONResponse(content={"token": user['idToken']}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/candidates")
async def get_candidates():
    """
    Fetches candidate data from Firestore and returns it in a usable format.
    """
    try:
        # Fetch documents from the "candidate" collection
        candidates_ref = db.collection("candidate")
        docs = candidates_ref.stream()

        # Map Firestore documents to a usable format
        candidates_data = []
        for doc in docs:
            doc_data = doc.to_dict()
            candidates_data.append({
                "id": doc.id,  # Document ID
                **doc_data  # All other fields
            })

        return JSONResponse(content={"candidates": candidates_data}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}") from e



@router.get("/candidate")
async def get_candidate_by_email(email: str = Query(..., example="nsovo1@example.com")):
    """
    Fetch a candidate's data from Firestore by email.
    """
    try:
        # Query Firestore for a candidate with the provided email
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("email", "==", email).stream()

        # Extract the candidate data
        candidates = []
        for doc in query:
            doc_data = doc.to_dict()
            candidates.append({
                "id": doc.id,  # Document ID
                **doc_data  # All other fields
            })

        # Check if candidate exists
        if not candidates:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return JSONResponse(content={"candidates": candidates}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}") from e


@router.post("/ping")
async def validate_token(request: Request):
    """
    Validates a provided JWT token from the request headers.
    """
    jwt = request.headers.get("authorization")
    if not jwt:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        user = auth.verify_id_token(jwt)
        return {"user_id": user["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
