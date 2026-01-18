from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.user import RegisterRequest, LoginRequest, User as UserSchema
from app.schemas.profile import ProfileCompletionRequest, Profile as ProfileSchema
from app.schemas.token import LoginResponse
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.config import settings
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    Requires: email, first_name, last_name, password
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        created_by=user_data.email,  # Set to user's email for first registration
        updated_by=user_data.email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login and get access token.
    Requires: email and password
    Returns: token, user details (user_id, first_name, last_name, email), and profile (null if not present)
    """
    # Eagerly load the profile relationship
    user = db.query(User).options(joinedload(User.profile)).filter(User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    # Build response with user data and optional profile
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "profile": user.profile if user.profile else None
    }
    
    return response_data


@router.post("/profile/complete", response_model=ProfileSchema, status_code=status.HTTP_201_CREATED)
def complete_profile(
    profile_data: ProfileCompletionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Complete or update user profile.
    Requires authentication.
    Requires: phone_number, gender, date_of_birth, bio
    """
    # Check if phone number is already taken by another user
    existing_profile_with_phone = db.query(Profile).filter(
        Profile.phone_number == profile_data.phone_number,
        Profile.user_id != current_user.user_id
    ).first()
    
    if existing_profile_with_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Check if profile already exists for this user
    existing_profile = db.query(Profile).filter(Profile.user_id == current_user.user_id).first()
    
    if existing_profile:
        # Update existing profile
        existing_profile.phone_number = profile_data.phone_number
        existing_profile.gender = profile_data.gender.value  # Store enum value as string
        existing_profile.date_of_birth = profile_data.date_of_birth
        existing_profile.bio = profile_data.bio
        existing_profile.updated_by = str(current_user.user_id)  # Use user_id for authenticated requests
        
        db.commit()
        db.refresh(existing_profile)
        return existing_profile
    else:
        # Create new profile
        db_profile = Profile(
            user_id=current_user.user_id,
            phone_number=profile_data.phone_number,
            gender=profile_data.gender.value,  # Store enum value as string
            date_of_birth=profile_data.date_of_birth,
            bio=profile_data.bio,
            created_by=str(current_user.user_id),  # Use user_id for authenticated requests
            updated_by=str(current_user.user_id),  # Use user_id for authenticated requests
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
