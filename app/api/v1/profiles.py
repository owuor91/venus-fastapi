from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.profile import ProfileLocationUpdate
from app.api.deps import get_current_active_user
from app.core.geo import string_to_coordinates_tuple

router = APIRouter()


@router.post("/location", status_code=status.HTTP_200_OK, responses={
    200:{"message": "location_updated"}
})
def update_profile_location(
    location_data: ProfileLocationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the current coordinates for a profile.
    Requires authentication.
    The profile must belong to the authenticated user.
    """
    # Find the profile
    profile = db.query(Profile).filter(
        Profile.profile_id == location_data.profile_id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Verify the profile belongs to the authenticated user
    if profile.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile location"
        )
    
    # Validate coordinates format
    coords_tuple = string_to_coordinates_tuple(location_data.coordinates)
    if coords_tuple is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid coordinates format. Expected format: 'lat,lng' (e.g. '-1.2921,36.8219')"
        )
    
    # Update coordinates
    profile.current_coordinates = location_data.coordinates
    profile.updated_by = str(current_user.user_id)
    
    db.commit()
    db.refresh(profile)
    
    return {"message": "location_updated"}


@router.get("/map", responses={
    200: {
        "description": "List of matching profiles",
        "content": {
            "application/json": {
                "example": {
                    "map_profiles": [
                        {
                            "user_id": "87aa19c3-3242-4bad-9f35-ed259aec1f9c",
                            "first_name": "Mary",
                            "last_name": "Rose",
                            "avatar_url": None,
                            "profile": {
                                "profile_id": "0aca183b-21d4-4c5e-88d2-07cadfe851e0",
                                "gender": "FEMALE",
                                "bio": "Passionate about art, music, and outdoor adventures. Always up for trying something new!",
                                "online": True,
                                "current_coordinates": "-1.2921,36.8219"
                            }
                        }
                    ]
                }
            }
        }
    }
})
def get_map_profiles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get nearby profiles for map view.
    Returns a list of profiles that match the authenticated user's preferences
    (gender, age range, distance). Requires JWT authentication.
    
    Filters profiles based on:
    - Opposite gender
    - Online status
    - Distance within user's preference radius
    - Age within user's preference range (min_age to max_age)
    
    Returns empty list if:
    - User has no profile
    - User's profile has no current_coordinates
    - No profiles match the criteria
    """
    # Get current user's profile
    profile = db.query(Profile).filter(
        Profile.user_id == current_user.user_id
    ).first()
    
    if not profile or not profile.current_coordinates:
        return {"map_profiles": []}
    
    # Get preferences with defaults
    preferences = profile.preferences or {
        "min_age": 18,
        "max_age": 99,
        "distance": 50.0  # 50 km default
    }
    
    # Query users with opposite gender and online
    map_profiles = (
        db.query(User)
        .join(Profile)
        .filter(
            Profile.gender != profile.gender,
            Profile.online == True,
            Profile.user_id != current_user.user_id,  # Exclude current user
            Profile.active == True,
            User.active == True
        )
        .options(joinedload(User.profile))
        .all()
    )
    
    # Filter by distance and age range
    from app.core.geo import filter_out_profiles_outside_range
    filtered_profiles = filter_out_profiles_outside_range(
        profile,
        map_profiles,
        preferences
    )
    
    # Build response
    map_profiles_data = []
    for user in filtered_profiles:
        user_data = {
            "user_id": str(user.user_id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": user.avatar_url,
            "profile": {
                "profile_id": str(user.profile.profile_id) if user.profile else None,
                "gender": user.profile.gender if user.profile else None,
                "bio": user.profile.bio if user.profile else None,
                "online": user.profile.online if user.profile else None,
                "current_coordinates": user.profile.current_coordinates if user.profile else None,
            } if user.profile else None
        }
        map_profiles_data.append(user_data)
    
    return {"map_profiles": map_profiles_data}
