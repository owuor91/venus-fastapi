import pytest
from fastapi import status
from datetime import date
from tests.conftest import get_auth_headers


class TestProfileCompletion:
    """Test cases for profile completion endpoint."""
    
    def test_complete_profile_missing_required_params(self, client, test_user):
        """Test profile completion fails when required parameters are missing."""
        headers = get_auth_headers(test_user.email)
        
        # Test missing phone_number
        response = client.post("/api/v1/auth/profile/complete", json={
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "bio": "Test bio"
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing gender
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "bio": "Test bio"
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing date_of_birth
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "MALE",
            "bio": "Test bio"
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing bio
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "MALE",
            "date_of_birth": "1990-01-01"
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_complete_profile_all_params_present(self, client, test_user):
        """Test successful profile creation with all required parameters."""
        headers = get_auth_headers(test_user.email)
        
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "bio": "Test user bio"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["phone_number"] == "+1234567890"
        assert data["gender"] == "MALE"
        assert data["date_of_birth"] == "1990-01-01"
        assert data["bio"] == "Test user bio"
        assert data["user_id"] == str(test_user.user_id)
        assert data["online"] is True
        assert data["created_by"] == str(test_user.user_id)
        assert data["updated_by"] == str(test_user.user_id)
    
    def test_complete_profile_duplicate_phone_number(self, client, test_user, test_user2):
        """Test profile completion fails when phone number is already taken by another user."""
        headers = get_auth_headers(test_user.email)
        headers2 = get_auth_headers(test_user2.email)
        
        # Create profile for first user
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "bio": "Test user bio"
        }, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create profile for second user with same phone number
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "FEMALE",
            "date_of_birth": "1991-01-01",
            "bio": "Test user2 bio"
        }, headers=headers2)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Phone number already registered"
    
    def test_complete_profile_duplicate_user_id(self, client, test_user):
        """Test profile update when user already has a profile (should update, not create duplicate)."""
        headers = get_auth_headers(test_user.email)
        
        # Create initial profile
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+1234567890",
            "gender": "MALE",
            "date_of_birth": "1990-01-01",
            "bio": "Initial bio"
        }, headers=headers)
        assert response.status_code == status.HTTP_201_CREATED
        initial_profile_id = response.json()["profile_id"]
        
        # Update profile with new data
        response = client.post("/api/v1/auth/profile/complete", json={
            "phone_number": "+9876543210",
            "gender": "FEMALE",
            "date_of_birth": "1995-05-15",
            "bio": "Updated bio"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK  # Should return 200 for update
        data = response.json()
        assert data["profile_id"] == initial_profile_id  # Same profile_id
        assert data["phone_number"] == "+9876543210"  # Updated phone
        assert data["gender"] == "FEMALE"  # Updated gender
        assert data["date_of_birth"] == "1995-05-15"  # Updated date
        assert data["bio"] == "Updated bio"  # Updated bio
        assert data["user_id"] == str(test_user.user_id)  # Same user_id
