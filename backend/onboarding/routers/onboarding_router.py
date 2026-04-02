from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from onboarding.models.user_preference_model import UserPreference
from onboarding.schemas.preference_schema import PreferenceCreate
from onboarding.services.preference_service import PreferenceService
from core.db_session import get_db

router = APIRouter(tags=["Onboarding"])


@router.post("/onboarding/preferences")
def save_preferences(
    payload: PreferenceCreate,
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Save the user's onboarding questionnaire answers and return
    a personalized roadmap generated from those preferences.
    """
    effective_user_id = user_id if user_id is not None else payload.user_id
    if effective_user_id is None:
        raise HTTPException(
            status_code=422,
            detail="user_id is required as a query parameter or in the request body",
        )

    pref_service = PreferenceService(db)
    return pref_service.save_preferences_with_roadmap(
        user_id=effective_user_id,
        data=payload,
    )


@router.get("/roadmap/{user_id}")
def get_roadmap(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch the stored preferences for a user and return their roadmap.
    Returns 404 if the user has not completed onboarding yet.
    """
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

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
