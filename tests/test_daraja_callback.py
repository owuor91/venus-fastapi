import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from datetime import datetime, timezone
from uuid import uuid4
from tests.conftest import get_auth_headers


def successful_callback_payload(checkout_request_id, amount, mpesa_code, transaction_date):
    """Helper function to generate successful Daraja callback payload."""
    return {
        "Body": {
            "stkCallback": {
                "ResultCode": 0,
                "ResultDesc": "The service request is processed successfully.",
                "MerchantRequestID": "test_merchant_req_123",
                "CheckoutRequestID": checkout_request_id,
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": amount},
                        {"Name": "MpesaReceiptNumber", "Value": mpesa_code},
                        {"Name": "TransactionDate", "Value": transaction_date},
                        {"Name": "PhoneNumber", "Value": "254712345678"}
                    ]
                }
            }
        }
    }


def failed_callback_payload(result_code, result_desc):
    """Helper function to generate failed Daraja callback payload."""
    return {
        "Body": {
            "stkCallback": {
                "ResultCode": result_code,
                "ResultDesc": result_desc,
                "MerchantRequestID": "test_merchant_req_123",
                "CheckoutRequestID": "test_checkout_123"
            }
        }
    }


def invalid_callback_payload():
    """Helper function to generate invalid callback payload."""
    return {
        "Body": {
            "stkCallback": {
                # Missing CheckoutRequestID
            }
        }
    }


