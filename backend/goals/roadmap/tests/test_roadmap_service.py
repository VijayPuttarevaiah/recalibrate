"""
TDD - RED phase tests for services/roadmap_service.py

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

class TestReturnType:

    def test_returns_a_list(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        assert isinstance(result, list)

    def test_each_phase_has_phase_key(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        for phase in result:
            assert "phase" in phase

    def test_each_phase_has_steps_key(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        for phase in result:
            assert "steps" in phase

    def test_steps_is_a_list(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        for phase in result:
            assert isinstance(phase["steps"], list)

    def test_result_is_not_empty(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        assert len(result) > 0


# ── Coding agent ───────────────────────────────────────────────────────────────

class TestCodingAgent:

    def test_coding_beginner_returns_roadmap(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        assert len(result) >= MIN_PHASES_CODING

    def test_software_keyword_triggers_coding_agent(self, service):
        result = service.generate_roadmap("software", "beginner", 10, 4)
        assert len(result) >= MIN_PHASES_CODING

    def test_tech_keyword_triggers_coding_agent(self, service):
        result = service.generate_roadmap("tech", "intermediate", 10, 4)
        assert len(result) >= MIN_PHASES_CODING

    def test_coding_intermediate_returns_roadmap(self, service):
        result = service.generate_roadmap("coding", "intermediate", 10, 4)
        assert len(result) >= MIN_PHASES_CODING

    def test_coding_advanced_returns_roadmap(self, service):
        result = service.generate_roadmap("coding", "advanced", 10, 4)
        assert len(result) >= MIN_PHASES_CODING_ADVANCED

    def test_coding_beginner_steps_are_non_empty(self, service):
        result = service.generate_roadmap("coding", "beginner", 10, 4)
        for phase in result:
            assert len(phase["steps"]) > 0


# ── Fitness agent ──────────────────────────────────────────────────────────────

class TestFitnessAgent:

    def test_fitness_beginner_returns_roadmap(self, service):
        result = service.generate_roadmap("fitness", "beginner", 5, 3)
        assert len(result) >= MIN_PHASES_FITNESS

    def test_health_keyword_triggers_fitness_agent(self, service):
        result = service.generate_roadmap("health", "beginner", 5, 3)
        assert len(result) >= MIN_PHASES_FITNESS

    def test_gym_keyword_triggers_fitness_agent(self, service):
        result = service.generate_roadmap("gym", "intermediate", 5, 3)
        assert len(result) >= MIN_PHASES_FITNESS

    def test_fitness_intermediate_returns_roadmap(self, service):
        result = service.generate_roadmap("fitness", "intermediate", 5, 3)
        assert len(result) >= MIN_PHASES_FITNESS

    def test_fitness_advanced_returns_roadmap(self, service):
        result = service.generate_roadmap("fitness", "advanced", 5, 3)
        assert len(result) >= MIN_PHASES_FITNESS_ADVANCED


# ── Immigration agent ──────────────────────────────────────────────────────────

class TestImmigrationAgent:

    def test_immigration_returns_roadmap(self, service):
        result = service.generate_roadmap("immigration", "beginner", 5, 6)
        assert len(result) >= MIN_PHASES_IMMIGRATION

    def test_visa_keyword_triggers_immigration_agent(self, service):
        result = service.generate_roadmap("visa", "beginner", 5, 6)
        assert len(result) >= MIN_PHASES_IMMIGRATION

    def test_pr_keyword_triggers_immigration_agent(self, service):
        result = service.generate_roadmap("pr", "beginner", 5, 6)
        assert len(result) >= MIN_PHASES_IMMIGRATION


# ── Career agent (default) ─────────────────────────────────────────────────────

class TestCareerAgent:

    def test_unknown_interest_returns_career_roadmap(self, service):
        result = service.generate_roadmap("painting", "beginner", 5, 3)
        assert len(result) >= MIN_PHASES_CAREER

    def test_career_keyword_returns_roadmap(self, service):
        result = service.generate_roadmap("career", "intermediate", 5, 3)
        assert len(result) >= MIN_PHASES_CAREER

    def test_empty_interest_returns_roadmap(self, service):
        result = service.generate_roadmap("", "beginner", 5, 3)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_none_interest_returns_roadmap(self, service):
        result = service.generate_roadmap(None, "beginner", 5, 3)
        assert isinstance(result, list)
        assert len(result) >= 1