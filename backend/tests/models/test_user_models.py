# Tests for models/user_models.py
from auth.models.user_models import User


def test_user_model_creation(db_session):
    user = User(
        email="modeluser@example.com",
        first_name="Model",
        last_name="User",
        password="hashedpassword",
    )
    db_session.add(user)
    db_session.commit()
    fetched = db_session.query(User).filter_by(email="modeluser@example.com").first()
    assert fetched is not None
    assert fetched.email == "modeluser@example.com"
    assert fetched.is_verified is False
    assert fetched.user_email_enabled is True
    assert fetched.user_sms_enabled is False
