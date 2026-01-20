import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import SessionLocal, get_db
from app.models.user import User
from app.models.match import Match
from app.schemas.match import MatchCreateRequest, Match as MatchSchema
from app.api.deps import get_current_active_user
from app.core.notifications import notifications

logger = logging.getLogger(__name__)

router = APIRouter()


def _send_match_notification(match_id: UUID, partner_id: UUID) -> None:
    """
    Helper function to send match notification to partner.
    Runs in background task. Creates its own database session.
    """
    db = SessionLocal()
    try:
        # Get match
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            return

        # Get partner user
        partner = db.query(User).filter(User.user_id == partner_id).first()

        if not partner:
            return

        if not partner.fcm_token:
            return

        # Convert match to dict for notification
        match_dict = {
            "match_id": str(match.match_id),
            "my_id": str(match.my_id),
            "partner_id": str(match.partner_id),
            "thread_id": str(match.thread_id),
            "last_message": match.last_message or "",
            "last_message_date": (
                match.last_message_date.isoformat()
                if match.last_message_date else None
            ),
            "sent_by": str(match.sent_by) if match.sent_by else None,
        }

        # Send notification
        notifications.send_match_notification(match_dict, partner.fcm_token)
    except Exception as e:
        # Log error but don't fail - notification is non-critical
        logger.error(
            f"Error sending match notification: {str(e)}",
            exc_info=True
        )
    finally:
        db.close()


def _send_chat_notification(
    match_id: UUID,
    partner_id: UUID,
    sender_id: UUID
) -> None:
    """
    Helper function to send chat notification to partner.
    Runs in background task. Creates its own database session.
    """
    db = SessionLocal()
    try:
        # Get match
        match = db.query(Match).filter(Match.match_id == match_id).first()
        if not match:
            return

        # Get partner user
        partner = db.query(User).filter(User.user_id == partner_id).first()

        if not partner or not partner.fcm_token:
            return

        # Get sender user
        sender = db.query(User).filter(User.user_id == sender_id).first()

        if not sender:
            return

        # Send notification
        notifications.send_chat_notification(
            match,
            partner.fcm_token,
            sender,
            db
        )
    except Exception as e:
        # Log error but don't fail - notification is non-critical
        logger.error(
            f"Error sending chat notification: {str(e)}",
            exc_info=True
        )
    finally:
        db.close()


@router.post(
    "",
    response_model=MatchSchema,
    status_code=status.HTTP_201_CREATED
)
def create_or_update_match(
    match_data: MatchCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create or update a match.
    Requires authentication.
    Required fields: my_id, partner_id, thread_id
    Optional fields: last_message, last_message_date, sent_by

    Validates that my_id matches the authenticated user.
    If a match with the same (my_id, partner_id, thread_id) exists,
    it will be updated.
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

        # Send chat notification if there's a new message
        if match_data.last_message and match_data.sent_by:
            # Determine partner (the one who didn't send the message)
            partner_id = (
                match_data.partner_id
                if match_data.sent_by == match_data.my_id
                else match_data.my_id
            )

            # Send notification in background
            background_tasks.add_task(
                _send_chat_notification,
                existing_match.match_id,
                partner_id,
                match_data.sent_by
            )

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

        # Send match notification to partner in background
        background_tasks.add_task(
            _send_match_notification,
            db_match.match_id,
            db_match.partner_id
        )

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
        (
            (Match.my_id == current_user.user_id) |
            (Match.partner_id == current_user.user_id)
        ),
        Match.active.is_(True)
    ).all()

    return matches
