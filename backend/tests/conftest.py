# Import TestClient to simulate API requests during testing
from fastapi.testclient import TestClient
import pytest 
import os
from auth.models.user_models import User

# Set environment variable before importing app to ensure DBSession uses it
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.base import Base
from core.db_session import get_db
from auth.utils.auth import get_current_user

# Use an in-memory SQLite database to ensure tests are fast and isolated
DATABASE_URL = "sqlite:///:memory:"
VERIFICATION_CODE_LENGTH = 6
PASSWORD_RESET_CODE_LENGTH = 8

# Fixture to provide a clean database session for each test
@pytest.fixture(name="db_session")
def db_session_fixture():
    # Initialize the test database engine
    # StaticPool is used with in-memory SQLite to maintain the database connection throughout the test
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Create tables in the test database
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        # Yield the session for the test to use
        yield session
    finally:
        # Clean up: close the session and drop all tables after the test
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

# Fixture to provide a FastAPI TestClient with database dependencies overridden
@pytest.fixture(name="client")
def client_fixture(db_session):
    # Function to override the production get_db dependency with the test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Apply database dependency overrides for all relevant routers
    app.dependency_overrides[get_db] = override_get_db
    
    # Yield the TestClient instance
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear dependency overrides after each test to avoid side effects
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_client")
def auth_client_fixture(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {"user_id": 1, "email": "test@example.com"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_code_stores():
    from auth.email_verification.service import verification_codes
    from auth.password_reset.service import reset_codes

    verification_codes.clear()
    reset_codes.clear()
    yield
    verification_codes.clear()
    reset_codes.clear()


@pytest.fixture(autouse=True)
def mock_email_sender(monkeypatch):
    sent_emails = []

    def fake_send_email(to_email: str, subject: str, body: str):
        sent_emails.append({"to": to_email, "subject": subject, "body": body})

    monkeypatch.setattr("auth.utils.email_sender.send_email", fake_send_email)
    monkeypatch.setattr("auth.email_verification.service.send_email", fake_send_email)
    monkeypatch.setattr("auth.password_reset.service.send_email", fake_send_email)
    return sent_emails


@pytest.fixture
def register_user(client):
    def _register(
        email: str,
        password: str = "Password123!",
        first_name: str = "Test",
        last_name: str = "User",
    ):
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        }
        return client.post("/register", json=payload)

    return _register


@pytest.fixture
def verify_user(db_session):
    def _verify(email: str, verified: bool = True):
        user = db_session.query(User).filter(User.email == email).first()
        if user:
            user.is_verified = verified
            db_session.commit()
        return user

    return _verify


@pytest.fixture
def verification_code(monkeypatch):
    code = "VERIFY1"

    def _generate(self, length: int = VERIFICATION_CODE_LENGTH):
        return code

    monkeypatch.setattr(
        "auth.email_verification.service.VerificationService.generate_code",
        _generate,
    )
    return code


@pytest.fixture
def password_reset_code(monkeypatch):
    code = "RESET123"

    def _generate(self, length: int = PASSWORD_RESET_CODE_LENGTH):
        return code

    monkeypatch.setattr(
        "auth.password_reset.service.PasswordResetService.generate_code",
        _generate,
    )
    return code