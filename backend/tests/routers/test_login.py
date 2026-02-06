# Test cases for /login endpoint
import pytest
from models.user_models import User

# Helper function to register and manually verify a user during tests
def register_and_verify(db_session, client, email, password):
    # Register user via the API endpoint
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": password
    })
    # Manually bypass email verification by setting the flag in the database directly
    user = db_session.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        db_session.commit()

# Test successful login after registration and verification
def test_login_success(db_session, client):
    email = "loginuser@example.com"
    password = "Password123"
    register_and_verify(db_session, client, email, password)
    # User is verified in DB for this test
    response = client.post("/login", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

# Test login failure when an incorrect password is provided
def test_login_wrong_password(db_session, client):
    email = "wrongpass@example.com"
    password = "Password123"
    register_and_verify(db_session, client, email, password)
    response = client.post("/login", data={
        "username": email,
        "password": "WrongPassword"
    })
    assert response.status_code == 400
    assert "Incorrect email or password" in response.json()["detail"]

# Test login failure when the user's email has not been verified
def test_login_unverified_email(client):
    # Register user but do not verify
    email = "unverified@example.com"
    password = "Password123"
    client.post("/register", json={
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": password
    })
    response = client.post("/login", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 403
    assert "Email not verified" in response.json()["detail"]

# Test login failure when required form fields are missing
def test_login_missing_fields(client):
    response = client.post("/login", data={
        "username": "missingpass@example.com"
    })
    assert response.status_code == 422 

# Test login behavior with empty credentials
def test_login_empty_credentials(client):
    response = client.post(
        "/login",
        data={
            "username": "",
            "password": ""
        }
    )

    assert response.status_code in (400, 422)

# Test login behavior with an invalid email format
def test_login_invalid_email(client):
	response = client.post("/login", data={
		"username": "notanemail",
		"password": "Password123"
	})
	# Should return 400 or 422 depending on how pydantic/fastapi handles the error
	assert response.status_code in (400, 422)
