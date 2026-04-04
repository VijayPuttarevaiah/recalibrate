import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
MAX_MISSED_TITLES_FOR_PROMPT = 10
EXPLANATION_TEMPERATURE = 0.3
TASK_GENERATION_TEMPERATURE = 0.2


def _strip_code_fences(content: str) -> str:
    if not content.startswith("```"):
        return content
    return content.replace("```json", "").replace("```", "").strip()


def _extract_json_array(content: str) -> str:
    match = re.search(r"\[.*?\]", content, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")
    return match.group(0)


def _validate_task_structure(task: dict) -> None:
    if "title" not in task or "date" not in task:
        raise ValueError("Invalid task structure")


def _validate_date_string(date_value: str) -> None:
    if not isinstance(date_value, str):
        raise ValueError("Invalid date format: expected YYYY-MM-DD")
    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Invalid date format: expected YYYY-MM-DD") from exc


def _call_llm_for_tasks(prompt: str) -> list[dict]:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a replanning assistant. Generate adjusted tasks "
                    "based on the user's actual progress. Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": TASK_GENERATION_TEMPERATURE,
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"].strip()
    content = _strip_code_fences(content)

    json_array = _extract_json_array(content)
    tasks = json.loads(json_array)
    if not isinstance(tasks, list):
        raise ValueError("LLM did not return a list")

    for task in tasks:
        _validate_task_structure(task)
        _validate_date_string(task["date"])

    return tasks


def call_llm_for_tasks(prompt: str) -> list[dict]:
    return _call_llm_for_tasks(prompt)


@dataclass(frozen=True)
class ReplanTaskRequest:
    goal_title: str
    category: str
    start_date: str | date
    end_date: str | date
    goal_end_date: str | date
    notes: str | None
    progress_context: str
    research_context: str


def generate_replan_tasks(
    request: ReplanTaskRequest,
) -> list[dict]:
    prompt_lines = [
        "You are replanning a goal because the user fell behind schedule.",
        "",
        f"Goal: {request.goal_title}",
        f"Category: {request.category}",
        f"This chunk: {request.start_date} → {request.end_date}",
        f"Goal final deadline: {request.goal_end_date}",
        f"Notes: {request.notes or 'None'}",
        "",
        request.progress_context,
        "",
        request.research_context,
        "",
        "=== REPLANNING INSTRUCTIONS ===",
        "",
        "The user has fallen behind. You must create a REALISTIC adjusted plan:",
        "",
        "1. PRIORITIZE critical tasks that were missed — reschedule the most",
        "   important ones first",
        "2. COMBINE or COMPRESS lower-priority tasks to save time",
        "3. INCREASE intensity slightly where feasible (e.g., 2 topics per day",
        "   instead of 1) but stay realistic",
        "4. DROP tasks that are nice-to-have but not essential if time is tight",
        "5. Maintain proper sequencing — don't schedule advanced tasks before",
        "   prerequisites",
        "",
        "Rules:",
        "- One task per day (every day from",
        f"  {request.start_date} to {request.end_date})",
        "- Tasks must account for the user's actual progress (see completed tasks)",
        "- Tasks must pick up where the user left off, not restart from scratch",
        "- Be specific and actionable",
        "- Return ONLY valid JSON array",
        "",
        "Format:",
        "[",
        '  {"title": "Specific actionable task", "date": "YYYY-MM-DD"}',
        "]",
    ]
    prompt = "\n".join(prompt_lines)

    return call_llm_for_tasks(prompt)


def generate_replan_explanation(
    goal_title: str,
    category: str,
    summary: dict,
    new_task_count: int,
    remaining_days: int,
) -> str:
    stats = summary["stats"]
    missed_titles = [
        task["title"]
        for task in summary.get("missed_tasks", [])[:MAX_MISSED_TITLES_FOR_PROMPT]
    ]

    prompt_lines = [
        "You adjusted a user's goal plan. Explain the changes clearly and briefly.",
        "",
        f"Goal: {goal_title}",
        f"Category: {category}",
        f"Progress: {stats['completed']} completed, {stats['missed']} missed",
        f"New plan: {new_task_count} tasks over {remaining_days} days remaining",
        "",
        "Missed tasks included:",
        json.dumps(missed_titles, indent=2),
        "",
        "Write a 3-5 sentence explanation that covers:",
        "1. What went wrong (how many tasks missed, which area)",
        "2. What changed in the new plan (combined tasks, increased pace,",
        "   dropped items)",
        "3. Key trade-offs the user should know about",
        "",
        "Keep it friendly and motivating, not judgmental. Be specific about",
        "what was adjusted — don't be vague.",
        "",
        "Return ONLY the explanation text, no JSON, no markdown headers.",
    ]
    prompt = "\n".join(prompt_lines)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a supportive productivity coach. Be concise and specific.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": EXPLANATION_TEMPERATURE,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"Explanation generation error: {exc}")
        return (
            f"Your plan was adjusted because {stats['missed']} tasks were overdue. "
            f"The remaining {new_task_count} tasks have been redistributed across "
            f"{remaining_days} days. Some tasks were combined to catch up."
        )
