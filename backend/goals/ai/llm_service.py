# services/llm_service.py
import os
import json
import re
import requests
from dataclasses import dataclass
from goals.integrations.web_search_service import gather_research

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT = 60

@dataclass
class TaskGenerationContext:
    goal: str
    category: str
    start_date: str
    end_date: str
    research_context: str | None = None
    notes: str | None = None

def build_prompt(context: TaskGenerationContext) -> str:
        lines = [
                "You are an expert productivity planner with access to the latest web research.",
                "",
                f"Goal: {context.goal}",
                f"Category: {context.category}",
                f"Start Date: {context.start_date}",
                f"End Date: {context.end_date}",
                f"Notes: {context.notes or 'None'}",
                "",
                context.research_context or "",
                "",
                "=== INSTRUCTIONS ===",
                "",
                "Using the web research above as your PRIMARY source of truth (it contains the latest",
                "information), combined with your own knowledge, generate realistic DAILY tasks.",
                "",
                "PRIORITY ORDER:",
                "1. Web research results (latest, most accurate)",
                "2. Your own training knowledge (fill gaps only)",
                "",
                "Category-specific guidance:",
                "- IMMIGRATION: Follow the actual official process steps, deadlines, document requirements",
                "  found in the research. Map each bureaucratic step to specific dates.",
                "- CAREER: Use real course names, certifications, tools, and industry practices from",
                "  the research. Include actual skill-building milestones.",
                "- FITNESS: Use evidence-based workout progressions and rest days from the research.",
                "  Include real exercises with proper periodization.",
                "",
                "Rules:",
                "- One task per day (every day from start to end)",
                "- Tasks must be sequential and build on each other",
                "- Tasks must be specific and actionable (not vague like 'research stuff')",
                "- Include real names of documents, websites, tools, courses when available from research",
                "- Return ONLY valid JSON array, no markdown, no explanation",
                "",
                "Format:",
                "[",
                "  {\"title\": \"Specific actionable task\", \"date\": \"YYYY-MM-DD\"}",
                "]",
        ]
        return "\n".join(lines)


def extract_json(text: str):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return None

def _strip_code_fences(content: str) -> str:
    if not content.startswith("```"):
        return content
    return content.replace("```json", "").replace("```", "").strip()


def _validate_task_list(tasks: list) -> None:
    if not isinstance(tasks, list):
        raise ValueError("LLM did not return a list")
    for task in tasks:
        if "title" not in task or "date" not in task:
            raise ValueError("Invalid task structure")


def _parse_llm_json_response(content: str) -> list:
    content = _strip_code_fences(content)

    json_part = extract_json(content)
    if not json_part:
        raise ValueError("No JSON array found in response")

    tasks = json.loads(json_part)
    _validate_task_list(tasks)
    return tasks

def generate_tasks_llm(context: TaskGenerationContext):
    """Generate tasks using web research + LLM knowledge."""
    
    # If no pre-fetched research, fetch now (fallback)
    if not context.research_context:
        context.research_context = gather_research(
            context.goal,
            context.category,
            context.notes,
        )

    prompt = build_prompt(context)

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
        "temperature": DEFAULT_TEMPERATURE,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        print("\nRAW LLM RESPONSE:\n", content)

        return _parse_llm_json_response(content)

    except Exception as e:
        print("LLM generation error:", e)
        return []