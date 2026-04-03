import pytest
from unittest.mock import patch, MagicMock
from replan.llm.service import (
    call_llm_for_tasks,
    ReplanTaskRequest,
    generate_replan_tasks,
    generate_replan_explanation,
)

EXPECTED_TASK_COUNT_TWO = 2

def test_llm_tasks_valid():
    """Test _call_llm_for_tasks with a valid LLM response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": """
                    [
                        {"title": "Task 1", "date": "2026-03-07"},
                        {"title": "Task 2", "date": "2026-03-08"}
                    ]
                    """
                }
            }
        ]
    }

    import replan.llm.service as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            tasks = call_llm_for_tasks("test prompt")
            assert len(tasks) == EXPECTED_TASK_COUNT_TWO
            assert tasks[0]["title"] == "Task 1"
            assert tasks[1]["date"] == "2026-03-08"

def test_llm_tasks_invalid():
    """Test _call_llm_for_tasks with an invalid LLM response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Invalid JSON"}}]
    }

    import replan.llm.service as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(ValueError, match="No JSON array found in LLM response"):
                call_llm_for_tasks("test prompt")

def test_llm_tasks_missing_key():
    """Fail fast when OPENROUTER_API_KEY is missing."""
    import replan.llm.service as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", ""):
        with patch("requests.post") as mock_post:
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                replan_llm.call_llm_for_tasks("test prompt")
            mock_post.assert_not_called()

def test_llm_tasks_first_array():
    """If response contains multiple JSON arrays, use the first one."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": (
                        "Here is the plan A: "
                        '[{"title": "Task A", "date": "2026-03-07"}] '
                        "And plan B: "
                        '[{"title": "Task B", "date": "2026-03-08"}]'
                    )
                }
            }
        ]
    }

    import replan.llm.service as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            tasks = call_llm_for_tasks("test prompt")
            assert len(tasks) == 1
            assert tasks[0]["title"] == "Task A"

def test_llm_tasks_invalid_date():
    """Date must be YYYY-MM-DD; invalid formats should raise."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": '[{"title": "Task X", "date": "03/07/2026"}]'}}
        ]
    }

    import replan.llm.service as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(ValueError, match="date format"):
                call_llm_for_tasks("test prompt")

def test_generate_replan_tasks():
    """Test generate_replan_tasks with mocked _call_llm_for_tasks."""
    with patch(
        "replan.llm.service.call_llm_for_tasks",
        return_value=[{"title": "Task 1", "date": "2026-03-07"}],
    ):
        request = ReplanTaskRequest(
            goal_title="Goal Title",
            category="Category",
            start_date="2026-03-01",
            end_date="2026-03-10",
            goal_end_date="2026-03-15",
            notes="Notes",
            progress_context="Progress Context",
            research_context="Research Context",
        )
        tasks = generate_replan_tasks(request)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task 1"

def test_generate_explanation():
    """Test generate_replan_explanation with mocked LLM response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Your plan was adjusted due to missed tasks."}}
        ]
    }

    with patch("requests.post", return_value=mock_response):
        explanation = generate_replan_explanation(
            "Goal Title",
            "Category",
            {"stats": {"completed": 5, "missed": 3}},
            10,
            7,
        )
        assert explanation == "Your plan was adjusted due to missed tasks."
