"""

Covers all four routing agents:
  - Coding/Software
  - Fitness/Health
  - Immigration/Visa
  - Career (default)

And all experience levels: beginner, intermediate, advanced.
"""

import pytest
from goals.roadmap.service import RoadmapService

MIN_PHASES_CODING = 3
MIN_PHASES_CODING_ADVANCED = 2
MIN_PHASES_FITNESS = 3
MIN_PHASES_FITNESS_ADVANCED = 2
MIN_PHASES_IMMIGRATION = 2
MIN_PHASES_CAREER = 2

@pytest.fixture
def service():
    return RoadmapService()

# ── Return type ────────────────────────────────────────────────────────────────

def test_returns_a_list(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    assert isinstance(result, list)

def test_each_phase_has_phase_key(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    for phase in result:
        assert "phase" in phase

def test_each_phase_has_steps_key(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    for phase in result:
        assert "steps" in phase

def test_steps_is_a_list(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    for phase in result:
        assert isinstance(phase["steps"], list)

def test_result_is_not_empty(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    assert len(result) > 0

# ── Coding agent ───────────────────────────────────────────────────────────────

def test_coding_beginner_roadmap(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    assert len(result) >= MIN_PHASES_CODING

def test_software_triggers_coding(service):
    result = service.generate_roadmap("software", "beginner", 10, 4)
    assert len(result) >= MIN_PHASES_CODING

def test_tech_triggers_coding(service):
    result = service.generate_roadmap("tech", "intermediate", 10, 4)
    assert len(result) >= MIN_PHASES_CODING

def test_coding_intermediate(service):
    result = service.generate_roadmap("coding", "intermediate", 10, 4)
    assert len(result) >= MIN_PHASES_CODING

def test_coding_advanced_roadmap(service):
    result = service.generate_roadmap("coding", "advanced", 10, 4)
    assert len(result) >= MIN_PHASES_CODING_ADVANCED

def test_coding_steps_non_empty(service):
    result = service.generate_roadmap("coding", "beginner", 10, 4)
    for phase in result:
        assert len(phase["steps"]) > 0

# ── Fitness agent ──────────────────────────────────────────────────────────────

def test_fitness_beginner_roadmap(service):
    result = service.generate_roadmap("fitness", "beginner", 5, 3)
    assert len(result) >= MIN_PHASES_FITNESS

def test_health_triggers_fitness(service):
    result = service.generate_roadmap("health", "beginner", 5, 3)
    assert len(result) >= MIN_PHASES_FITNESS

def test_gym_triggers_fitness(service):
    result = service.generate_roadmap("gym", "intermediate", 5, 3)
    assert len(result) >= MIN_PHASES_FITNESS

def test_fitness_intermediate(service):
    result = service.generate_roadmap("fitness", "intermediate", 5, 3)
    assert len(result) >= MIN_PHASES_FITNESS

def test_fitness_advanced_roadmap(service):
    result = service.generate_roadmap("fitness", "advanced", 5, 3)
    assert len(result) >= MIN_PHASES_FITNESS_ADVANCED

# ── Immigration agent ──────────────────────────────────────────────────────────

def test_immigration_roadmap(service):
    result = service.generate_roadmap("immigration", "beginner", 5, 6)
    assert len(result) >= MIN_PHASES_IMMIGRATION

def test_visa_triggers_immigration(service):
    result = service.generate_roadmap("visa", "beginner", 5, 6)
    assert len(result) >= MIN_PHASES_IMMIGRATION

def test_pr_triggers_immigration(service):
    result = service.generate_roadmap("pr", "beginner", 5, 6)
    assert len(result) >= MIN_PHASES_IMMIGRATION

# ── Career agent (default) ─────────────────────────────────────────────────────

def test_unknown_interest_career(service):
    result = service.generate_roadmap("painting", "beginner", 5, 3)
    assert len(result) >= MIN_PHASES_CAREER

def test_career_keyword_roadmap(service):
    result = service.generate_roadmap("career", "intermediate", 5, 3)
    assert len(result) >= MIN_PHASES_CAREER

def test_empty_interest_roadmap(service):
    result = service.generate_roadmap("", "beginner", 5, 3)
    assert isinstance(result, list)
    assert len(result) >= 1

def test_none_interest_roadmap(service):
    result = service.generate_roadmap(None, "beginner", 5, 3)
    assert isinstance(result, list)
    assert len(result) >= 1
