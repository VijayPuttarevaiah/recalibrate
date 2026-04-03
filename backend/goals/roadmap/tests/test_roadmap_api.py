"""
@file test_roadmap_api.py
@description TDD tests for the personalized roadmap router.
"""

from starlette import status
from auth.models.user_models import User
from onboarding.models.user_preference_model import UserPreference

def _create_user_with_preferences(db, email, interest, experience_level):
    user = User(email=email, first_name="Test", last_name="User", password="hashed")
    db.add(user)
    db.commit()
    db.refresh(user)

    pref = UserPreference(
        user_id=user.id,
        interest=interest,
        experience_level=experience_level,
        hours_per_week=10,
        target_goal="Test goal",
    )
    db.add(pref)
    db.commit()
    return user

# ── Happy path ────────────────────────────────────────────────────────────────

def test_get_roadmap_returns_200(client, db_session):
    user = _create_user_with_preferences(
        db_session,
        "road1@example.com",
        "coding",
        "beginner",
    )
    response = client.get(f"/roadmap/{user.id}")
    assert response.status_code == status.HTTP_200_OK

def test_get_roadmap_has_key(client, db_session):
    user = _create_user_with_preferences(
        db_session,
        "road2@example.com",
        "fitness",
        "intermediate",
    )
    response = client.get(f"/roadmap/{user.id}")
    assert "roadmap" in response.json()

def test_get_roadmap_has_phases(client, db_session):
    user = _create_user_with_preferences(
        db_session,
        "road3@example.com",
        "career",
        "beginner",
    )
    data = client.get(f"/roadmap/{user.id}").json()
    assert len(data["roadmap"]) > 0

def test_get_roadmap_steps(client, db_session):
    user = _create_user_with_preferences(
        db_session,
        "road4@example.com",
        "coding",
        "advanced",
    )
    data = client.get(f"/roadmap/{user.id}").json()
    for phase in data["roadmap"]:
        assert "phase" in phase
        assert "steps" in phase
        assert len(phase["steps"]) > 0

def test_get_roadmap_interest(client, db_session):
    """Fitness user should get fitness-specific steps, not generic ones."""
    user = _create_user_with_preferences(
        db_session,
        "road5@example.com",
        "fitness",
        "beginner",
    )
    data = client.get(f"/roadmap/{user.id}").json()
    all_steps = [s for phase in data["roadmap"] for s in phase["steps"]]
    fitness_keywords = [
        "workout",
        "cardio",
        "training",
        "nutrition",
        "strength",
        "food",
    ]
    assert any(any(k in s.lower() for k in fitness_keywords) for s in all_steps)

def test_get_roadmap_coding_steps(client, db_session):
    user = _create_user_with_preferences(
        db_session,
        "road6@example.com",
        "coding",
        "beginner",
    )
    data = client.get(f"/roadmap/{user.id}").json()
    all_steps = [s for phase in data["roadmap"] for s in phase["steps"]]
    coding_keywords = [
        "programming",
        "project",
        "algorithm",
        "portfolio",
        "code",
        "developer",
    ]
    assert any(any(k in s.lower() for k in coding_keywords) for s in all_steps)

# ── No preferences ────────────────────────────────────────────────────────────

def test_get_roadmap_404_no_prefs(client, db_session):
    """A user with no saved preferences should get 404."""
    user = User(
        email="nopref@example.com",
        first_name="No",
        last_name="Pref",
        password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.get(f"/roadmap/{user.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_roadmap_404_no_user(client):
    response = client.get("/roadmap/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# ── Preference API ────────────────────────────────────────────────────────────

def test_save_prefs_200(client, db_session):
    user = User(
        email="api_pref@example.com",
        first_name="API",
        last_name="Test",
        password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        f"/onboarding/preferences?user_id={user.id}",
        json={
            "interest": "software",
            "experience_level": "beginner",
            "hours_per_week": 10,
            "target_goal": "backend developer",
        },
    )
    assert response.status_code == status.HTTP_200_OK

def test_save_prefs_returns_data(client, db_session):
    user = User(
        email="api_pref2@example.com",
        first_name="API",
        last_name="Test2",
        password="hashed",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        f"/onboarding/preferences?user_id={user.id}",
        json={
            "interest": "fitness",
            "experience_level": "intermediate",
            "hours_per_week": 5,
            "target_goal": "lose weight",
        },
    )
    data = response.json()
    assert data["interest"] == "fitness"
    assert data["user_id"] == user.id
