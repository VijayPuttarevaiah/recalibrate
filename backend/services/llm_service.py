# services/llm_service.py
import os
import json
import re
import requests
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from services.web_search_service import gather_research

# Configuration Constants
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"
LLM_TEMPERATURE = 0.2

# Prompt Template
TASK_GENERATION_PROMPT_TEMPLATE = """You are an expert productivity planner with access to the latest web research.

Goal: {goal}
Category: {category}
Start Date: {start_date}
End Date: {end_date}
Notes: {notes}

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
  {"title": "Specific actionable task", "date": "YYYY-MM-DD"}
]
"""


@dataclass
class TaskGenerationRequest:
    """Encapsulates parameters for task generation."""
    goal: str
    category: str
    start_date: str
    end_date: str
    research_context: str
    notes: Optional[str] = None


def build_prompt(request: TaskGenerationRequest) -> str:
    """Build LLM prompt from task generation request. (Reduced from 6 to 1 parameter)"""
    return TASK_GENERATION_PROMPT_TEMPLATE.format(
        goal=request.goal,
        category=request.category,
        start_date=request.start_date,
        end_date=request.end_date,
        notes=request.notes or "None",
        research_context=request.research_context
    )


def extract_json(text: str) -> Optional[str]:
    """Extract JSON array from text, handling markdown code blocks."""
    # Remove markdown code block markers if present
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    
    # Find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group(0) if match else None


def _validate_task(task: Dict[str, Any]) -> bool:
    """Validate a single task has required fields."""
    return "title" in task and "date" in task


def _validate_tasks(tasks: Any) -> List[Dict[str, str]]:
    """Validate response is a list of properly formatted tasks.
    
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(tasks, list):
        raise ValueError("LLM did not return a list")
    
    if not all(_validate_task(task) for task in tasks):
        raise ValueError("Invalid task structure - missing 'title' or 'date'")
    
    return tasks


def _process_llm_response(raw_response: str) -> List[Dict[str, str]]:
    """Extract and validate JSON from LLM response.
    
    Reduces cyclomatic complexity by isolating JSON processing logic.
    
    Args:
        raw_response: Raw text from LLM
        
    Returns:
        List of validated task dictionaries
        
    Raises:
        ValueError: If JSON extraction or validation fails
    """
    print("\nRAW LLM RESPONSE:\n", raw_response)
    
    json_part = extract_json(raw_response)
    if not json_part:
        raise ValueError("No JSON array found in response")
    
    tasks = json.loads(json_part)
    return _validate_tasks(tasks)


def _make_llm_request(request: TaskGenerationRequest) -> str:
    """Make HTTP request to OpenRouter API and return response content.
    
    Reduces cyclomatic complexity by isolating HTTP logic.
    
    Args:
        request: Task generation parameters
        
    Returns:
        Response content string
        
    Raises:
        requests.RequestException: If API call fails
    """
    prompt = build_prompt(request)
    
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
        "temperature": LLM_TEMPERATURE,
    }

    response = requests.post(
        OPENROUTER_URL, headers=headers, json=payload, timeout=60
    )
    response.raise_for_status()
    
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_tasks_llm(goal: str, category: str, start_date: str, end_date: str, 
                       notes: Optional[str] = None, 
                       research_context: Optional[str] = None) -> List[Dict[str, str]]:
    """Generate tasks using web research + LLM knowledge.
    
    Refactored: Now delegates to helper methods for reduced complexity.
    Original CC=8, now simplified to CC=2 by extracting helper methods.
    
    Args:
        goal: The goal to generate tasks for
        category: Goal category (e.g., IMMIGRATION, CAREER, FITNESS)
        start_date: Task start date (YYYY-MM-DD)
        end_date: Task end date (YYYY-MM-DD)
        notes: Optional additional notes
        research_context: Pre-fetched web research. If None, will be fetched.
        
    Returns:
        List of task dictionaries with 'title' and 'date' keys, or empty list on error
    """
    # Fetch research if not provided
    if not research_context:
        research_context = gather_research(goal, category, notes)
    
    # Build request object (single parameter instead of 6)
    request = TaskGenerationRequest(
        goal=goal,
        category=category,
        start_date=start_date,
        end_date=end_date,
        research_context=research_context,
        notes=notes
    )
    
    try:
        # Make API request
        response_content = _make_llm_request(request)
        
        # Process and validate response
        tasks = _process_llm_response(response_content)
        
        return tasks

    except Exception as e:
        print("LLM generation error:", e)
        return []