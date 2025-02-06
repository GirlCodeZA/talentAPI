import uuid

from fastapi import APIRouter, HTTPException, Body, Query, File, UploadFile
from fastapi.responses import JSONResponse

from app.firebase import db, bucket
from app.models import ProgressModel, BasicInformation

router = APIRouter()
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


@router.post("/basic-details")
async def add_basic_details(basic_info: BasicInformation):
    """
    Adds basic details of a candidate to the database.

    Args:
        basic_info (BasicInformation): The basic information of the candidate.

    Returns:
        JSONResponse: A response indicating the success or failure of the operation.
    """
    try:
        # Step 1: Validate that the candidate exists in Firestore
        candidate_ref = db.collection("candidate").document(basic_info.id)
        candidate_doc = candidate_ref.get()

        if not candidate_doc.exists:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Step 2: Update Firestore document with basic information
        candidate_ref.update({
            "phone": basic_info.phone,
            "passport": basic_info.passport,
            "city": basic_info.city,
            "country": basic_info.country,
            "role": basic_info.role,
            "urls": {
                "linkedIn": basic_info.Urls.linkedIn,
                "github": basic_info.Urls.github,
            }
        })

        return JSONResponse(
            content={"message": "Basic details added successfully"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding basic details: {str(e)}"
        ) from e


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


@router.put("/update-basic-info/{candidate_id}", tags=["Candidate Management"])
async def update_basic_information(candidate_id: str, basic_info: BasicInformation = Body(...)):
    """
    Updates basic information for a candidate in Firestore by candidate ID.

    Args:
        candidate_id (str): The ID of the candidate document.
        basic_info (BasicInformation): The object containing updated candidate details.

    Returns:
        JSONResponse: A response indicating the success or failure of the operation.
    """
    try:
        # Reference to the candidate document
        candidate_ref = db.collection("candidate").document(candidate_id)
        if not candidate_ref.get().exists:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Update the candidate document
        candidate_ref.update(basic_info.dict())

        return JSONResponse(
            content={"message": "Candidate information updated successfully"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating candidate information: {str(e)}"
        ) from e


