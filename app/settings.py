from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_access_key: str
    aws_secret_key: str
    aws_bucket_name: str
    aws_region: str

    class Config:
        env_file = ".env"

settings = Settings()
