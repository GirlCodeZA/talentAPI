import uuid

from fastapi import APIRouter, HTTPException, Body, Query, File, UploadFile, Request
from fastapi.responses import JSONResponse

from typing import List

from app.firebase import db, bucket
from app.models import ProgressModel, BasicInformation, Education

candidate_router = APIRouter()

@candidate_router.get("/candidate")
async def get_candidate_by_email(email: str = Query(..., example="nsovo1@example.com")):
    """
    Fetch a candidate's data from Firestore by email.

    Args:
        email (str): The email of the candidate to fetch.

    Returns:
        JSONResponse: A response containing the candidate's data with sorted progressSteps.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("email", "==", email).stream()

        candidates = []
        correct_order = [
            "Basic Information",
            "Education",
            "Work Experience",
            "Job Preference",
            "Skills",
            "Projects",
            "Awards"
        ]

        for doc in query:
            doc_data = doc.to_dict()

            # Get progressSteps and sort it
            progress_steps_data = doc_data.get("progressSteps", {})
            sorted_progress_steps = {
                step: progress_steps_data[step] for step in correct_order if step in progress_steps_data
            }

            # Update the candidate's data with sorted progressSteps
            candidates.append({
                "id": doc.id,  # Document ID
                **doc_data,  # All other fields
                "progressSteps": sorted_progress_steps  # Sorted progressSteps
            })

        if not candidates:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return JSONResponse(content={"candidates": candidates}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}") from e


# @candidate_router.post("/add-basic-details")
# async def add_basic_details(basic_info: BasicInformation):
#     """
#     Adds basic details of a candidate to the database.
#
#     Args:
#         basic_info (BasicInformation): The basic information of the candidate.
#
#     Returns:
#         JSONResponse: A response indicating the success or failure of the operation.
#     """
#     try:
#         candidate_ref = db.collection("candidate").document(basic_info.id)
#         candidate_doc = candidate_ref.get()
#
#         if not candidate_doc.exists:
#             raise HTTPException(status_code=404, detail="Candidate not found")
#
#         candidate_ref.update({
#             "phone": basic_info.phone,
#             "passport": basic_info.passport,
#             "city": basic_info.city,
#             "country": basic_info.country,
#             "role": basic_info.role,
#             "urls": {
#                 "linkedIn": basic_info.Urls.linkedIn,
#                 "github": basic_info.Urls.github,
#             }
#         })
#
#         return JSONResponse(
#             content={"message": "Basic details added successfully"},
#             status_code=200
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Error adding basic details: {str(e)}"
#         ) from e


@candidate_router.post("/update-picture")
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


@candidate_router.post("/save-progress", tags=["Candidate Management"])
async def save_progress(
        email: str = Query(..., example="nsovo1@example.com"),
        progress_steps: dict = Body(...)
):
    """
    Updates the progressSteps field for a candidate in Firestore by email.

    Args:
        email (str): The email of the candidate to update.
        progress_steps (dict): The object containing progress steps.

    Returns:
        JSONResponse: A response indicating the success or failure of the update.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]  # Assuming one document per email
        candidate_ref = candidates_ref.document(candidate_doc.id)

        existing_progress_steps = candidate_doc.to_dict().get("progressSteps", {})

        # Define the correct order of progress steps
        correct_order = [
            "Basic Information",
            "Education",
            "Work Experience",
            "Job Preference",
            "Skills",
            "Projects",
            "Awards"
        ]

        for step in correct_order:
            if step not in existing_progress_steps:
                existing_progress_steps[step] = {"done": False, "percentage": 0}

        # Merge new progress updates with existing ones
        for step, values in progress_steps.items():
            if step in existing_progress_steps:
                existing_progress_steps[step].update(values)

        candidate_ref.update({"progressSteps": existing_progress_steps})

        return JSONResponse(
            content={"message": "Progress steps updated successfully", "progressSteps": existing_progress_steps},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating progress steps: {str(e)}"
        ) from e



@candidate_router.get("/list-candidates", tags=["Candidate Management"])
async def list_candidates():
    candidates = db.collection("candidate").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in candidates]


@candidate_router.put("/update-basic-info", tags=["Candidate Management"])
async def update_basic_information(basic_info: BasicInformation = Body(...)):
    """
    Updates basic information for a candidate in Firestore by email.
    """
    try:
        candidates_ref = db.collection("candidate").where("email", "==", basic_info.email).stream()

        candidate_doc = None
        candidate_id = None

        for doc in candidates_ref:
            candidate_doc = doc.to_dict()
            candidate_id = doc.id
            break

        if not candidate_doc:
            print(f"Candidate with email {basic_info.email} not found in Firestore.")  # Debugging
            raise HTTPException(status_code=404, detail=f"Candidate with email {basic_info.email} not found")

        candidate_ref = db.collection("candidate").document(candidate_id)
        candidate_ref.update(basic_info.dict())

        return JSONResponse(content={"message": "Candidate information updated successfully"}, status_code=200)

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating candidate information: {str(e)}")


@candidate_router.post("/save-education", tags=["Candidate Management"])
async def save_education(
        email: str = Query(..., example="nsovo1@example.com"),
        educationList: List[Education] = []
):
    """
    Updates the education field for a candidate in Firestore by email.

    Args:
        email (str): The email of the candidate to update.
        educationList (List[Education]): The list of education records.

    Returns:
        JSONResponse: A response indicating the success or failure of the update.
    """
    try:
        candidates_ref = db.collection("candidate")
        query = candidates_ref.where("email", "==", email).stream()

        candidate_docs = [doc for doc in query]
        if not candidate_docs:
            raise HTTPException(status_code=404, detail="Candidate not found")

        candidate_doc = candidate_docs[0]
        candidate_ref = candidates_ref.document(candidate_doc.id)

        existing_education = candidate_doc.to_dict().get("education", [])

        updated_education = existing_education + [edu.dict() for edu in educationList]

        candidate_ref.update({"education": updated_education})

        return JSONResponse(
            content={"message": "Education data saved successfully", "education": updated_education},
            status_code=200
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating education data: {str(e)}"
        ) from e




