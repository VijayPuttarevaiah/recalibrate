# Test cases for /login endpoint

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_UNPROCESSABLE = 422


def test_login_success(client, register_user, verify_user):
    email = "loginuser@example.com"
    password = "Password123!"
    register_user(email=email, password=password)
    verify_user(email)

    response = client.post("/login", data={"username": email, "password": password})
    assert response.status_code == HTTP_OK
    assert "access_token" in response.json()


def test_login_wrong_password(client, register_user, verify_user):
    email = "wrongpass@example.com"
    password = "Password123!"
    register_user(email=email, password=password)
    verify_user(email)

    response = client.post("/login", data={"username": email, "password": "WrongPassword"})
    assert response.status_code == HTTP_BAD_REQUEST
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_unverified_email(client, register_user):
    email = "unverified@example.com"
    password = "Password123!"
    register_user(email=email, password=password)

    response = client.post("/login", data={"username": email, "password": password})
    assert response.status_code == HTTP_FORBIDDEN
    assert "Email not verified" in response.json()["detail"]

# Test login failure when required form fields are missing
def test_login_missing_fields(client):
    response = client.post("/login", data={
        "username": "missingpass@example.com"
    })
    assert response.status_code == HTTP_UNPROCESSABLE

# Test login behavior with empty credentials
def test_login_empty_credentials(client):
    response = client.post(
        "/login",
        data={
            "username": "",
            "password": ""
        }
    )

    assert response.status_code in (HTTP_BAD_REQUEST, HTTP_UNPROCESSABLE)

# Test login behavior with an invalid email format
def test_login_invalid_email(client):
    response = client.post("/login", data={
        "username": "notanemail",
        "password": "Password123!"
    })
    # Should return 400 or 422 depending on how pydantic/fastapi handles the error
    assert response.status_code in (HTTP_BAD_REQUEST, HTTP_UNPROCESSABLE)
