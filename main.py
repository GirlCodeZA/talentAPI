from fastapi import FastAPI
import uvicorn
import pyrebase

import firebase_admin
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import credentials,auth
from starlette import status

import MODELS
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import Depends

import bcrypt
import requests
app = FastAPI(
    description = "GirlCode Talent App to help young women in Tech find jobs",
    title= "Firebase Auth",
    docs_url= "/"
)

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)


firebaseConfig = {
"apiKey": "AIzaSyCLLY0NwXljTkfZSOIo-l2dD_HyxZC3AaU",
 "authDomain": "girlcode1be1trial.firebaseapp.com",
  "projectId": "girlcode1be1trial",
  "storageBucket": "girlcode1be1trial.firebasestorage.app",
  "messagingSenderId": "915243864109",
  "appId": "1:915243864109:web:467e464f9f89d86f1168a4",
  "measurementId": "G-YP39CZSCLR",
  "databaseURL":""
}

firebase = pyrebase.initialize_app(firebaseConfig)


@app.post("/signup")
async def create_an_account(user_data: MODELS.SignUpSchema):
    email = user_data.email
    password = user_data.password

    models.validate_user_data(user_data)
    models.confirm_password_validation(user_data)
    try:
        # salt = bcrypt.gensalt()
        # hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        # print(hashed_password)
        # user = auth.create_user(email=email, password=str(hashed_password))

        user = auth.create_user(email=email, password=password)
        return JSONResponse(content={
            "message": f"Account created successfully. User ID: {user.uid}"},
            status_code=status.HTTP_201_CREATED)

    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account already exists for email {email}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post('/login')
async def login(user_data:models.LoginSchema):
    email = user_data.email
    password = user_data.password

    models.validate_user_data(user_data)

    try:
        user = firebase.auth().sign_in_with_email_and_password(
            email = email,
            password = password
        )

        token = user['idToken']
        return JSONResponse(content={
            "token":token
        },status_code=status.HTTP_200_OK)

    except requests.exceptions.HTTPError as e:
        error_message = str(e)
        if "INVALID_LOGIN_CREDENTIALS" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def verify_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

#@app.get("/protected-route")
#async def protected_route(token: str = Depends(oauth2_scheme)):
    #user_data = verify_token(token)
    #return {"message": "Access granted to protected route", "user": user_data}

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True)
