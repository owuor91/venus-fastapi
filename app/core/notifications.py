import json
import logging
import os
from typing import Dict, Optional
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.match import Match
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class Notifications:
    """Firebase Cloud Messaging notifications service."""

    def __init__(self):
        """Initialize Firebase Admin SDK if not already initialized."""
        try:
            firebase_admin.get_app()
        except ValueError:
            # Firebase app not initialized, initialize it
            if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
                if os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                    cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning(
                        f"Firebase service account file not found at: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}"
                    )
            else:
                logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH not configured, notifications will be disabled")

    def send_match_notification(self, match_message: Dict, fcm_token: str) -> None:
        """
        Send a match notification to a user.
        
        Args:
            match_message: Dictionary containing match notification data
            fcm_token: FCM token of the recipient user
        """
        if not fcm_token:
            logger.warning("FCM token is missing, skipping match notification")
            return

        try:
            message = messaging.Message(
                data=match_message,
                token=fcm_token,
                android=messaging.AndroidConfig(priority="high"),
            )
            messaging.send(message)
            logger.info(f"Match notification sent successfully to token: {fcm_token[:10]}...")
        except Exception as e:
            logger.error(f"Failed to send match notification: {str(e)}", exc_info=True)

    def send_chat_notification(self, match: Match, partner_fcm_token: str, sender: User, db: Session) -> None:
        """
        Send a chat notification when a new message is sent in a match.
        
        Args:
            match: Match SQLAlchemy object
            partner_fcm_token: FCM token of the partner (recipient)
            sender: User object of the sender
            db: Database session
        """
        if not partner_fcm_token:
            logger.warning("Partner FCM token is missing, skipping chat notification")
            return

        if match.sent_by is None:
            logger.warning("Match sent_by is None, skipping chat notification")
            return

        try:
            match_message = {}
            match_message["title"] = f"{sender.first_name} {sender.last_name}"
            match_message["avatar"] = sender.avatar_url or ""
            
            # Convert match object to dict for JSON serialization
            match_dict = {
                "match_id": str(match.match_id),
                "my_id": str(match.my_id),
                "partner_id": str(match.partner_id),
                "thread_id": str(match.thread_id),
                "last_message": match.last_message or "",
                "last_message_date": match.last_message_date.isoformat() if match.last_message_date else None,
                "sent_by": str(match.sent_by) if match.sent_by else None,
            }
            match_message["match"] = json.dumps(match_dict)

            message = messaging.Message(
                data=match_message,
                token=partner_fcm_token,
                android=messaging.AndroidConfig(priority="high"),
            )
            messaging.send(message)
            logger.info(f"Chat notification sent successfully to token: {partner_fcm_token[:10]}...")
        except Exception as e:
            logger.error(f"Failed to send chat notification: {str(e)}", exc_info=True)

    def send_payment_notification(self, payment: Payment, fcm_token: str) -> None:
        """
        Send a payment notification to a user.
        
        Args:
            payment: Payment SQLAlchemy model instance
            fcm_token: FCM token of the recipient user
        """
        if not fcm_token:
            logger.warning("FCM token is missing, skipping payment notification")
            return

        try:
            # Convert payment model to dict for FCM message
            payment_dict = {
                "payment_id": str(payment.payment_id),
                "user_id": str(payment.user_id),
                "amount": str(payment.amount),
                "payment_ref": payment.payment_ref or "",
                "transaction_status": payment.transaction_status or "",
                "plan_id": str(payment.plan_id),
            }
            
            payment_message = {
                "title": "Payment received",
                "type": "payment",
                "payment_data": json.dumps(payment_dict)
            }

            message = messaging.Message(
                data=payment_message,
                token=fcm_token,
                android=messaging.AndroidConfig(priority="high"),
            )
            messaging.send(message)
            logger.info(f"Payment notification sent successfully to token: {fcm_token[:10]}...")
        except Exception as e:
            logger.error(f"Failed to send payment notification: {str(e)}", exc_info=True)


# Global instance
notifications = Notifications()
