from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    aws_access_key: str
    aws_secret_key: str
    aws_bucket_name: str
    aws_region: str

    sendgrid_api_key: str = Field(..., alias="SENDGRID_API_KEY")  # <- add this
    sender_email: str = Field("no-reply@girlcode.com", alias="SENDER_EMAIL")  # optional, defaults

    class Config:
        env_file = ".env"
        extra = "forbid"  # optional, already default in v2 but makes intent clear

settings = Settings()
