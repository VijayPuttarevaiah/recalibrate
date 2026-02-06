# Import TestClient to simulate API requests during testing
from fastapi.testclient import TestClient
import pytest 
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models.base import Base
from routers.login import get_db as login_get_db
from routers.register import get_db as register_get_db
from routers.email_verification import get_db as email_get_db
from routers.logout import get_db as logout_get_db

# Use an in-memory SQLite database to ensure tests are fast and isolated
DATABASE_URL = "sqlite:///:memory:"

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
    app.dependency_overrides[login_get_db] = override_get_db
    app.dependency_overrides[register_get_db] = override_get_db
    app.dependency_overrides[email_get_db] = override_get_db
    app.dependency_overrides[logout_get_db] = override_get_db
    
    # Yield the TestClient instance
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear dependency overrides after each test to avoid side effects
    app.dependency_overrides.clear()