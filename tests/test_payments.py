import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from uuid import uuid4
from tests.conftest import get_auth_headers


class TestCreatePayment:
    """Test cases for creating payments."""
    
    def test_create_payment_missing_params(self, client, test_user, test_payment_plan):
        """Test validation for missing amount, plan_id."""
        headers = get_auth_headers(test_user.email)
        
        # Test missing amount
        response = client.post("/api/v1/payments", json={
            "plan_id": str(test_payment_plan.plan_id)
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test missing plan_id
        response = client.post("/api/v1/payments", json={
            "amount": 100.0
        }, headers=headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_payment_invalid_plan_id(self, client, test_user):
        """Test 400 when plan_id doesn't exist."""
        headers = get_auth_headers(test_user.email)
        fake_plan_id = str(uuid4())
        
        response = client.post("/api/v1/payments", json={
            "amount": 100.0,
            "plan_id": fake_plan_id
        }, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid plan_id" in response.json()["detail"]
    
    def test_create_payment_inactive_plan(self, client, test_user, db_session):
        """Test 400 when plan is inactive."""
        from app.models.payment_plan import PaymentPlan
        from app.models.enums import PlanEnum
        
        headers = get_auth_headers(test_user.email)
        
        # Create an inactive plan
        inactive_plan = PaymentPlan(
            plan=PlanEnum.TEST,
            amount=50.0,
            months=1,
            active=False,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(inactive_plan)
        db_session.commit()
        db_session.refresh(inactive_plan)
        
        response = client.post("/api/v1/payments", json={
            "amount": 50.0,
            "plan_id": str(inactive_plan.plan_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid plan_id" in response.json()["detail"]
    
    def test_create_payment_unauthorized(self, client, test_payment_plan):
        """Test 401 without authentication."""
        response = client.post("/api/v1/payments", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id)
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_payment_success(self, client, test_user, test_payment_plan):
        """Test successful creation with auto-calculated dates."""
        headers = get_auth_headers(test_user.email)
        
        response = client.post("/api/v1/payments", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(test_user.user_id)
        assert data["amount"] == 100.0
        assert data["plan_id"] == str(test_payment_plan.plan_id)
        assert data["created_by"] == str(test_user.user_id)
        assert data["updated_by"] == str(test_user.user_id)
        assert data["active"] is True
        assert "payment_date" in data
        assert "valid_until" in data
    
    def test_create_payment_auto_dates(self, client, test_user, test_payment_plan):
        """Verify payment_date and valid_until are calculated correctly based on plan.months."""
        headers = get_auth_headers(test_user.email)
        
        response = client.post("/api/v1/payments", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Parse dates - handle both Z and +00:00 formats
        payment_date_str = data["payment_date"].replace('Z', '+00:00')
        valid_until_str = data["valid_until"].replace('Z', '+00:00')
        payment_date = datetime.fromisoformat(payment_date_str)
        valid_until = datetime.fromisoformat(valid_until_str)
        
        # Ensure timezone-aware
        if payment_date.tzinfo is None:
            payment_date = payment_date.replace(tzinfo=timezone.utc)
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        
        # Verify payment_date is recent (within last minute)
        now = datetime.now(timezone.utc)
        assert abs((now - payment_date).total_seconds()) < 60
        
        # Verify valid_until is payment_date + plan.months
        expected_valid_until = payment_date + relativedelta(months=test_payment_plan.months)
        assert abs((valid_until - expected_valid_until).total_seconds()) < 60


class TestGetUserPayments:
    """Test cases for getting user payments."""
    
    def test_get_user_payments_unauthorized(self, client):
        """Test 401 without authentication."""
        response = client.get("/api/v1/payments")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_user_payments_success(self, client, test_user, test_payment):
        """Test returns only authenticated user's payments."""
        headers = get_auth_headers(test_user.email)
        
        response = client.get("/api/v1/payments", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # All payments should belong to test_user
        for payment in data:
            assert payment["user_id"] == str(test_user.user_id)
    
    def test_get_user_payments_only_active(self, client, test_user, test_payment, db_session):
        """Test that inactive payments are filtered out."""
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        headers = get_auth_headers(test_user.email)
        
        # Create an inactive payment
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=1)
        inactive_payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=50.0,
            plan_id=test_payment.plan_id,
            active=False,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id)
        )
        db_session.add(inactive_payment)
        db_session.commit()
        
        response = client.get("/api/v1/payments", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned payments should be active
        for payment in data:
            assert payment["active"] is True
    
    def test_get_user_payments_empty(self, client, test_user2):
        """Test empty list when user has no payments."""
        headers = get_auth_headers(test_user2.email)
        
        response = client.get("/api/v1/payments", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


class TestGetSinglePayment:
    """Test cases for getting a single payment."""
    
    def test_get_payment_not_found(self, client, test_user):
        """Test 404 when payment doesn't exist."""
        headers = get_auth_headers(test_user.email)
        fake_payment_id = str(uuid4())
        
        response = client.get(f"/api/v1/payments/{fake_payment_id}", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_payment_different_user(self, client, test_user, test_user2, test_payment):
        """Test 404 when payment belongs to different user."""
        headers = get_auth_headers(test_user2.email)
        
        response = client.get(f"/api/v1/payments/{test_payment.payment_id}", headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_payment_success(self, client, test_user, test_payment):
        """Test successful retrieval of own payment."""
        headers = get_auth_headers(test_user.email)
        
        response = client.get(f"/api/v1/payments/{test_payment.payment_id}", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["payment_id"] == str(test_payment.payment_id)
        assert data["user_id"] == str(test_user.user_id)


class TestUpdatePayment:
    """Test cases for updating payments."""
    
    def test_update_payment_not_found(self, client, test_user):
        """Test 404 when payment doesn't exist."""
        headers = get_auth_headers(test_user.email)
        fake_payment_id = str(uuid4())
        
        response = client.patch(f"/api/v1/payments/{fake_payment_id}", json={
            "transaction_status": "SUCCESSFUL",
            "updated_by": str(test_user.user_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_payment_different_user(self, client, test_user2, test_payment):
        """Test 404 when updating another user's payment."""
        headers = get_auth_headers(test_user2.email)
        
        response = client.patch(f"/api/v1/payments/{test_payment.payment_id}", json={
            "transaction_status": "SUCCESSFUL",
            "updated_by": str(test_user2.user_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_payment_status_success(self, client, test_user, test_payment):
        """Test successful status update."""
        headers = get_auth_headers(test_user.email)
        
        response = client.patch(f"/api/v1/payments/{test_payment.payment_id}", json={
            "transaction_status": "SUCCESSFUL",
            "updated_by": str(test_user.user_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["transaction_status"] == "SUCCESSFUL"
        assert data["payment_id"] == str(test_payment.payment_id)
    
    def test_update_payment_multiple_fields(self, client, test_user, test_payment):
        """Test updating multiple fields at once."""
        headers = get_auth_headers(test_user.email)
        
        response = client.patch(f"/api/v1/payments/{test_payment.payment_id}", json={
            "transaction_status": "SUCCESSFUL",
            "payment_ref": "MPESA123456",
            "mpesa_transaction_id": "checkout_req_123",
            "updated_by": str(test_user.user_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["transaction_status"] == "SUCCESSFUL"
        assert data["payment_ref"] == "MPESA123456"
        assert data["mpesa_transaction_id"] == "checkout_req_123"


class TestInitiateSTK:
    """Test cases for STK push initiation."""
    
    def test_initiate_stk_missing_phone_number(self, client, test_user, test_payment_plan):
        """Test 400 when phone_number is missing."""
        headers = get_auth_headers(test_user.email)
        
        response = client.post("/api/v1/payments/initiate-stk", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id)
        }, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "phone_number" in response.json()["detail"].lower()
    
    def test_initiate_stk_invalid_plan(self, client, test_user):
        """Test 400 when plan_id is invalid."""
        headers = get_auth_headers(test_user.email)
        fake_plan_id = str(uuid4())
        
        response = client.post("/api/v1/payments/initiate-stk", json={
            "amount": 100.0,
            "plan_id": fake_plan_id,
            "phone_number": "254712345678"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid plan_id" in response.json()["detail"]
    
    def test_initiate_stk_unauthorized(self, client, test_payment_plan):
        """Test 401 without authentication."""
        response = client.post("/api/v1/payments/initiate-stk", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id),
            "phone_number": "254712345678"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.api.v1.payments.initiate_stk_push')
    def test_initiate_stk_success(self, mock_stk_push, client, test_user, test_payment_plan):
        """Test successful STK push initiation (with mocked Daraja)."""
        headers = get_auth_headers(test_user.email)
        
        # Mock successful STK push response
        mock_stk_push.return_value = ({
            "ResponseCode": "0",
            "CheckoutRequestID": "test_checkout_123",
            "ResponseDescription": "Success"
        }, 200)
        
        response = client.post("/api/v1/payments/initiate-stk", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id),
            "phone_number": "254712345678"
        }, headers=headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(test_user.user_id)
        assert data["amount"] == 100.0
        assert data["plan_id"] == str(test_payment_plan.plan_id)
        # Verify STK push was called
        mock_stk_push.assert_called_once()
    
    @patch('app.api.v1.payments.initiate_stk_push')
    def test_initiate_stk_daraja_failure(self, mock_stk_push, client, test_user, test_payment_plan):
        """Test that payment is still created even if Daraja call fails."""
        headers = get_auth_headers(test_user.email)
        
        # Mock failed STK push response
        mock_stk_push.return_value = ({
            "errorCode": "500.001.1001",
            "errorMessage": "Wrong credentials"
        }, 500)
        
        response = client.post("/api/v1/payments/initiate-stk", json={
            "amount": 100.0,
            "plan_id": str(test_payment_plan.plan_id),
            "phone_number": "254712345678"
        }, headers=headers)
        
        # Payment should still be created even if STK push fails
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(test_user.user_id)
        assert data["amount"] == 100.0
        # Verify STK push was attempted
        mock_stk_push.assert_called_once()
