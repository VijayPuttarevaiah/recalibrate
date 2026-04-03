from datetime import date
from unittest.mock import MagicMock, patch
from workflows.replan_workflow import (
    build_replan_graph,
    gather_research_node,
    generate_tasks_node,
)
from replan.services.replan_llm import ReplanTaskRequest

DEFAULT_GOAL_ID = 1
CHUNK_INDEX_START = 0
CHUNK_INDEX_NEXT = 1

def test_minimal_gather_research():
    """Test that the gather_research node initializes correctly."""
    db = MagicMock()
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
    }

    graph = build_replan_graph(db)
    with (
        patch(
            "workflows.replan_workflow.gather_research",
            return_value="Research Context",
        ),
        patch(
            "workflows.replan_workflow.generate_replan_tasks",
            return_value=[],
        ),
    ):
        result = graph.invoke(state)
    assert "research_context" in result, "Research context should be in the result."

def test_minimal_generate_tasks():
    """Test that the generate_tasks node initializes correctly."""
    db = MagicMock()
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "chunks": [{"start": "2026-03-01", "end": "2026-03-31"}],
        "end_date": date(2026, 3, 31),
        "current_chunk_index": CHUNK_INDEX_START,
        "progress_context": "Progress Context",
    }

    graph = build_replan_graph(db)
    with (
        patch(
            "workflows.replan_workflow.gather_research",
            return_value="Research Context",
        ),
        patch(
            "workflows.replan_workflow.generate_replan_tasks",
            return_value=[{"title": "Task 1", "date": "2026-03-01"}],
        ),
    ):
        result = graph.invoke(state)
    assert "generated_tasks" in result, "Generated tasks should be in the result."

def test_minimal_workflow_exec():
    """Test that the replan workflow executes minimally."""
    db = MagicMock()
    state = {
        "goal_id": DEFAULT_GOAL_ID,
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
        "end_date": date(2026, 3, 31),
        "today": date(2026, 3, 1),
        "summary": {"stats": {"missed": 0, "completed": 0, "total_tasks": 0}},
        "chunks": [{"start": "2026-03-01", "end": "2026-03-31"}],
        "current_chunk_index": CHUNK_INDEX_START,
        "progress_context": "Progress Context",
    }

    graph = build_replan_graph(db)
    with (
        patch(
            "workflows.replan_workflow.gather_research",
            return_value="Research Context",
        ),
        patch(
            "workflows.replan_workflow.generate_replan_tasks",
            return_value=[{"title": "Task 1", "date": "2026-03-01"}],
        ),
    ):
        result = graph.invoke(state)
    assert "result" in result, "Result should be in the final state."

def test_gather_research_calls():
    """gather_research node should call web search service."""
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
    }

    with patch(
        "workflows.replan_workflow.gather_research",
        return_value="Research Context",
    ) as mock_research:
        result = gather_research_node(state)

    mock_research.assert_called_once_with("Test Goal", "Health", "Test Notes")
    assert result["research_context"] == "Research Context"

def test_generate_tasks_calls_llm():
    """generate_tasks should call LLM and increment chunk index."""
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
        "end_date": date(2026, 3, 31),
        "chunks": [{"start": date(2026, 3, 1), "end": date(2026, 3, 10)}],
        "current_chunk_index": CHUNK_INDEX_START,
        "progress_context": "Progress Context",
        "research_context": "Research Context",
        "generated_tasks": [],
    }

    returned_tasks = [{"title": "Task A", "date": "2026-03-01"}]

    with patch(
        "workflows.replan_workflow.generate_replan_tasks",
        return_value=returned_tasks,
    ) as mock_generate:
        result = generate_tasks_node(state)

    mock_generate.assert_called_once()
    request = mock_generate.call_args.args[0]
    assert isinstance(request, ReplanTaskRequest)
    assert request.goal_title == "Test Goal"
    assert request.category == "Health"
    assert request.start_date == date(2026, 3, 1)
    assert request.end_date == date(2026, 3, 10)
    assert request.goal_end_date == date(2026, 3, 31)
    assert request.notes == "Test Notes"
    assert request.progress_context == "Progress Context"
    assert request.research_context == "Research Context"
    assert result["generated_tasks"] == returned_tasks
    assert result["current_chunk_index"] == CHUNK_INDEX_NEXT
