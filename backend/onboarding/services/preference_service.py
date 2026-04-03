from sqlalchemy.orm import Session

from onboarding.models.user_preference_model import UserPreference
from onboarding.schemas.preference_schema import PreferenceCreate, PreferenceResponse
from goals.roadmap.service import RoadmapService


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

        payload = data.model_dump(exclude={"user_id"})

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            pref = existing
        else:
            pref = UserPreference(user_id=user_id, **payload)
            self.db.add(pref)

        self.db.commit()
        self.db.refresh(pref)
        return pref

    def save_preferences_with_roadmap(
        self, user_id: int, data: PreferenceCreate
    ) -> dict:
        pref = self.save_preferences(user_id=user_id, data=data)
        roadmap_service = RoadmapService()
        roadmap = roadmap_service.generate_roadmap(
            interest=data.interest,
            experience_level=data.experience_level,
            hours_per_week=data.hours_per_week,
            timeline_months=3,
        )
        pref_response = PreferenceResponse.model_validate(pref)
        response_data = pref_response.model_dump()
        response_data["roadmap"] = roadmap
        return response_data
