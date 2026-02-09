import json
import os
import httpx
from config.config import Config
from utils.goal_prompt_builder import build_goal_prompt
from utils.logging_config import LogManager

logger = LogManager.get_logger()


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 12.0,
    ):
        config = Config().config
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or config.get("groq", "api_key", fallback=None)
        self.model = model or os.getenv("GROQ_MODEL") or config.get("groq", "model", fallback="llama-3.3-70b-versatile")
        self.base_url = base_url or os.getenv("GROQ_BASE_URL") or config.get(
            "groq",
            "base_url",
            fallback="https://api.groq.com/openai/v1",
        )
        self.timeout_seconds = timeout_seconds

    def analyze_goal(
        self,
        goal_text: str,
        categories: list[str],
        start_date=None,
        end_date=None,
        note: str | None = None,
    ) -> dict | None:
        if not self.api_key:
            logger.warning("Groq API key missing; skipping LLM analysis")
            return None

        prompt = build_goal_prompt(categories)
        user_payload = {
            "goal_text": goal_text,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "note": note,
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            "temperature": 0,
            "max_tokens": 200,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            logger.warning(f"Groq API request failed: {exc}")
            return None

        if response.status_code != 200:
            logger.warning(f"Groq API error: {response.status_code} - {response.text}")
            return None

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            logger.warning(f"Groq response parsing failed: {exc}")
            return None

        if not content:
            return None

        content = content.strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = content[start : end + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
            logger.warning("Groq response is not valid JSON")
            return None

        return None

    def ping(self) -> tuple[bool, str | None]:
        if not self.api_key:
            return False, "Groq API key missing"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            return False, f"Groq API request failed: {exc}"

        if response.status_code != 200:
            return False, f"Groq API error: {response.status_code}"

        return True, None
