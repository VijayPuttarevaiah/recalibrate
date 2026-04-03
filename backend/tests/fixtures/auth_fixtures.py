import pytest

from auth.models.user_models import User

VERIFICATION_CODE_LENGTH = 6
PASSWORD_RESET_CODE_LENGTH = 8

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
