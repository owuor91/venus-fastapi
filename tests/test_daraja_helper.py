import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timezone
from app.core.daraja_helper import (
    get_access_token,
    initiate_stk_push,
    daraja_timestamp_to_datetime
)
from app.models.payment import Payment
from app.models.payment_plan import PaymentPlan
from app.models.enums import PlanEnum
from app.core.config import settings


class TestGetAccessToken:
    """Test cases for get_access_token function."""
    
    @patch('app.core.daraja_helper.requests.get')
    def test_get_access_token_success(self, mock_get):
        """Mock successful token retrieval."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token_12345"}
        mock_get.return_value = mock_response
        
        # Temporarily set credentials
        original_key = settings.CONSUMER_KEY
        original_secret = settings.CONSUMER_SECRET
        original_url = settings.DARAJA_CREDENTIALS_URL
        
        settings.CONSUMER_KEY = "test_key"
        settings.CONSUMER_SECRET = "test_secret"
        settings.DARAJA_CREDENTIALS_URL = "https://test.url"
        
        try:
            token = get_access_token()
            assert token == "test_token_12345"
            mock_get.assert_called_once()
        finally:
            # Restore original values
            settings.CONSUMER_KEY = original_key
            settings.CONSUMER_SECRET = original_secret
            settings.DARAJA_CREDENTIALS_URL = original_url
    
    def test_get_access_token_missing_credentials(self):
        """Test None when credentials not set."""
        original_key = settings.CONSUMER_KEY
        original_secret = settings.CONSUMER_SECRET
        
        settings.CONSUMER_KEY = ""
        settings.CONSUMER_SECRET = ""
        
        try:
            token = get_access_token()
            assert token is None
        finally:
            settings.CONSUMER_KEY = original_key
            settings.CONSUMER_SECRET = original_secret
    
    @patch('app.core.daraja_helper.requests.get')
    def test_get_access_token_api_error(self, mock_get):
        """Mock API error response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        original_key = settings.CONSUMER_KEY
        original_secret = settings.CONSUMER_SECRET
        original_url = settings.DARAJA_CREDENTIALS_URL
        
        settings.CONSUMER_KEY = "test_key"
        settings.CONSUMER_SECRET = "test_secret"
        settings.DARAJA_CREDENTIALS_URL = "https://test.url"
        
        try:
            token = get_access_token()
            assert token is None
        finally:
            settings.CONSUMER_KEY = original_key
            settings.CONSUMER_SECRET = original_secret
            settings.DARAJA_CREDENTIALS_URL = original_url
    
    @patch('app.core.daraja_helper.requests.get')
    def test_get_access_token_invalid_response(self, mock_get):
        """Mock response without access_token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_get.return_value = mock_response
        
        original_key = settings.CONSUMER_KEY
        original_secret = settings.CONSUMER_SECRET
        original_url = settings.DARAJA_CREDENTIALS_URL
        
        settings.CONSUMER_KEY = "test_key"
        settings.CONSUMER_SECRET = "test_secret"
        settings.DARAJA_CREDENTIALS_URL = "https://test.url"
        
        try:
            token = get_access_token()
            assert token is None
        finally:
            settings.CONSUMER_KEY = original_key
            settings.CONSUMER_SECRET = original_secret
            settings.DARAJA_CREDENTIALS_URL = original_url


class TestInitiateSTKPush:
    """Test cases for initiate_stk_push function."""
    
    @pytest.fixture
    def mock_payment(self, db_session, test_user, test_payment_plan):
        """Create a mock payment for testing."""
        from datetime import datetime, timezone
        from dateutil.relativedelta import relativedelta
        
        payment_date = datetime.now(timezone.utc)
        valid_until = payment_date + relativedelta(months=1)
        
        payment = Payment(
            user_id=test_user.user_id,
            payment_date=payment_date,
            valid_until=valid_until,
            amount=100.0,
            plan_id=test_payment_plan.plan_id,  # Use test_payment_plan fixture
            created_by=str(test_user.user_id),
            updated_by=str(test_user.user_id),
            active=True
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)
        return payment
    
    @pytest.fixture
    def mock_plan(self, test_payment_plan):
        """Create a mock payment plan for testing."""
        # Use the existing test_payment_plan fixture
        return test_payment_plan
    
    @patch('app.core.daraja_helper.get_access_token')
    @patch('app.core.daraja_helper.requests.post')
    def test_initiate_stk_push_success(self, mock_post, mock_get_token, mock_payment, mock_plan, db_session):
        """Mock successful STK push."""
        # Mock access token
        mock_get_token.return_value = "test_access_token"
        
        # Mock successful STK push response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "test_checkout_123",
            "ResponseDescription": "Success"
        }
        mock_response.content = b'{"ResponseCode":"0"}'
        mock_post.return_value = mock_response
        
        # Set required settings
        original_short_code = settings.SHORT_CODE
        original_passkey = settings.DARAJA_PASSKEY
        original_url = settings.DARAJA_STK_PUSH_URL
        original_callback = settings.DARAJA_CALLBACK_URL
        
        settings.SHORT_CODE = "174379"
        settings.DARAJA_PASSKEY = "test_passkey"
        settings.DARAJA_STK_PUSH_URL = "https://test.url"
        settings.DARAJA_CALLBACK_URL = "https://callback.url"
        
        # Update payment with correct plan_id
        mock_payment.plan_id = mock_plan.plan_id
        db_session.commit()
        db_session.refresh(mock_payment)
        
        try:
            response_data, status_code = initiate_stk_push(
                mock_payment,
                "254712345678",
                mock_plan,
                db_session
            )
            
            assert status_code == 200
            assert response_data["ResponseCode"] == "0"
            assert response_data["CheckoutRequestID"] == "test_checkout_123"
            mock_post.assert_called_once()
            
            # Verify payment was updated
            db_session.refresh(mock_payment)
            assert mock_payment.mpesa_transaction_id == "test_checkout_123"
            assert mock_payment.transaction_response is not None
        finally:
            settings.SHORT_CODE = original_short_code
            settings.DARAJA_PASSKEY = original_passkey
            settings.DARAJA_STK_PUSH_URL = original_url
            settings.DARAJA_CALLBACK_URL = original_callback
    
    def test_initiate_stk_push_missing_credentials(self, mock_payment, mock_plan, db_session):
        """Test error when SHORT_CODE/PASSKEY missing."""
        original_short_code = settings.SHORT_CODE
        original_passkey = settings.DARAJA_PASSKEY
        
        settings.SHORT_CODE = ""
        settings.DARAJA_PASSKEY = ""
        
        try:
            response_data, status_code = initiate_stk_push(
                mock_payment,
                "254712345678",
                mock_plan,
                db_session
            )
            
            assert status_code == 500
            assert "error" in response_data
        finally:
            settings.SHORT_CODE = original_short_code
            settings.DARAJA_PASSKEY = original_passkey
    
    @patch('app.core.daraja_helper.get_access_token')
    @patch('app.core.daraja_helper.requests.post')
    def test_initiate_stk_push_api_error(self, mock_post, mock_get_token, mock_payment, mock_plan, db_session):
        """Mock Daraja API error."""
        mock_get_token.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "errorCode": "400.001.01",
            "errorMessage": "Bad Request"
        }
        mock_response.content = b'{"errorCode":"400.001.01"}'
        mock_post.return_value = mock_response
        
        original_short_code = settings.SHORT_CODE
        original_passkey = settings.DARAJA_PASSKEY
        original_url = settings.DARAJA_STK_PUSH_URL
        original_callback = settings.DARAJA_CALLBACK_URL
        
        settings.SHORT_CODE = "174379"
        settings.DARAJA_PASSKEY = "test_passkey"
        settings.DARAJA_STK_PUSH_URL = "https://test.url"
        settings.DARAJA_CALLBACK_URL = "https://callback.url"
        
        try:
            response_data, status_code = initiate_stk_push(
                mock_payment,
                "254712345678",
                mock_plan,
                db_session
            )
            
            assert status_code == 400
            assert "errorCode" in response_data
        finally:
            settings.SHORT_CODE = original_short_code
            settings.DARAJA_PASSKEY = original_passkey
            settings.DARAJA_STK_PUSH_URL = original_url
            settings.DARAJA_CALLBACK_URL = original_callback
    
    @patch('app.core.daraja_helper.get_access_token')
    @patch('app.core.daraja_helper.requests.post')
    def test_initiate_stk_push_wrong_credentials(self, mock_post, mock_get_token, mock_payment, mock_plan, db_session):
        """Mock 500.001.1001 error code."""
        mock_get_token.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "errorCode": "500.001.1001",
            "errorMessage": "Wrong credentials"
        }
        mock_response.content = b'{"errorCode":"500.001.1001"}'
        mock_post.return_value = mock_response
        
        original_short_code = settings.SHORT_CODE
        original_passkey = settings.DARAJA_PASSKEY
        original_url = settings.DARAJA_STK_PUSH_URL
        original_callback = settings.DARAJA_CALLBACK_URL
        
        settings.SHORT_CODE = "174379"
        settings.DARAJA_PASSKEY = "test_passkey"
        settings.DARAJA_STK_PUSH_URL = "https://test.url"
        settings.DARAJA_CALLBACK_URL = "https://callback.url"
        
        try:
            response_data, status_code = initiate_stk_push(
                mock_payment,
                "254712345678",
                mock_plan,
                db_session
            )
            
            assert status_code == 500
            assert response_data["errorCode"] == "500.001.1001"
        finally:
            settings.SHORT_CODE = original_short_code
            settings.DARAJA_PASSKEY = original_passkey
            settings.DARAJA_STK_PUSH_URL = original_url
            settings.DARAJA_CALLBACK_URL = original_callback
    
    @patch('app.core.daraja_helper.get_access_token')
    @patch('app.core.daraja_helper.requests.post')
    def test_initiate_stk_push_updates_payment(self, mock_post, mock_get_token, mock_payment, mock_plan, db_session):
        """Verify payment record is updated with transaction details."""
        mock_get_token.return_value = "test_token"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "test_checkout_456",
            "ResponseDescription": "Success"
        }
        mock_response.content = b'{"ResponseCode":"0"}'
        mock_post.return_value = mock_response
        
        original_short_code = settings.SHORT_CODE
        original_passkey = settings.DARAJA_PASSKEY
        original_url = settings.DARAJA_STK_PUSH_URL
        original_callback = settings.DARAJA_CALLBACK_URL
        
        settings.SHORT_CODE = "174379"
        settings.DARAJA_PASSKEY = "test_passkey"
        settings.DARAJA_STK_PUSH_URL = "https://test.url"
        settings.DARAJA_CALLBACK_URL = "https://callback.url"
        
        # Update payment with correct plan_id
        mock_payment.plan_id = mock_plan.plan_id
        db_session.commit()
        db_session.refresh(mock_payment)
        
        try:
            response_data, status_code = initiate_stk_push(
                mock_payment,
                "254712345678",
                mock_plan,
                db_session
            )
            
            assert status_code == 200
            
            # Verify payment was updated
            db_session.refresh(mock_payment)
            assert mock_payment.mpesa_transaction_id == "test_checkout_456"
            assert mock_payment.transaction_request is not None
            assert mock_payment.transaction_response is not None
            assert "BusinessShortCode" in mock_payment.transaction_request
            assert "CheckoutRequestID" in mock_payment.transaction_response
        finally:
            settings.SHORT_CODE = original_short_code
            settings.DARAJA_PASSKEY = original_passkey
            settings.DARAJA_STK_PUSH_URL = original_url
            settings.DARAJA_CALLBACK_URL = original_callback


class TestDarajaTimestampToDatetime:
    """Test cases for daraja_timestamp_to_datetime function."""
    
    def test_daraja_timestamp_valid(self):
        """Test valid timestamp conversion."""
        timestamp_str = "20240119120000"
        dt = daraja_timestamp_to_datetime(timestamp_str)
        
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 19
        assert dt.hour == 12
        assert dt.minute == 0
        assert dt.second == 0
        assert dt.tzinfo == timezone.utc
    
    def test_daraja_timestamp_invalid(self):
        """Test invalid timestamp format."""
        timestamp_str = "invalid"
        dt = daraja_timestamp_to_datetime(timestamp_str)
        
        # Should return current time on error
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc
    
    def test_daraja_timestamp_short(self):
        """Test timestamp with insufficient length."""
        timestamp_str = "20240119"  # Too short
        dt = daraja_timestamp_to_datetime(timestamp_str)
        
        # Should return current time on error
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc
