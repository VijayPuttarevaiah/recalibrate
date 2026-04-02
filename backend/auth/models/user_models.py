from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timezone
from core.base import Base


# Represents the User entity in the database
class User(Base):
    __tablename__ = "users"
    # Primary key for the user, uniquely identifying each record
    id = Column(Integer, primary_key=True, autoincrement=True)
    # User email address, must be unique across all users
    email = Column(String(512), unique=True, nullable=False)
    # User's first name
    first_name = Column(String(512), nullable=False)
    # User's last name
    last_name = Column(String(512), nullable=False)
    # Hashed version of the user's password for security
    password = Column(String(512), nullable=False)
    # Timestamp when the user record was created
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Timestamp when the user record was last updated
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    # Flag to enable/disable email notifications for the user
    user_email_enabled = Column(Boolean, default=True)
    # Flag to enable/disable SMS notifications for the user
    user_sms_enabled = Column(Boolean, default=False)
    # Flag indicating whether the user's email has been verified
    is_verified = Column(Boolean, default=False, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_email_enabled": self.user_email_enabled,
            "user_sms_enabled": self.user_sms_enabled,
            "is_verified": self.is_verified,
        }

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, email={self.email!r}, is_verified={self.is_verified})"
        )
