from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional, TypedDict, Dict, Any

from langgraph.graph import StateGraph, END

from goals.models.goal_models import Goal
from goals.models.task_models import Task
from goals.ai.llm_service import generate_tasks_llm, TaskGenerationContext
from goals.integrations.web_search_service import gather_research


class GoalCreationState(TypedDict, total=False):
    """State for the goal creation workflow.

    This is kept simple and per-request only; we don't persist the graph state.
    """

    # Input fields
    user_id: int
    goal_title: str
    category: str
    start_date: date
    end_date: date
    notes: Optional[str]

    # Internal / derived fields
    goal_id: int
    date_chunks: List[Dict[str, date]]  # [{"start": date, "end": date}, ...]
    current_chunk_index: int
    research_context: str
    tasks: List[Dict[str, Any]]  # raw task dicts from LLM


def _create_goal_node(db):
    """Minimal implementation for create_goal node."""

    def node(state: GoalCreationState) -> GoalCreationState:
        goal = Goal(
            user_id=state["user_id"],
            title=state["goal_title"],
            category=state.get("category"),
            notes=state.get("notes"),
            start_date=state["start_date"],
            end_date=state["end_date"],
        )

        db.add(goal)
        db.commit()
        if hasattr(db, "refresh"):
            db.refresh(goal)

        return {"goal_id": goal.id}

    return node


def _gather_research_node(state: GoalCreationState) -> GoalCreationState:
    """Gather web research once for the entire goal."""

    print(f"\n Researching: {state['goal_title']} [{state['category']}]")
    research_context = gather_research(
        state["goal_title"],
        state["category"],
        state.get("notes"),
    )
    print(f"\n Research gathered ({len(research_context)} chars)")
    return {"research_context": research_context}


def _generate_tasks_node(state: GoalCreationState) -> GoalCreationState:
    """Generate tasks for the current date chunk via LLM."""

    idx = state.get("current_chunk_index", 0)
    chunks = state.get("date_chunks") or []
    if idx >= len(chunks):
        return {}

    chunk = chunks[idx]
    context = TaskGenerationContext(
        goal=state["goal_title"],
        category=state["category"],
        start_date=chunk["start"],
        end_date=chunk["end"],
        notes=state.get("notes"),
        research_context=state.get("research_context"),
    )
    tasks = generate_tasks_llm(context)

    existing_tasks = state.get("tasks") or []
    return {
        "tasks": existing_tasks + tasks,
        "current_chunk_index": idx + 1,
    }


def _persist_tasks_node(db):
    """Persist all generated tasks to the database."""

    def node(state: GoalCreationState) -> GoalCreationState:
        goal_id = state["goal_id"]
        tasks = state.get("tasks") or []

        print(f"\n Persisting {len(tasks)} tasks to goal {goal_id}")

        for t in tasks:
            task = Task(
                goal_id=goal_id,
                title=t["title"],
                due_date=t["date"],
            )
            db.add(task)

        db.commit()
        return {}

    return node


def _should_continue_chunks(state: GoalCreationState) -> str:
    """Control whether we keep generating tasks for more chunks."""

    idx = state.get("current_chunk_index", 0)
    chunks = state.get("date_chunks") or []
    if idx < len(chunks):
        return "more"
    return "done"


def build_goal_creation_graph(db):
    """Build the LangGraph workflow for goal creation."""

    workflow = StateGraph(GoalCreationState)

    # Nodes
    workflow.add_node("create_goal", _create_goal_node(db))
    workflow.add_node("gather_research", _gather_research_node)
    workflow.add_node("generate_tasks", _generate_tasks_node)
    workflow.add_node("persist_tasks", _persist_tasks_node(db))

    # Edges
    workflow.set_entry_point("create_goal")
    workflow.add_edge("create_goal", "gather_research")
    next_nodes = {
        "more": "generate_tasks",
        "done": "persist_tasks",
    }
    workflow.add_conditional_edges(
        "generate_tasks",
        _should_continue_chunks,
        next_nodes,
    )
    workflow.add_edge("gather_research", "generate_tasks")
    workflow.add_edge("persist_tasks", END)

    return workflow.compile()


def run_goal_creation_workflow(db, goal_data):
    """Public entrypoint used by services.

    Mirrors the behavior of the previous create_goal_with_tasks function,
    but runs it as a LangGraph workflow and returns the created Goal.
    """

    category_value = goal_data.category
    if hasattr(category_value, "value"):
        category_value = category_value.value

    graph = build_goal_creation_graph(db)

    initial_state: GoalCreationState = {
        "user_id": goal_data.user_id,
        "goal_title": goal_data.goal,
        "category": category_value,
        "start_date": goal_data.start_date,
        "end_date": goal_data.end_date,
        "notes": goal_data.notes,
        "tasks": [],
    }

    final_state = graph.invoke(initial_state)

    # Reload and return the goal from DB using the id recorded in the state
    goal_id = final_state["goal_id"]
    goal_query = db.query(Goal)
    goal = goal_query.get(goal_id)
    return goal
