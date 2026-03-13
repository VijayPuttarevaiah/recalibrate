import pytest
from unittest.mock import patch, MagicMock
from services.replan_llm import (
    _call_llm_for_tasks,
    generate_replan_tasks,
    generate_replan_explanation,
)

def test_call_llm_for_tasks_valid_response():
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

    import services.replan_llm as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            tasks = _call_llm_for_tasks("test prompt")
            assert len(tasks) == 2
            assert tasks[0]["title"] == "Task 1"
            assert tasks[1]["date"] == "2026-03-08"

def test_call_llm_for_tasks_invalid_response():
    """Test _call_llm_for_tasks with an invalid LLM response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Invalid JSON"
                }
            }
        ]
    }

    import services.replan_llm as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", "test-key"):
        with patch("requests.post", return_value=mock_response):
            with pytest.raises(ValueError, match="No JSON array found in LLM response"):
                _call_llm_for_tasks("test prompt")


def test_call_llm_for_tasks_missing_api_key():
    """RED: Fail fast when OPENROUTER_API_KEY is missing."""
    import services.replan_llm as replan_llm

    with patch.object(replan_llm, "OPENROUTER_API_KEY", ""):
        with patch("requests.post") as mock_post:
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                replan_llm._call_llm_for_tasks("test prompt")
            mock_post.assert_not_called()

def test_generate_replan_tasks():
    """Test generate_replan_tasks with mocked _call_llm_for_tasks."""
    with patch("services.replan_llm._call_llm_for_tasks", return_value=[
        {"title": "Task 1", "date": "2026-03-07"}
    ]):
        tasks = generate_replan_tasks(
            "Goal Title",
            "Category",
            "2026-03-01",
            "2026-03-10",
            "2026-03-15",
            "Notes",
            "Progress Context",
            "Research Context",
        )
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Task 1"

def test_generate_replan_explanation():
    """Test generate_replan_explanation with mocked LLM response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Your plan was adjusted due to missed tasks."
                }
            }
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