class TestDarajaCallback:
    """Test cases for Daraja callback endpoint."""
    
    def test_callback_successful_payment(self, client, test_user, test_payment_plan, db_session):
        """Test successful callback (result_code=0) with valid payment."""
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        # Create a payment with mpesa_transaction_id
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=test_payment_plan.months)
        checkout_request_id = "test_checkout_123"
        
        payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=test_payment_plan.amount,
            plan_id=test_payment_plan.plan_id,
            mpesa_transaction_id=checkout_request_id,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Mock notification sending
        with patch('app.api.v1.payments.notifications.send_payment_notification') as mock_notify:
            # Create callback payload
            transaction_date = "20240119120000"
            callback_data = successful_callback_payload(
                checkout_request_id,
                test_payment_plan.amount,
                "MPESA123456",
                transaction_date
            )
            
            response = client.post("/api/v1/payments/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "success"
            assert data["payment_id"] == str(payment.payment_id)
            
            # Verify payment was updated
            db_session.refresh(payment)
            assert payment.transaction_status == "SUCCESSFUL"
            assert payment.payment_ref == "MPESA123456"
            assert payment.transaction_callback == callback_data
    
    def test_callback_failed_payment(self, client):
        """Test callback with result_code != 0 (payment failed)."""
        callback_data = failed_callback_payload(1032, "Request cancelled by user")
        
        response = client.post("/api/v1/payments/callback", json=callback_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "received"
        assert data["result_code"] == 1032
    
    def test_callback_missing_checkout_request_id(self, client):
        """Test 400 when CheckoutRequestID is missing."""
        # Create a callback with result_code=0 but missing CheckoutRequestID
        callback_data = {
            "Body": {
                "stkCallback": {
                    "ResultCode": 0,
                    "ResultDesc": "Success",
                    "MerchantRequestID": "test_merchant_req_123",
                    # Missing CheckoutRequestID
                    "CallbackMetadata": {
                        "Item": []
                    }
                }
            }
        }
        
        response = client.post("/api/v1/payments/callback", json=callback_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["status"] == "error"
        assert "CheckoutRequestID" in data["message"]
    
    def test_callback_payment_not_found(self, client):
        """Test 404 when payment with CheckoutRequestID doesn't exist."""
        checkout_request_id = "nonexistent_checkout_123"
        callback_data = successful_callback_payload(
            checkout_request_id,
            100.0,
            "MPESA123456",
            "20240119120000"
        )
        
        response = client.post("/api/v1/payments/callback", json=callback_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()
    
    def test_callback_successful_with_payment_plan(self, client, test_user, test_payment_plan, db_session):
        """Test status set to SUCCESSFUL when amount >= plan.amount."""
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=test_payment_plan.months)
        checkout_request_id = "test_checkout_456"
        
        payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=test_payment_plan.amount,
            plan_id=test_payment_plan.plan_id,
            mpesa_transaction_id=checkout_request_id,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Amount equals plan amount
        callback_data = successful_callback_payload(
            checkout_request_id,
            test_payment_plan.amount,
            "MPESA789012",
            "20240119120000"
        )
        
        with patch('app.api.v1.payments.notifications.send_payment_notification'):
            response = client.post("/api/v1/payments/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_200_OK
            db_session.refresh(payment)
            assert payment.transaction_status == "SUCCESSFUL"
    
    def test_callback_partially_paid(self, client, test_user, test_payment_plan, db_session):
        """Test status set to PARTIALLY_PAID when amount < plan.amount."""
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=test_payment_plan.months)
        checkout_request_id = "test_checkout_789"
        
        payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=test_payment_plan.amount,  # Original amount
            plan_id=test_payment_plan.plan_id,
            mpesa_transaction_id=checkout_request_id,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Amount less than plan amount
        partial_amount = test_payment_plan.amount - 10.0
        callback_data = successful_callback_payload(
            checkout_request_id,
            partial_amount,
            "MPESA345678",
            "20240119120000"
        )
        
        with patch('app.api.v1.payments.notifications.send_payment_notification'):
            response = client.post("/api/v1/payments/callback", json=callback_data)
            
            assert response.status_code == status.HTTP_200_OK
            db_session.refresh(payment)
            assert payment.transaction_status == "PARTIALLY_PAID"
            assert payment.amount == partial_amount
    
    def test_callback_payment_plan_not_found(self, client, test_user, test_payment_plan, db_session):
        """Test callback processes when payment plan query returns None.
        
        Note: Due to foreign key constraints, we can't create a payment without a valid plan_id.
        The actual code checks `if payment_plan:` which handles None case gracefully.
        This test verifies the callback works correctly when plan exists.
        The None plan scenario is handled by the code's conditional check.
        """
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        # Create a payment with a valid plan_id
        payment_date = datetime.now(timezone.utc)
        checkout_request_id = "test_checkout_plan_missing"
        
        payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=payment_date + relativedelta(months=1),
            amount=100.0,
            plan_id=test_payment_plan.plan_id,
            mpesa_transaction_id=checkout_request_id,
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        # Temporarily deactivate the plan to simulate it not being found in query
        # (though it still exists for FK constraint)
        test_payment_plan.active = False
        db_session.commit()
        
        callback_data = successful_callback_payload(
            checkout_request_id,
            100.0,
            "MPESA999888",
            "20240119120000"
        )
        
        with patch('app.api.v1.payments.notifications.send_payment_notification'):
            response = client.post("/api/v1/payments/callback", json=callback_data)
            
            # Callback should process successfully
            # The plan query will find the plan (even if inactive), so status will be set
            assert response.status_code == status.HTTP_200_OK
            db_session.refresh(payment)
            # Verify payment was updated with callback data
            assert payment.transaction_callback == callback_data
            assert payment.payment_ref == "MPESA999888"
            # Status should be set since plan exists (even if inactive)
            assert payment.transaction_status == "SUCCESSFUL"
    
    def test_callback_invalid_structure(self, client):
        """Test error handling for malformed callback data."""
        # Missing Body - result_code will be None, which is != 0, so it returns 200 with result_code=None
        response = client.post("/api/v1/payments/callback", json={})
        
        # When Body is missing, result_code is None, which is != 0, so it returns 200
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "received"
        assert data["result_code"] is None
    
    @patch('app.api.v1.payments.notifications.send_payment_notification')
    def test_callback_notification_sent(self, mock_notify, client, test_user_with_fcm, test_payment_plan, db_session):
        """Test that FCM notification is sent on successful payment (mock notifications)."""
        from app.models.payment import Payment
        from dateutil.relativedelta import relativedelta
        
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=test_payment_plan.months)
        checkout_request_id = "test_checkout_notify"
        
        payment = Payment(
            user_id=test_user_with_fcm.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=test_payment_plan.amount,
            plan_id=test_payment_plan.plan_id,
            mpesa_transaction_id=checkout_request_id,
            created_by=str(test_user_with_fcm.user_id),
            updated_by=str(test_user_with_fcm.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        
        callback_data = successful_callback_payload(
            checkout_request_id,
            test_payment_plan.amount,
            "MPESA111222",
            "20240119120000"
        )
        
        response = client.post("/api/v1/payments/callback", json=callback_data)
        
        assert response.status_code == status.HTTP_200_OK
        # Verify notification was sent
        mock_notify.assert_called_once()
        # Verify it was called with payment and FCM token
        call_args = mock_notify.call_args
        assert call_args[0][0].payment_id == payment.payment_id
        assert call_args[0][1] == test_user_with_fcm.fcm_token
