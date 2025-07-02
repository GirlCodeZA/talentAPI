from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    aws_access_key: str
    aws_secret_key: str
    aws_bucket_name: str
    aws_region: str

    sendgrid_api_key: str = Field(..., alias="SENDGRID_API_KEY")
    sender_email: str = Field("no-reply@girlcode.com", alias="SENDER_EMAIL")

    highwind_api_url: str = Field(..., alias="HIGHWIND_API_URL")
    highwind_api_key: str = Field(..., alias="HIGHWIND_API_KEY")

    class Config:
        env_file = ".env"
        extra = "forbid"
        populate_by_name = True
        alias_priority = 2

settings = Settings()
