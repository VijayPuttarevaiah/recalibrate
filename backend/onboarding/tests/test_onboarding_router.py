"""
TDD - RED phase tests for routers/onboarding_router.py

Covers:
  - POST /onboarding/preferences  → save preferences, return roadmap
  - GET  /roadmap/{user_id}       → fetch stored preferences and return roadmap
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from main import app
from core.db_session import get_db
from onboarding.models.user_preference_model import UserPreference


HOURS_PER_WEEK_DEFAULT = 10
USER_ID_DEFAULT = 1
PREFERENCE_ID_DEFAULT = 1
ROADMAP_SAMPLE = [{"phase": "Month 1", "steps": ["Step A"]}]


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_preference(user_id=USER_ID_DEFAULT):
    pref = MagicMock(spec=UserPreference)
    pref.id = PREFERENCE_ID_DEFAULT
    pref.user_id = user_id
    pref.interest = "coding"
    pref.experience_level = "beginner"
    pref.hours_per_week = HOURS_PER_WEEK_DEFAULT
    pref.target_goal = "Get a dev job"
    return pref


def make_pref_response(roadmap=ROADMAP_SAMPLE):
    return {
        "id": PREFERENCE_ID_DEFAULT,
        "user_id": USER_ID_DEFAULT,
        "interest": "coding",
        "experience_level": "beginner",
        "hours_per_week": HOURS_PER_WEEK_DEFAULT,
        "target_goal": "Get a dev job",
        "roadmap": roadmap,
    }


def _set_pref_lookup(mock_db, preference):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = preference


VALID_PAYLOAD = {
    "user_id": USER_ID_DEFAULT,
    "interest": "coding",
    "experience_level": "beginner",
    "hours_per_week": HOURS_PER_WEEK_DEFAULT,
    "target_goal": "Get a dev job",
}


# ── POST /onboarding/preferences ──────────────────────────────────────────────


@patch("onboarding.routers.onboarding_router.PreferenceService")
def test_pref_200_valid(mock_pref_cls, client):
    mock_pref_cls.return_value.save_preferences_with_roadmap.return_value = (
        make_pref_response()
    )
    response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
    assert response.status_code == HTTP_200_OK


@patch("onboarding.routers.onboarding_router.PreferenceService")
def test_pref_has_roadmap(mock_pref_cls, client):
    mock_pref_cls.return_value.save_preferences_with_roadmap.return_value = (
        make_pref_response()
    )
    response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
    assert "roadmap" in response.json()


@patch("onboarding.routers.onboarding_router.PreferenceService")
def test_pref_roadmap_list(mock_pref_cls, client):
    mock_pref_cls.return_value.save_preferences_with_roadmap.return_value = (
        make_pref_response()
    )
    response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
    assert isinstance(response.json()["roadmap"], list)


@patch("onboarding.routers.onboarding_router.PreferenceService")
def test_pref_calls_save(mock_pref_cls, client):
    mock_pref_inst = mock_pref_cls.return_value
    mock_pref_inst.save_preferences_with_roadmap.return_value = make_pref_response(
        roadmap=[]
    )
    client.post("/onboarding/preferences", json=VALID_PAYLOAD)
    mock_pref_inst.save_preferences_with_roadmap.assert_called_once()


@patch("onboarding.routers.onboarding_router.PreferenceService")
def test_pref_calls_roadmap(mock_pref_cls, client):
    mock_pref_inst = mock_pref_cls.return_value
    mock_pref_inst.save_preferences_with_roadmap.return_value = make_pref_response(
        roadmap=[]
    )
    client.post("/onboarding/preferences", json=VALID_PAYLOAD)
    mock_pref_inst.save_preferences_with_roadmap.assert_called_once()


def test_pref_422_missing(client):
    incomplete = {"user_id": USER_ID_DEFAULT, "interest": "coding"}
    response = client.post("/onboarding/preferences", json=incomplete)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY


# ── GET /roadmap/{user_id} ─────────────────────────────────────────────────────


@patch("onboarding.routers.onboarding_router.RoadmapService")
def test_roadmap_200_found(mock_roadmap_cls, client, mock_db):
    _set_pref_lookup(mock_db, make_preference())
    mock_roadmap_cls.return_value.generate_roadmap.return_value = [
        {"phase": "Month 1", "steps": ["Step A"]}
    ]
    response = client.get(f"/roadmap/{USER_ID_DEFAULT}")
    assert response.status_code == HTTP_200_OK


@patch("onboarding.routers.onboarding_router.RoadmapService")
def test_roadmap_has_list(mock_roadmap_cls, client, mock_db):
    _set_pref_lookup(mock_db, make_preference())
    mock_roadmap_cls.return_value.generate_roadmap.return_value = [
        {"phase": "Month 1", "steps": ["Step A"]}
    ]
    response = client.get(f"/roadmap/{USER_ID_DEFAULT}")
    assert "roadmap" in response.json()


def test_roadmap_404_missing(client, mock_db):
    _set_pref_lookup(mock_db, None)
    response = client.get("/roadmap/99")
    assert response.status_code == HTTP_404_NOT_FOUND


def test_roadmap_404_detail_msg(client, mock_db):
    _set_pref_lookup(mock_db, None)
    response = client.get("/roadmap/99")
    assert "preference" in response.json()["detail"].lower()
