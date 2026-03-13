import pytest
from datetime import date
from unittest.mock import MagicMock
from models.goal_models import Goal
from workflows.goal_creation_workflow import build_goal_creation_graph, _create_goal_node

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


def test_create_goal_node_persists_goal():
    """RED: create_goal should persist a Goal and return its id."""
    db = MagicMock()

    def add_side_effect(goal):
        goal.id = 42

    db.add.side_effect = add_side_effect

    state = {
        "user_id": 1,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "notes": "Test Notes",
    }

    node = _create_goal_node(db)
    result = node(state)

    db.add.assert_called_once()
    db.commit.assert_called_once()

    created_goal = db.add.call_args.args[0]
    assert isinstance(created_goal, Goal)
    assert created_goal.user_id == 1
    assert created_goal.title == "Test Goal"
    assert created_goal.category == "Health"
    assert created_goal.notes == "Test Notes"
    assert created_goal.start_date == date(2026, 3, 1)
    assert created_goal.end_date == date(2026, 3, 31)
    assert result["goal_id"] == 42