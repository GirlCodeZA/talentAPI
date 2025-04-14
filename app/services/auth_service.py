import requests
from firebase_admin import auth
from app.config import firebase_config

def verify_current_password(email: str, password: str):
    url = f"{firebase_config['signInWithPasswordBaseURL']}?key={firebase_config['apiKey']}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError("Invalid current password")

def verify_current_password(email: str, password: str, api_key: str):
    url = f"{firebase_config['signInWithPasswordBaseURL']}?key={firebase_config['apiKey']}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError("Invalid current password")

def update_password(uid: str, new_password: str):
    auth.update_user(uid, password=new_password)
