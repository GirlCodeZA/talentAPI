
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

"""
Configuration file for Firebase settings.
"""

firebase_config = {
    "apiKey": "AIzaSyBfdQmnLpJd_hGdiU1mQYoGW-LMjom_U20",
    "authDomain": "talent-4e063.firebaseapp.com",
    "projectId": "talent-4e063",
    "storageBucket": "talent-4e063.appspot.com",
    "messagingSenderId": "111415801370",
    "appId": "1:111415801370:web:f86c07eef4b0a9f00e03a3",
    "measurementId": "G-WGQHXRBEF3",
    "databaseURL": "",
    "signInWithPasswordBaseURL": "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
}


""" SendGrid configuration for sending emails."""
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "nsovom@girlcode.com"  # Must be a verified sender in SendGrid

