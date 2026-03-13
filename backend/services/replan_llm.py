import json
import os
import re
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


def _call_llm_for_tasks(prompt: str) -> list[dict]:
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
        "temperature": 0.2,
    }

    response = requests.post(
        OPENROUTER_URL, headers=headers, json=payload, timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")

    tasks = json.loads(match.group(0))
    if not isinstance(tasks, list):
        raise ValueError("LLM did not return a list")

    for t in tasks:
        if "title" not in t or "date" not in t:
            raise ValueError("Invalid task structure")

    return tasks


def generate_replan_tasks(
    goal_title: str,
    category: str,
    start_date,
    end_date,
    goal_end_date,
    notes,
    progress_context: str,
    research_context: str,
) -> list[dict]:
    prompt = f"""
You are replanning a goal because the user fell behind schedule.

Goal: {goal_title}
Category: {category}
This chunk: {start_date} → {end_date}
Goal final deadline: {goal_end_date}
Notes: {notes or "None"}

{progress_context}

{research_context}

=== REPLANNING INSTRUCTIONS ===

The user has fallen behind. You must create a REALISTIC adjusted plan:

1. PRIORITIZE critical tasks that were missed — reschedule the most 
   important ones first
2. COMBINE or COMPRESS lower-priority tasks to save time
3. INCREASE intensity slightly where feasible (e.g., 2 topics per day 
   instead of 1) but stay realistic
4. DROP tasks that are nice-to-have but not essential if time is tight
5. Maintain proper sequencing — don't schedule advanced tasks before 
   prerequisites

Rules:
- One task per day (every day from {start_date} to {end_date})
- Tasks must account for the user's actual progress (see completed tasks)
- Tasks must pick up where the user left off, not restart from scratch
- Be specific and actionable
- Return ONLY valid JSON array

Format:
[
  {{"title": "Specific actionable task", "date": "YYYY-MM-DD"}}
]
"""

    return _call_llm_for_tasks(prompt)


def generate_replan_explanation(
    goal_title: str,
    category: str,
    summary: dict,
    new_task_count: int,
    remaining_days: int,
) -> str:
    stats = summary["stats"]
    missed_titles = [t["title"] for t in summary.get("missed_tasks", [])[:10]]

    prompt = f"""
You adjusted a user's goal plan. Explain the changes clearly and briefly.

Goal: {goal_title}
Category: {category}
Progress: {stats['completed']} completed, {stats['missed']} missed
New plan: {new_task_count} tasks over {remaining_days} days remaining

Missed tasks included:
{json.dumps(missed_titles, indent=2)}

Write a 3-5 sentence explanation that covers:
1. What went wrong (how many tasks missed, which area)
2. What changed in the new plan (combined tasks, increased pace, dropped items)
3. Key trade-offs the user should know about

Keep it friendly and motivating, not judgmental. Be specific about 
what was adjusted — don't be vague.

Return ONLY the explanation text, no JSON, no markdown headers.
"""

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
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30,
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
