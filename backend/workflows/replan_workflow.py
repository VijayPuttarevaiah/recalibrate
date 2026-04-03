from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session


from goals.progress.summarizer import format_summary_for_llm
from replan.llm.service import (
    ReplanTaskRequest,
    generate_replan_tasks,
)
from goals.integrations.web_search_service import gather_research


class ReplanState(TypedDict, total=False):
    goal_id: int
    goal_title: str
    category: str
    notes: str
    end_date: date
    today: date
    summary: Dict[str, Any]
    progress_context: str
    research_context: str
    chunks: List[Dict[str, date]]
    current_chunk_index: int
    generated_tasks: List[Dict[str, Any]]
    tasks_deleted: int
    explanation: str
    adjustment_id: int
    result: Dict[str, Any]


def _gather_research_node(state: ReplanState) -> ReplanState:
    """Gather web research context for replanning."""
    research_context = gather_research(
        state["goal_title"],
        state["category"],
        state.get("notes"),
    )
    return {"research_context": research_context}


def gather_research_node(state: ReplanState) -> ReplanState:
    return _gather_research_node(state)


def _generate_tasks_node(state: ReplanState) -> ReplanState:
    """Generate replan tasks for the current chunk via LLM."""
    idx = state.get("current_chunk_index", 0)
    chunks = state.get("chunks") or []
    if idx >= len(chunks):
        return {}

    chunk = chunks[idx]
    request = ReplanTaskRequest(
        goal_title=state["goal_title"],
        category=state["category"],
        start_date=chunk["start"],
        end_date=chunk["end"],
        goal_end_date=state["end_date"],
        notes=state.get("notes"),
        progress_context=state.get("progress_context", ""),
        research_context=state.get("research_context", ""),
    )
    tasks = generate_replan_tasks(request)

    existing_tasks = state.get("generated_tasks") or []
    updated_tasks = existing_tasks + tasks
    next_chunk_index = idx + 1
    return {
        "generated_tasks": updated_tasks,
        "current_chunk_index": next_chunk_index,
    }


def generate_tasks_node(state: ReplanState) -> ReplanState:
    return _generate_tasks_node(state)


def _validate_tasks_node(state: ReplanState) -> ReplanState:
    """Minimal implementation for validate_tasks node."""
    if not state.get("generated_tasks"):
        return {}
    return {}


def _apply_plan_node(db: Session):
    """Minimal implementation for apply_plan node."""

    def node(state: ReplanState) -> ReplanState:
        return {"tasks_deleted": 0}  # Placeholder for tasks deleted

    return node


def _generate_explanation_node(state: ReplanState) -> ReplanState:
    """Minimal implementation for generate_explanation node."""
    return {"explanation": "Placeholder explanation"}


def _log_adjustment_node(db: Session):
    """Minimal implementation for log_adjustment node."""

    def node(state: ReplanState) -> ReplanState:
        return {"adjustment_id": 1}  # Placeholder adjustment ID

    return node


def _finalize_node(state: ReplanState) -> ReplanState:
    """Minimal implementation for finalize node."""
    return {"result": {"adjusted": True}}


def _should_continue_chunks(state: ReplanState) -> str:
    """Control whether we keep generating tasks for more chunks."""
    idx = state.get("current_chunk_index", 0)
    chunks = state.get("chunks") or []
    print(f"_should_continue_chunks: idx={idx}, total_chunks={len(chunks)}")
    if idx < len(chunks):
        print("_should_continue_chunks: returning 'more'")
        return "more"
    print("_should_continue_chunks: returning 'done'")
    return "done"


def should_continue_chunks(state: ReplanState) -> str:
    return _should_continue_chunks(state)


def build_replan_graph(db: Session) -> StateGraph:
    wf = StateGraph(ReplanState)

    wf.add_node("gather_research", _gather_research_node)
    wf.add_node("generate_tasks", _generate_tasks_node)
    wf.add_node("validate_tasks", _validate_tasks_node)
    wf.add_node("apply_plan", _apply_plan_node(db))
    wf.add_node("generate_explanation", _generate_explanation_node)
    wf.add_node("log_adjustment", _log_adjustment_node(db))
    wf.add_node("finalize", _finalize_node)

    wf.set_entry_point("gather_research")
    wf.add_edge("gather_research", "generate_tasks")
    continuation_edges = {
        "more": "generate_tasks",
        "done": "validate_tasks",
    }
    wf.add_conditional_edges(
        "generate_tasks",
        _should_continue_chunks,
        continuation_edges,
    )
    wf.add_edge("validate_tasks", "apply_plan")
    wf.add_edge("apply_plan", "generate_explanation")
    wf.add_edge("generate_explanation", "log_adjustment")
    wf.add_edge("log_adjustment", "finalize")
    wf.add_edge("finalize", END)

    return wf.compile()


def run_replan_workflow(db: Session, goal, summary: dict, today: date):
    graph = build_replan_graph(db)

    # Build 30-day chunks from today to goal end date
    chunks: List[Dict[str, date]] = []
    current_start = today
    while current_start <= goal.end_date:
        current_end = min(current_start + timedelta(days=29), goal.end_date)
        chunks.append({"start": current_start, "end": current_end})
        current_start = current_end + timedelta(days=1)

    progress_context = format_summary_for_llm(summary, goal.title)
    initial_state: ReplanState = {
        "goal_id": goal.id,
        "goal_title": goal.title,
        "category": goal.category,
        "notes": goal.notes,
        "end_date": goal.end_date,
        "today": today,
        "summary": summary,
        "progress_context": progress_context,
        "chunks": chunks,
        "current_chunk_index": 0,
        "generated_tasks": [],
    }

    final_state = graph.invoke(initial_state)
    return final_state["result"]
