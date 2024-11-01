"""
Initializes Firebase and Firebase Admin SDK for use in the application.
"""

import pyrebase
from firebase_admin import credentials, initialize_app
from app.config import firebase_config

firebase = pyrebase.initialize_app(firebase_config)

# Initialize Firebase Admin SDK
def init_firebase():
    """
    Initializes Firebase Admin SDK if it hasn't been initialized already.
    """
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        initialize_app(cred)
    except ValueError:
        # Firebase Admin is already initialized
        pass

init_firebase()
