# services/llm_service.py
import os
import json
import re
import requests
from services.web_search_service import gather_research

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


def build_prompt(goal, category, start_date, end_date, research_context, notes=None):
    return f"""
You are an expert productivity planner with access to the latest web research.

Goal: {goal}
Category: {category}
Start Date: {start_date}
End Date: {end_date}
Notes: {notes or "None"}

{research_context}

=== INSTRUCTIONS ===

Using the web research above as your PRIMARY source of truth (it contains the latest 
information), combined with your own knowledge, generate realistic DAILY tasks.

PRIORITY ORDER:
1. Web research results (latest, most accurate)
2. Your own training knowledge (fill gaps only)

Category-specific guidance:
- IMMIGRATION: Follow the actual official process steps, deadlines, document requirements 
  found in the research. Map each bureaucratic step to specific dates.
- CAREER: Use real course names, certifications, tools, and industry practices from 
  the research. Include actual skill-building milestones.
- FITNESS: Use evidence-based workout progressions and rest days from the research.
  Include real exercises with proper periodization.

Rules:
- One task per day (every day from start to end)
- Tasks must be sequential and build on each other
- Tasks must be specific and actionable (not vague like "research stuff")
- Include real names of documents, websites, tools, courses when available from research
- Return ONLY valid JSON array, no markdown, no explanation

Format:
[
  {{"title": "Specific actionable task", "date": "YYYY-MM-DD"}}
]
"""


def extract_json(text: str):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def generate_tasks_llm(goal, category, start_date, end_date, notes=None, 
                        research_context=None):
    """Generate tasks using web research + LLM knowledge."""
    
    # If no pre-fetched research, fetch now (fallback)
    if not research_context:
        research_context = gather_research(goal, category, notes)

    prompt = build_prompt(goal, category, start_date, end_date, 
                          research_context, notes)

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
                    "You are a planning assistant. You MUST use the provided web "
                    "research as your primary information source. Return valid JSON only."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        print("\nRAW LLM RESPONSE:\n", content)

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        json_part = extract_json(content)
        if not json_part:
            raise ValueError("No JSON array found in response")

        tasks = json.loads(json_part)
        if not isinstance(tasks, list):
            raise ValueError("LLM did not return a list")

        for t in tasks:
            if "title" not in t or "date" not in t:
                raise ValueError("Invalid task structure")

        return tasks

    except Exception as e:
        print("LLM generation error:", e)
        return []