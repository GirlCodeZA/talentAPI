from firebase_admin import credentials, initialize_app, firestore, storage
import pyrebase
from app.config import firebase_config
import os

# Initialize Pyrebase
firebase = pyrebase.initialize_app(firebase_config)

# Initialize Firebase Admin SDK
def init_firebase():
    """
    Initializes Firebase Admin SDK if it hasn't been initialized already.
    """
    try:
        cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json"))
        initialize_app(cred, {
            "storageBucket": os.getenv("FIREBASE_BUCKET", "your-project-id.appspot.com")
        })
    except ValueError:
        # Firebase Admin is already initialized
        pass

init_firebase()

# Export Firestore and Storage
db = firestore.client()
bucket = storage.bucket()
