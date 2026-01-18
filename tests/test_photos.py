import pytest
from fastapi import status
from io import BytesIO
from tests.conftest import get_auth_headers


class TestPhotoUpload:
    """Test cases for photo upload endpoint."""
    
    def test_upload_photo_invalid_file_type(self, client, test_user):
        """Test photo upload fails with invalid file type."""
        headers = get_auth_headers(test_user.email)
        
        # Create a fake file with invalid extension
        fake_file = BytesIO(b"fake pdf content")
        fake_file.name = "document.pdf"
        
        response = client.post(
            "/api/v1/photos",
            files={"image": ("document.pdf", fake_file, "application/pdf")},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "File type not allowed" in response.json()["detail"]
    
    def test_upload_photo_valid_file(self, client, test_user, monkeypatch):
        """Test successful photo upload with valid file."""
        headers = get_auth_headers(test_user.email)
        
        # Mock S3 upload to avoid actual AWS calls
        def mock_upload_fileobj(*args, **kwargs):
            pass
        
        def mock_get_s3_client():
            class MockS3Client:
                def upload_fileobj(self, *args, **kwargs):
                    pass
            return MockS3Client()
        
        # Mock the S3 client and upload
        from app.core import s3_helper
        monkeypatch.setattr(s3_helper, "get_s3_client", mock_get_s3_client)
        
        # Create a fake image file
        fake_image = BytesIO(b"fake image content")
        fake_image.name = "photo.jpg"
        
        # Mock the upload_photo_to_s3 to return a fake URL
        def mock_upload_photo_to_s3(file, user_id, photo_id):
            return f"https://test-bucket.s3.us-east-1.amazonaws.com/users/{user_id}/photos/{photo_id}.jpg"
        
        monkeypatch.setattr(s3_helper, "upload_photo_to_s3", mock_upload_photo_to_s3)
        
        response = client.post(
            "/api/v1/photos",
            files={"image": ("photo.jpg", fake_image, "image/jpeg")},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "photo_id" in data
        assert data["user_id"] == str(test_user.user_id)
        assert "photo_url" in data
        assert data["verified"] is False
        assert data["created_by"] == str(test_user.user_id)
        assert data["updated_by"] == str(test_user.user_id)
    
    def test_upload_photo_without_authentication(self, client):
        """Test photo upload fails without authentication."""
        fake_image = BytesIO(b"fake image content")
        fake_image.name = "photo.jpg"
        
        response = client.post(
            "/api/v1/photos",
            files={"image": ("photo.jpg", fake_image, "image/jpeg")}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_upload_photo_allowed_extensions(self, client, test_user, monkeypatch):
        """Test photo upload accepts all allowed file extensions."""
        headers = get_auth_headers(test_user.email)
        
        # Mock the upload function
        def mock_upload_photo_to_s3(file, user_id, photo_id):
            return f"https://test-bucket.s3.us-east-1.amazonaws.com/users/{user_id}/photos/{photo_id}.ext"
        
        from app.core import s3_helper
        monkeypatch.setattr(s3_helper, "upload_photo_to_s3", mock_upload_photo_to_s3)
        
        # Test each allowed extension
        allowed_extensions = ["png", "jpg", "jpeg", "gif"]
        
        for ext in allowed_extensions:
            fake_image = BytesIO(b"fake image content")
            fake_image.name = f"photo.{ext}"
            
            response = client.post(
                "/api/v1/photos",
                files={"image": (f"photo.{ext}", fake_image, f"image/{ext}")},
                headers=headers
            )
            
            assert response.status_code == status.HTTP_201_CREATED, f"Failed for extension: {ext}"
            data = response.json()
            assert "photo_id" in data
            assert data["user_id"] == str(test_user.user_id)
