import pytest
from unittest.mock import MagicMock
from workflows.replan_workflow import build_replan_graph

def test_minimal_gather_research_node():
    """Test that the gather_research node initializes correctly."""
    db = MagicMock()
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
    }

    graph = build_replan_graph(db)
    result = graph.invoke(state)
    assert "research_context" in result, "Research context should be in the result."

def test_minimal_generate_tasks_node():
    """Test that the generate_tasks node initializes correctly."""
    db = MagicMock()
    state = {
        "goal_title": "Test Goal",
        "category": "Health",
        "chunks": [{"start": "2026-03-01", "end": "2026-03-31"}],
        "current_chunk_index": 0,
        "progress_context": "Progress Context",
    }

    graph = build_replan_graph(db)
    result = graph.invoke(state)
    assert "generated_tasks" in result, "Generated tasks should be in the result."

def test_minimal_workflow_execution():
    """Test that the replan workflow executes minimally."""
    db = MagicMock()
    state = {
        "goal_id": 1,
        "goal_title": "Test Goal",
        "category": "Health",
        "notes": "Test Notes",
        "end_date": "2026-03-31",
        "today": "2026-03-01",
        "summary": {"stats": {"missed": 0, "completed": 0, "total_tasks": 0}},
        "chunks": [{"start": "2026-03-01", "end": "2026-03-31"}],
        "current_chunk_index": 0,
        "progress_context": "Progress Context",
    }

    graph = build_replan_graph(db)
    result = graph.invoke(state)
    assert "result" in result, "Result should be in the final state."