def get_user_collection(user_type: str, db):
    # Can be "candidate", "employer", or "admin"
    return db.collection(user_type.lower())