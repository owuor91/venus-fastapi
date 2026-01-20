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


class TestProfileLocation:
    """Test cases for profile location endpoint."""
    
    def test_update_location_missing_coordinates(self, client, test_user, db_session):
        """Test location update fails when coordinates are missing."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create a profile for test_user
        profile = Profile(
            user_id=test_user.user_id,
            phone_number="+1234567890",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        # Test missing coordinates
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id)
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_location_invalid_coordinates(self, client, test_user, db_session):
        """Test location update fails with invalid coordinates format."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create a profile for test_user
        profile = Profile(
            user_id=test_user.user_id,
            phone_number="+1234567890",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        # Test invalid format
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id),
            "coordinates": "invalid"
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid lat/lng values
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id),
            "coordinates": "91,181"  # Out of range
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_location_unauthorized(self, client, test_user, db_session):
        """Test location update fails without authentication."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        # Create a profile for test_user
        profile = Profile(
            user_id=test_user.user_id,
            phone_number="+1234567890",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id),
            "coordinates": "-1.2921,36.8219"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_location_different_user(self, client, test_user, test_user2, db_session):
        """Test location update fails when profile belongs to different user."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create a profile for test_user2
        profile = Profile(
            user_id=test_user2.user_id,
            phone_number="+9876543210",
            gender=GenderEnum.FEMALE.value,
            date_of_birth=date(1991, 1, 1),
            bio="Test bio 2",
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id),
            "coordinates": "-1.2921,36.8219"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "own profile" in response.json()["detail"].lower()
    
    def test_update_location_success(self, client, test_user, db_session):
        """Test successful location update."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create a profile for test_user
        profile = Profile(
            user_id=test_user.user_id,
            phone_number="+1234567890",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)
        
        response = client.post("/api/v1/profiles/location", json={
            "profile_id": str(profile.profile_id),
            "coordinates": "-1.2921,36.8219"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "location_updated"
        
        # Verify coordinates were saved
        db_session.refresh(profile)
        assert profile.current_coordinates == "-1.2921,36.8219"


class TestMapProfiles:
    """Test cases for map profiles endpoint."""
    
    def test_get_map_profiles_no_profile(self, client, test_user):
        """Test map endpoint returns empty list when user has no profile."""
        headers = get_auth_headers(test_user.email)
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["map_profiles"] == []
    
    def test_get_map_profiles_no_coordinates(self, client, test_user, db_session):
        """Test map endpoint returns empty list when profile has no coordinates."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create a profile without coordinates
        profile = Profile(
            user_id=test_user.user_id,
            phone_number="+1234567890",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["map_profiles"] == []
    
    def test_get_map_profiles_same_gender_excluded(self, client, test_user, test_user2, db_session):
        """Test that profiles of same gender are excluded."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create profile for test_user (MALE)
        profile1 = Profile(
            user_id=test_user.user_id,
            phone_number="+1111111111",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            current_coordinates="-1.2921,36.8219",
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile1)
        
        # Create profile for test_user2 (MALE - same gender)
        profile2 = Profile(
            user_id=test_user2.user_id,
            phone_number="+2222222222",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1991, 1, 1),
            bio="Test bio 2",
            current_coordinates="-1.2922,36.8220",
            online=True,
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile2)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        # Should return empty list since test_user2 has same gender
        assert len(response.json()["map_profiles"]) == 0
    
    def test_get_map_profiles_opposite_gender_included(self, client, test_user, test_user2, db_session):
        """Test that profiles of opposite gender and online are included."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create profile for test_user (MALE)
        profile1 = Profile(
            user_id=test_user.user_id,
            phone_number="+1111111111",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            current_coordinates="-1.2921,36.8219",
            preferences={"min_age": 18, "max_age": 99, "distance": 50.0},
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile1)
        
        # Create profile for test_user2 (FEMALE - opposite gender)
        profile2 = Profile(
            user_id=test_user2.user_id,
            phone_number="+2222222222",
            gender=GenderEnum.FEMALE.value,
            date_of_birth=date(1991, 1, 1),
            bio="Test bio 2",
            current_coordinates="-1.2922,36.8220",  # Close coordinates
            online=True,
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile2)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should include test_user2's profile
        assert len(data["map_profiles"]) >= 1
        assert any(p["user_id"] == str(test_user2.user_id) for p in data["map_profiles"])
    
    def test_get_map_profiles_offline_excluded(self, client, test_user, test_user2, db_session):
        """Test that offline profiles are excluded."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create profile for test_user (MALE)
        profile1 = Profile(
            user_id=test_user.user_id,
            phone_number="+1111111111",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            current_coordinates="-1.2921,36.8219",
            preferences={"min_age": 18, "max_age": 99, "distance": 50.0},
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile1)
        
        # Create profile for test_user2 (FEMALE but offline)
        profile2 = Profile(
            user_id=test_user2.user_id,
            phone_number="+2222222222",
            gender=GenderEnum.FEMALE.value,
            date_of_birth=date(1991, 1, 1),
            bio="Test bio 2",
            current_coordinates="-1.2922,36.8220",
            online=False,  # Offline
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile2)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should not include offline profile
        assert len(data["map_profiles"]) == 0
    
    def test_get_map_profiles_distance_filtering(self, client, test_user, test_user2, db_session):
        """Test that profiles outside distance range are filtered out."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create profile for test_user (MALE) with small distance preference
        profile1 = Profile(
            user_id=test_user.user_id,
            phone_number="+1111111111",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),
            bio="Test bio",
            current_coordinates="-1.2921,36.8219",  # Nairobi coordinates
            preferences={"min_age": 18, "max_age": 99, "distance": 1.0},  # 1 km radius
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile1)
        
        # Create profile for test_user2 (FEMALE) far away
        # Coordinates far from Nairobi (approximately 100+ km away)
        profile2 = Profile(
            user_id=test_user2.user_id,
            phone_number="+2222222222",
            gender=GenderEnum.FEMALE.value,
            date_of_birth=date(1991, 1, 1),
            bio="Test bio 2",
            current_coordinates="-0.0236,37.9062",  # Nyeri coordinates (far from Nairobi)
            online=True,
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile2)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should not include profile2 since it's outside the 1km radius
        assert len(data["map_profiles"]) == 0
    
    def test_get_map_profiles_age_filtering(self, client, test_user, test_user2, db_session):
        """Test that profiles outside age range are filtered out."""
        from app.models.profile import Profile
        from app.models.enums import GenderEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create profile for test_user (MALE) with age range 25-30
        profile1 = Profile(
            user_id=test_user.user_id,
            phone_number="+1111111111",
            gender=GenderEnum.MALE.value,
            date_of_birth=date(1990, 1, 1),  # Age ~34
            bio="Test bio",
            current_coordinates="-1.2921,36.8219",
            preferences={"min_age": 25, "max_age": 30, "distance": 50.0},
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(profile1)
        
        # Create profile for test_user2 (FEMALE) with age outside range
        # Use a date that makes them clearly outside the 25-30 range (e.g., age 20 or age 35)
        profile2 = Profile(
            user_id=test_user2.user_id,
            phone_number="+2222222222",
            gender=GenderEnum.FEMALE.value,
            date_of_birth=date(2006, 1, 1),  # Age ~20 (outside range 25-30)
            bio="Test bio 2",
            current_coordinates="-1.2922,36.8220",  # Close coordinates
            online=True,
            created_by=str(test_user2.user_id),
            updated_by=str(test_user2.user_id)
        )
        db_session.add(profile2)
        db_session.commit()
        
        response = client.get("/api/v1/profiles/map", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should not include profile2 since age (20) is outside range (25-30)
        assert len(data["map_profiles"]) == 0
