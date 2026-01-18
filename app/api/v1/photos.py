import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.photo import Photo
from app.schemas.photo import Photo as PhotoSchema
from app.api.deps import get_current_active_user
from app.core.s3_helper import upload_photo_to_s3

router = APIRouter()


@router.post("", response_model=PhotoSchema, status_code=status.HTTP_201_CREATED)
def upload_photo(
    image: UploadFile = File(..., alias="image"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a photo to S3 and create a photo record.
    Requires authentication.
    Accepts multipart form data with field name "image".
    Accepts file types: png, jpg, jpeg, gif
    Maximum file size: 10MB (configurable)
    """
    # Generate photo_id
    photo_id = uuid.uuid4()
    
    # Upload to S3
    try:
        photo_url = upload_photo_to_s3(image, current_user.user_id, photo_id)
    except HTTPException:
        raise  # Re-raise HTTP exceptions from s3_helper
    
    # Create photo record in database
    db_photo = Photo(
        photo_id=photo_id,
        user_id=current_user.user_id,
        photo_url=photo_url,
        verified=False,
        created_by=str(current_user.user_id),
        updated_by=str(current_user.user_id),
    )
    
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    return db_photo
