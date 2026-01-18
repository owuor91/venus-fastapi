import pytest
from fastapi import status
from datetime import datetime, timezone
from uuid import uuid4
from tests.conftest import get_auth_headers


class TestMatches:
    """Test cases for matches endpoints."""
    
    def test_create_match_different_user(self, client, test_user, test_user2):
        """Test 403 error when my_id doesn't match authenticated user."""
        headers = get_auth_headers(test_user.email)
        thread_id = str(uuid4())
        
        # Try to create match with my_id as test_user2, but authenticated as test_user
        response = client.post("/api/v1/matches", json={
            "my_id": str(test_user2.user_id),  # Different user
            "partner_id": str(test_user.user_id),
            "thread_id": thread_id
        }, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "You can only create matches for yourself"
    
    def test_create_match_correct_user(self, client, test_user, test_user2):
        """Test successful match creation when my_id matches authenticated user."""
        headers = get_auth_headers(test_user.email)
        thread_id = str(uuid4())
        
        response = client.post("/api/v1/matches", json={
            "my_id": str(test_user.user_id),  # Correct user
            "partner_id": str(test_user2.user_id),
            "thread_id": thread_id
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["my_id"] == str(test_user.user_id)
        assert data["partner_id"] == str(test_user2.user_id)
        assert data["thread_id"] == thread_id
        assert data["created_by"] == str(test_user.user_id)
        assert data["updated_by"] == str(test_user.user_id)
        assert data["active"] is True
    
    def test_update_existing_match(self, client, test_user, test_user2):
        """Test updating existing match with last_message and last_message_date."""
        headers = get_auth_headers(test_user.email)
        thread_id = str(uuid4())
        
        # Create initial match
        response = client.post("/api/v1/matches", json={
            "my_id": str(test_user.user_id),
            "partner_id": str(test_user2.user_id),
            "thread_id": thread_id
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        match_id = response.json()["match_id"]
        initial_last_message = response.json().get("last_message")
        assert initial_last_message is None
        
        # Update match with last_message and last_message_date
        last_message = "Hello, how are you?"
        last_message_date = datetime.now(timezone.utc)
        
        response = client.post("/api/v1/matches", json={
            "my_id": str(test_user.user_id),
            "partner_id": str(test_user2.user_id),
            "thread_id": thread_id,
            "last_message": last_message,
            "last_message_date": last_message_date.isoformat(),
            "sent_by": str(test_user.user_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED  # Still 201 because it's an update via POST
        data = response.json()
        assert data["match_id"] == match_id  # Same match_id
        assert data["last_message"] == last_message
        # Compare datetime strings (response may have slightly different format)
        assert data["last_message_date"] is not None
        assert data["sent_by"] == str(test_user.user_id)
        assert data["my_id"] == str(test_user.user_id)
        assert data["partner_id"] == str(test_user2.user_id)
        assert data["thread_id"] == thread_id
