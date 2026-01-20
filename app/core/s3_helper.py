import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import UploadFile, HTTPException, status
from uuid import UUID
import os

from app.core.config import settings


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def get_s3_client():
    """Create and return an S3 client."""
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension and return lowercase extension.
    Raises HTTPException if extension is not allowed.
    """
    if not filename or '.' not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have an extension"
        )

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type not allowed. "
                f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        )

    return ext


def validate_file_size(file: UploadFile) -> None:
    """
    Validate file size.
    Raises HTTPException if file exceeds maximum size.
    """
    # Read file to check size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer

    max_size_bytes = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File size exceeds maximum allowed size of "
                f"{settings.MAX_PHOTO_SIZE_MB}MB"
            )
        )


def upload_photo_to_s3(file: UploadFile, user_id: UUID, photo_id: UUID) -> str:
    """
    Upload a photo file to S3 and return the public URL.

    Args:
        file: FastAPI UploadFile object
        user_id: UUID of the user uploading the photo
        photo_id: UUID of the photo record

    Returns:
        str: Public URL of the uploaded photo

    Raises:
        HTTPException: If file validation fails or S3 upload fails
    """
    # Validate file extension
    ext = validate_file_extension(file.filename)

    # Validate file size
    validate_file_size(file)

    # Generate S3 key
    s3_key = f"users/{user_id}/photos/{photo_id}.{ext}"

    try:
        # Create S3 client
        s3_client = get_s3_client()

        # Upload file to S3
        file.file.seek(0)  # Ensure we're at the beginning of the file
        s3_client.upload_fileobj(
            file.file,
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type or f'image/{ext}',
                'ACL': 'public-read'  # Make the object publicly readable
            }
        )

        # Generate public URL
        photo_url = (
            f"https://{settings.S3_BUCKET_NAME}.s3."
            f"{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        )

        return photo_url

    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo to S3: {str(e)}"
        )
    except BotoCoreError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AWS service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during photo upload: {str(e)}"
        )
