from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Body, Query, File, UploadFile
from fastapi.responses import JSONResponse
from firebase_admin import auth, firestore, storage
from app.firebase import firebase
from app.models import LoginSchema, SignUpSchema, ProfileStatus, ProgressModel, ProgressStep
from app.firebase import db, bucket
import uuid


router = APIRouter()


@router.post("/signup")
async def create_an_account(
        user_data: SignUpSchema = Body(
            ...,
            example={
                "email": "user@example.com",
                "password": "your_password",
                "name": "John",
                "lastName": "Doe"
            }
        )
):
    """
    Creates a new user account with the provided email and password,
    and stores user data in Firestore with default progress steps.
    """
    try:
        # Step 1: Create a new user in Firebase Authentication
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )

        # Step 2: Get current timestamp in ISO 8601 format
        created_at = datetime.utcnow().isoformat()

        # Step 3: Default progress steps
        progress_steps_default = {
            "Basic Information": {"done": False, "percentage": 0},
            "Education": {"done": False, "percentage": 0},
            "Work Experience": {"done": False, "percentage": 0},
            "Job Preference": {"done": False, "percentage": 0},
            "Skills": {"done": False, "percentage": 0},
            "Projects": {"done": False, "percentage": 0},
            "Awards": {"done": False, "percentage": 0}
        }

        # Debug log for progress steps
        print("Default progress steps:", progress_steps_default)

        # Step 4: Save the user data and progress steps in Firestore
        user_ref = db.collection("candidate").document(user.uid)
        user_data_to_store = {
            "email": user_data.email,
            "name": user_data.name,
            "lastName": user_data.lastName,
            "status": "PENDING",  # Use default status if missing
            "createdAt": created_at,
            "progressSteps": progress_steps_default
        }

        # Debug log for final user data
        print("User data to store:", user_data_to_store)

        user_ref.set(user_data_to_store)

        return JSONResponse(
            content={"message": f"User account created successfully for user {user.uid}"},
            status_code=201
        )
    except Exception as e:
        print("Error during signup:", str(e))  # Log the error for debugging
        raise HTTPException(status_code=400, detail=str(e)) from e





@router.post("/login")
async def login(user_data: LoginSchema = Body(..., example={
    "email": "user@example.com",
    "password": "your_password"
})):
    """
    Authenticates a user and returns a token upon successful login.

    Args:
        user_data (LoginSchema): The user data for login.

    Returns:
        JSONResponse: A response containing the authentication token.
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


@router.post("/ping")
async def validate_token(request: Request):
    """
    Validates a provided JWT token from the request headers.

    Args:
        request (Request): The request object containing the JWT token.

    Returns:
        dict: A dictionary containing the user ID if the token is valid.
    """
    jwt = request.headers.get("authorization")
    if not jwt:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        user = auth.verify_id_token(jwt)
        return {"user_id": user["user_id"]}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/candidates")
async def get_candidates():
    """
    Fetches candidate data from Firestore and returns it in a usable format.

    Returns:
        JSONResponse: A response containing the list of candidates.
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

    Args:
        email (str): The email of the candidate to fetch.

    Returns:
        JSONResponse: A response containing the candidate's data.
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


@router.post("/update-picture")
async def update_picture(
        candidate_id: str = Query(..., example="candidate123"),
        file: UploadFile = File(...)
):
    """
    Uploads a profile picture to Firebase Storage and links it to the candidate in Firestore.
    """
    try:
        # Step 1: Generate a unique file name
        file_extension = file.filename.split(".")[-1]
        file_name = f"profile-pictures/{candidate_id}-{uuid.uuid4()}.{file_extension}"

        # Step 2: Upload the file to Firebase Storage
        blob = bucket.blob(file_name)
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make the file publicly accessible
        download_url = blob.public_url

        # Step 3: Update the candidate's Firestore record with the profile picture URL
        candidate_ref = db.collection("candidate").document(candidate_id)
        candidate_doc = candidate_ref.get()

        if not candidate_doc.exists:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_ref.update({"profile_picture": download_url})

        return JSONResponse(
            content={
                "message": "Profile picture updated successfully",
                "profile_picture_url": download_url
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading picture: {str(e)}") from e


@router.post("/save-progress", tags=["Progress Management"])
async def save_progress(
        email: str = Query(..., example="nsovo1@example.com"),
        progress_steps: ProgressModel = Body(..., example={
            "steps": {
                "Personal Information": {"done": False, "percentage": 10},
                "Qualifications": {"done": False, "percentage": 10},
                "Work Experience": {"done": True, "percentage": 10},
                "Job Preference": {"done": True, "percentage": 10},
                "Skills": {"done": False, "percentage": 10},
                "Projects": {"done": False, "percentage": 10},
                "Awards": {"done": False, "percentage": 10}
            }
        })
):
    """
    Updates the progressSteps field for a candidate in Firestore by email.

    Args:
        email (str): The email of the candidate to update.
        progress_steps (ProgressModel): The object containing progress steps.

    Returns:
        JSONResponse: A response indicating the success or failure of the update.
    """
    try:
        # Find the candidate document by email
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("email", "==", email).stream()

        # Check if the candidate exists
        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]  # Assuming one document per email
        candidate_ref = candidates_ref.document(candidate_doc.id)

        # Update the progressSteps field in Firestore
        candidate_ref.update({"progressSteps": progress_steps.steps})

        return JSONResponse(
            content={"message": "Progress steps updated successfully"},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating progress steps: {str(e)}"
        ) from e