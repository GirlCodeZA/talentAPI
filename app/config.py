
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

"""
Configuration file for Firebase settings.
"""

firebase_config = {
    "apiKey": "AIzaSyDzQy9RklkGFuoVCnJnA51P5wbHxJZpGKs",
    "authDomain": "talent-dd7dd.firebaseapp.com",
    "projectId": "talent-firestore-access",
    "storageBucket": "talent-dd7dd.appspot.com",
    "messagingSenderId": "565928155897",
    "appId": "1:565928155897:web:74e66194deb6f390876028",
    "measurementId": "G-M000JMGV0W",
    "databaseURL": "",
    "signInWithPasswordBaseURL": "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
}


""" SendGrid configuration for sending emails."""
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "nsovom@girlcode.com"  # Must be a verified sender in SendGrid

