"""
@file router.py
@description Personalized roadmap endpoint — fetches user preferences
             and delegates generation to RoadmapService.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from onboarding.models.user_preference_model import UserPreference
from goals.roadmap.service import RoadmapService
from core.db_session import get_db

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


@router.get("/{user_id}")
def get_user_roadmap(user_id: int, db: Session = Depends(get_db)):
    """
    Returns a personalized roadmap based on the user's saved preferences.
    Raises 404 if no preferences exist for the user.
    """
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

    if not pref:
        raise HTTPException(
            status_code=404,
            detail="No preferences found for this user. Complete onboarding first.",
        )

    roadmap = RoadmapService().generate_roadmap(
        interest=pref.interest,
        experience_level=pref.experience_level,
        hours_per_week=pref.hours_per_week,
        timeline_months=4,
    )

    return {"roadmap": roadmap}
