import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Patch SQLite to handle UUID types BEFORE importing models
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

def visit_UUID(self, type_, **kw):
    """Convert UUID to String for SQLite."""
    return "VARCHAR(36)"

# Apply the patch before any imports that use UUID
if not hasattr(SQLiteTypeCompiler, '_uuid_patched'):
    SQLiteTypeCompiler.visit_UUID = visit_UUID
    SQLiteTypeCompiler._uuid_patched = True

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match
from app.models.payment_plan import PaymentPlan
from app.models.payment import Payment
from app.models.enums import PlanEnum
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta, datetime, timezone
from dateutil.relativedelta import relativedelta
from app.core.config import settings

# Create SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign keys for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user for authenticated tests."""
    hashed_password = get_password_hash("testpassword123")
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=hashed_password,
        created_by="test@example.com",
        updated_by="test@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create a second test user for testing matches."""
    hashed_password = get_password_hash("testpassword123")
    user = User(
        email="test2@example.com",
        first_name="Test",
        last_name="User2",
        hashed_password=hashed_password,
        created_by="test2@example.com",
        updated_by="test2@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_headers(user_email: str):
    """Helper function to generate auth headers for a user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_email},
        expires_delta=access_token_expires
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_payment_plan(db_session, test_user):
    """Create a test payment plan for testing."""
    plan = PaymentPlan(
        plan=PlanEnum.MONTHLY,
        amount=100.0,
        months=1,
        created_by=str(test_user.user_id),
        updated_by=str(test_user.user_id),
        active=True
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture
def test_payment(db_session, test_user, test_payment_plan):
    """Create a test payment linked to test_user and test_payment_plan."""
    payment_date = datetime.now(timezone.utc)
    valid_until = payment_date + relativedelta(months=test_payment_plan.months)
    
    payment = Payment(
        user_id=test_user.user_id,
        payment_ref=None,
        payment_date=payment_date,
        valid_until=valid_until,
        amount=test_payment_plan.amount,
        plan_id=test_payment_plan.plan_id,
        mpesa_transaction_id=None,
        transaction_request=None,
        transaction_response=None,
        transaction_callback=None,
        transaction_status=None,
        date_completed=None,
        created_by=str(test_user.user_id),
        updated_by=str(test_user.user_id),
        active=True
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


@pytest.fixture
def test_user_with_fcm(db_session):
    """Create a test user with FCM token for notification tests."""
    hashed_password = get_password_hash("testpassword123")
    user = User(
        email="fcmuser@example.com",
        first_name="FCM",
        last_name="User",
        hashed_password=hashed_password,
        fcm_token="test_fcm_token_12345",
        created_by="fcmuser@example.com",
        updated_by="fcmuser@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
