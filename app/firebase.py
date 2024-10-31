# app/firebase.py

import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, initialize_app
from app.config import firebase_config

firebase = pyrebase.initialize_app(firebase_config)

# Initialize Firebase Admin SDK
def init_firebase():
    if not firebase_admin._apps:  # Corrected check for initialized apps
        cred = credentials.Certificate("serviceAccountKey.json")
        initialize_app(cred)

init_firebase()
