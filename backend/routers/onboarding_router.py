from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.user_preference_model import UserPreference
from schemas.preference_schema import PreferenceCreate
from services.preference_service import PreferenceService
from services.roadmap_service import RoadmapService
from utils.db_session import get_db

router = APIRouter(tags=["Onboarding"])


class OnboardingRequest(BaseModel):
    user_id: int
    interest: str
    experience_level: str
    hours_per_week: int
    target_goal: str


@router.post("/onboarding/preferences")
def save_preferences(payload: OnboardingRequest, db: Session = Depends(get_db)):
    """
    Save the user's onboarding questionnaire answers and return
    a personalized roadmap generated from those preferences.
    """
    pref_data = PreferenceCreate(
        interest=payload.interest,
        experience_level=payload.experience_level,
        hours_per_week=payload.hours_per_week,
        target_goal=payload.target_goal,
    )

    pref_service = PreferenceService(db)
    pref_service.save_preferences(user_id=payload.user_id, data=pref_data)

    roadmap_service = RoadmapService()
    roadmap = roadmap_service.generate_roadmap(
        interest=payload.interest,
        experience_level=payload.experience_level,
        hours_per_week=payload.hours_per_week,
        timeline_months=3,
    )

    return {"roadmap": roadmap}


@router.get("/roadmap/{user_id}")
def get_roadmap(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch the stored preferences for a user and return their roadmap.
    Returns 404 if the user has not completed onboarding yet.
    """
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )

    if not pref:
        raise HTTPException(
            status_code=404,
            detail="No preferences found for this user. Please complete onboarding.",
        )

    roadmap_service = RoadmapService()
    roadmap = roadmap_service.generate_roadmap(
        interest=pref.interest,
        experience_level=pref.experience_level,
        hours_per_week=pref.hours_per_week,
        timeline_months=3,
    )

    return {"roadmap": roadmap}