import pytest
from fastapi import status


class TestRegistration:
    """Test cases for user registration endpoint."""
    
    def test_register_missing_required_params(self, client):
        """Test registration fails when required parameters are missing."""
        # Test missing email
        response = client.post("/api/v1/auth/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing first_name
        response = client.post("/api/v1/auth/register", json={
            "email": "john@example.com",
            "last_name": "Doe",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing last_name
        response = client.post("/api/v1/auth/register", json={
            "email": "john@example.com",
            "first_name": "John",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing password
        response = client.post("/api/v1/auth/register", json={
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_all_params_present(self, client):
        """Test successful registration with all required parameters."""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "password123"
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert "user_id" in data
        assert "hashed_password" not in data  # Password should not be in response
        assert data["created_by"] == "newuser@example.com"
        assert data["updated_by"] == "newuser@example.com"


class TestLogin:
    """Test cases for login endpoint."""
    
    def test_login_correct_credentials(self, client, test_user):
        """Test successful login with correct credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == str(test_user.user_id)
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["profile"] is None  # No profile created yet
    
    def test_login_incorrect_credentials(self, client, test_user):
        """Test login fails with incorrect credentials."""
        # Test wrong password
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"
        
        # Test wrong email
        response = client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com",
            "password": "testpassword123"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"
