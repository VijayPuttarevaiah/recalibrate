import pytest
from unittest.mock import MagicMock
from workflows.goal_creation_workflow import build_goal_creation_graph

def test_minimal_create_goal_node():
    """Test that the create_goal node initializes correctly."""
    db = MagicMock()
    state = {
        "user_id": 1,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "notes": "Test Notes",
    }

    graph = build_goal_creation_graph(db)
    result = graph.invoke(state)
    assert "goal_id" in result, "Goal ID should be in the result."

def test_minimal_generate_tasks_node():
    """Test that the generate_tasks node initializes correctly."""
    db = MagicMock()
    state = {
        "user_id": 1,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "notes": "Test Notes",
    }

    graph = build_goal_creation_graph(db)
    result = graph.invoke(state)
    assert "tasks" in result, "Tasks should be in the result."

def test_minimal_workflow_execution():
    """Test that the workflow executes minimally."""
    db = MagicMock()
    state = {
        "user_id": 1,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": "2026-03-01",
        "end_date": "2026-03-31",
        "notes": "Test Notes",
    }

    graph = build_goal_creation_graph(db)
    result = graph.invoke(state)
    assert "goal_id" in result, "Goal ID should be in the result."
    assert "tasks" in result, "Tasks should be in the result."