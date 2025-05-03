import uuid
from typing import Optional
import boto3
from botocore.config import Config
from app.settings import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key,
    aws_secret_access_key=settings.aws_secret_key,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"})
)

def upload_file_to_s3(file, folder: Optional[str] = "") -> str:
    file_extension = file.filename.split(".")[-1]
    file_key = f"{folder}/{uuid.uuid4()}.{file_extension}" if folder else f"{uuid.uuid4()}.{file_extension}"

    s3_client.upload_fileobj(Fileobj=file.file, Bucket=settings.aws_bucket_name, Key=file_key)

    file_url = f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{file_key}"
    return file_url

def generate_signed_url(key: str, expiration: int = 604800):
    print(f"Generating signed URL for key: {key}")
    return s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.aws_bucket_name, "Key": key},
        ExpiresIn=expiration
    )

