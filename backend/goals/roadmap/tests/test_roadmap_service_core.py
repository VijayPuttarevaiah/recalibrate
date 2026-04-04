"""Core roadmap service tests (return type + coding agent)."""

import pytest

from goals.roadmap.service import RoadmapService

MIN_PHASES_CODING = 3
MIN_PHASES_CODING_ADVANCED = 2


@pytest.fixture
def service():
    return RoadmapService()


# Return type


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


# Coding agent


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
