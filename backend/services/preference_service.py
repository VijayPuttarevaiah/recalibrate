from sqlalchemy.orm import Session

from models.user_preference_model import UserPreference
from schemas.preference_schema import PreferenceCreate


class PreferenceService:
    def __init__(self, db: Session):
        self.db = db

    def save_preferences(self, user_id: int, data: PreferenceCreate) -> UserPreference:
        """
        Create or update preferences for a user.
        If preferences already exist for the user, update them in place.
        """
        existing = (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .first()
        )

        if existing:
            for field, value in data.model_dump().items():
                setattr(existing, field, value)
            pref = existing
        else:
            pref = UserPreference(user_id=user_id, **data.model_dump())
            self.db.add(pref)

        self.db.commit()
        self.db.refresh(pref)
        return pref