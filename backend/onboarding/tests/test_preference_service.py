"""

Covers:
  - save_preferences: create new, update existing, db commit/refresh
"""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from onboarding.services.preference_service import PreferenceService
from onboarding.schemas.preference_schema import PreferenceCreate
from onboarding.models.user_preference_model import UserPreference

# ── Fixtures ───────────────────────────────────────────────────────────────────
DEFAULT_USER_ID = 1
EXISTING_USER_ID = 42
HOURS_PER_WEEK_DEFAULT = 10
HOURS_PER_WEEK_EXISTING = 5
PREFERENCE_ID_DEFAULT = 1

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

@pytest.fixture
def sample_data():
    return PreferenceCreate(
        interest="coding",
        experience_level="beginner",
        hours_per_week=HOURS_PER_WEEK_DEFAULT,
        target_goal="Get a developer job",
    )

@pytest.fixture
def existing_pref():
    pref = MagicMock(spec=UserPreference)
    pref.id = PREFERENCE_ID_DEFAULT
    pref.user_id = EXISTING_USER_ID
    pref.interest = "fitness"
    pref.experience_level = "intermediate"
    pref.hours_per_week = HOURS_PER_WEEK_EXISTING
    pref.target_goal = "Lose weight"
    return pref

def _set_pref_lookup(mock_db, preference):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = preference

# ── save_preferences: CREATE path ─────────────────────────────────────────────

def test_adds_pref_when_none(mock_db, sample_data):
    _set_pref_lookup(mock_db, None)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=DEFAULT_USER_ID, data=sample_data)
    mock_db.add.assert_called_once()

def test_commits_after_create(mock_db, sample_data):
    _set_pref_lookup(mock_db, None)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=DEFAULT_USER_ID, data=sample_data)
    mock_db.commit.assert_called_once()

def test_refreshes_after_create(mock_db, sample_data):
    _set_pref_lookup(mock_db, None)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=DEFAULT_USER_ID, data=sample_data)
    mock_db.refresh.assert_called_once()

def test_returns_pref_on_create(mock_db, sample_data):
    _set_pref_lookup(mock_db, None)
    service = PreferenceService(mock_db)
    result = service.save_preferences(user_id=DEFAULT_USER_ID, data=sample_data)
    assert result is not None

def test_no_add_when_pref_exists(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    mock_db.add.assert_not_called()

# ── save_preferences: UPDATE path ─────────────────────────────────────────────

def test_updates_pref_fields(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    assert existing_pref.interest == "coding"

def test_updates_experience_level(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    assert existing_pref.experience_level == "beginner"

def test_updates_hours_per_week(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    assert existing_pref.hours_per_week == HOURS_PER_WEEK_DEFAULT

def test_commits_after_update(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    mock_db.commit.assert_called_once()

def test_returns_updated_pref(mock_db, sample_data, existing_pref):
    _set_pref_lookup(mock_db, existing_pref)
    service = PreferenceService(mock_db)
    result = service.save_preferences(user_id=EXISTING_USER_ID, data=sample_data)
    assert result is existing_pref
