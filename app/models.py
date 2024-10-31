from pydantic import BaseModel

class SignUpSchema(BaseModel):
    password: str
    email: str

    class Config:
        schema_extra = {
            "example": {
                "password": "password",
                "email": "test@gmail.com"
            }
        }

class LoginSchema(BaseModel):
    email: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "password": "password",
                "email": "test@gmail.com"
            }
        }