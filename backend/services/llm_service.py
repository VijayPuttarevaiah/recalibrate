import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"  # free model


def build_prompt(goal, category, start_date, end_date, notes=None):
    return f"""
You are an expert productivity planner.

Goal: {goal}
Category: {category}
Start Date: {start_date}
End Date: {end_date}
Notes: {notes or "None"}

Generate realistic DAILY tasks.

Rules:
- One task per day
- Tasks must be practical
- Return ONLY valid JSON
- No markdown
- No explanation

Format:
[
  {{"title": "Task name", "date": "YYYY-MM-DD"}}
]
"""


import re


def extract_json(text: str):
    """
    Extract first JSON array from text.
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return match.group(0)
    return None


def generate_tasks_llm(goal, category, start_date, end_date, notes=None):
    prompt = build_prompt(goal, category, start_date, end_date, notes)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You must return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        print("RESPONSE IS : ",response)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        print("\nRAW LLM RESPONSE:\n", content)

        # Remove markdown if present
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        json_part = extract_json(content)

        if not json_part:
            raise ValueError("No JSON array found in response")

        tasks = json.loads(json_part)

        # Validate structure
        if not isinstance(tasks, list):
            raise ValueError("LLM did not return a list")

        for t in tasks:
            if "title" not in t or "date" not in t:
                raise ValueError("Invalid task structure")

        return tasks

    except Exception as e:
        print("OpenRouter error:", e)
        return []
