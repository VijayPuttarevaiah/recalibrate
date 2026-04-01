import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from goals.models.goal_models import Goal
from goals.ai.llm_service import TaskGenerationContext
from workflows.goal_creation_workflow import (
    build_goal_creation_graph,
    _create_goal_node,
    _generate_tasks_node,
)

DEFAULT_USER_ID = 1
CREATED_GOAL_ID = 42
CHUNK_INDEX_START = 0
CHUNK_INDEX_NEXT = 1

def test_minimal_create_goal_node():
    """Test that the create_goal node initializes correctly."""
    db = MagicMock()
    state = {
        "user_id": DEFAULT_USER_ID,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "notes": "Test Notes",
        "date_chunks": [{"start": date(2026, 3, 1), "end": date(2026, 3, 10)}],
        "current_chunk_index": CHUNK_INDEX_START,
        "tasks": [],
    }

    graph = build_goal_creation_graph(db)
    with patch(
        "workflows.goal_creation_workflow.gather_research",
        return_value="Research Context",
    ), patch(
        "workflows.goal_creation_workflow.generate_tasks_llm",
        return_value=[],
    ):
        result = graph.invoke(state)
    assert "goal_id" in result, "Goal ID should be in the result."

def test_minimal_generate_tasks_node():
    """Test that the generate_tasks node initializes correctly."""
    db = MagicMock()
    state = {
        "user_id": DEFAULT_USER_ID,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "notes": "Test Notes",
        "date_chunks": [{"start": date(2026, 3, 1), "end": date(2026, 3, 10)}],
        "current_chunk_index": CHUNK_INDEX_START,
        "tasks": [],
    }

    graph = build_goal_creation_graph(db)
    with patch(
        "workflows.goal_creation_workflow.gather_research",
        return_value="Research Context",
    ), patch(
        "workflows.goal_creation_workflow.generate_tasks_llm",
        return_value=[{"title": "Task 1", "date": "2026-03-01"}],
    ):
        result = graph.invoke(state)
    assert "tasks" in result, "Tasks should be in the result."

def test_minimal_workflow_execution():
    """Test that the workflow executes minimally."""
    db = MagicMock()
    state = {
        "user_id": DEFAULT_USER_ID,
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "notes": "Test Notes",
        "date_chunks": [{"start": date(2026, 3, 1), "end": date(2026, 3, 10)}],
        "current_chunk_index": CHUNK_INDEX_START,
        "tasks": [],
    }

    graph = build_goal_creation_graph(db)
    with patch(
        "workflows.goal_creation_workflow.gather_research",
        return_value="Research Context",
    ), patch(
        "workflows.goal_creation_workflow.generate_tasks_llm",
        return_value=[{"title": "Task 1", "date": "2026-03-01"}],
    ):
        result = graph.invoke(state)
    assert "goal_id" in result, "Goal ID should be in the result."
    assert "tasks" in result, "Tasks should be in the result."


def test_create_goal_node_persists_goal():
    """RED: create_goal should persist a Goal and return its id."""
    db = MagicMock()

    def add_side_effect(goal):
        goal.id = CREATED_GOAL_ID

    db.add.side_effect = add_side_effect

    state = {
        "user_id": DEFAULT_USER_ID,
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
    assert created_goal.user_id == DEFAULT_USER_ID
    assert created_goal.title == "Test Goal"
    assert created_goal.category == "Health"
    assert created_goal.notes == "Test Notes"
    assert created_goal.start_date == date(2026, 3, 1)
    assert created_goal.end_date == date(2026, 3, 31)
    assert result["goal_id"] == CREATED_GOAL_ID


def test_generate_tasks_node_calls_llm_and_advances():
    """RED: generate_tasks should call LLM and increment chunk index."""
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 3, 31),
        "notes": "Test Notes",
        "research_context": "Research Context",
        "date_chunks": [
            {"start": date(2026, 3, 1), "end": date(2026, 3, 10)}
        ],
        "current_chunk_index": CHUNK_INDEX_START,
        "tasks": [],
    }

    returned_tasks = [{"title": "Task 1", "date": "2026-03-01"}]

    with patch(
        "workflows.goal_creation_workflow.generate_tasks_llm",
        return_value=returned_tasks,
    ) as mock_generate:
        result = _generate_tasks_node(state)

    mock_generate.assert_called_once()
    context = mock_generate.call_args.args[0]
    assert isinstance(context, TaskGenerationContext)
    assert context.goal == "Test Goal"
    assert context.category == "Health"
    assert context.start_date == date(2026, 3, 1)
    assert context.end_date == date(2026, 3, 10)
    assert context.notes == "Test Notes"
    assert context.research_context == "Research Context"
    assert result["tasks"] == returned_tasks
    assert result["current_chunk_index"] == CHUNK_INDEX_NEXT