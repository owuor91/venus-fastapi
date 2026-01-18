from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.match import Match
from app.schemas.match import MatchCreateRequest, Match as MatchSchema
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("", response_model=MatchSchema, status_code=status.HTTP_201_CREATED)
def create_or_update_match(
    match_data: MatchCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update a match.
    Requires authentication.
    Required fields: my_id, partner_id, thread_id
    Optional fields: last_message, last_message_date, sent_by
    
    Validates that my_id matches the authenticated user.
    If a match with the same (my_id, partner_id, thread_id) exists, it will be updated.
    """
    # Validate that my_id matches the authenticated user
    if match_data.my_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create matches for yourself"
        )
    
    # Check if match already exists
    existing_match = db.query(Match).filter(
        Match.my_id == match_data.my_id,
        Match.partner_id == match_data.partner_id,
        Match.thread_id == match_data.thread_id
    ).first()
    
    if existing_match:
        # Update existing match
        existing_match.last_message = match_data.last_message
        existing_match.last_message_date = match_data.last_message_date
        existing_match.sent_by = match_data.sent_by
        existing_match.updated_by = str(current_user.user_id)
        
        db.commit()
        db.refresh(existing_match)
        return existing_match
    else:
        # Create new match
        db_match = Match(
            my_id=match_data.my_id,
            partner_id=match_data.partner_id,
            thread_id=match_data.thread_id,
            last_message=match_data.last_message,
            last_message_date=match_data.last_message_date,
            sent_by=match_data.sent_by,
            created_by=str(current_user.user_id),
            updated_by=str(current_user.user_id),
        )
        db.add(db_match)
        db.commit()
        db.refresh(db_match)
        return db_match


@router.get("", response_model=List[MatchSchema])
def get_user_matches(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active matches for the authenticated user.
    Returns matches where the current user is either my_id or partner_id.
    Only returns active matches.
    """
    matches = db.query(Match).filter(
        ((Match.my_id == current_user.user_id) | (Match.partner_id == current_user.user_id)),
        Match.active == True
    ).all()
    
    return matches
