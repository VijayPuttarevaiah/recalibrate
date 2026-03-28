import json
import os
import httpx
from exceptions.llm_exceptions import LLMClientError
from utils.goal_category_prompt_builder import build_goal_category_prompt
from utils.logging_config import LogManager

logger = LogManager.get_logger()


class LLMClient:
    def __init__(self, timeout_seconds: float = 12.0):
        # Use OpenRouter instead of Google
        self.provider = "openrouter"
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        # Model selection
        configured_model = os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
        self.model = configured_model

        # OpenRouter base URL
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout_seconds = timeout_seconds

    def _call_generate_content(self, model_name: str, payload: dict) -> tuple[int, dict]:
        url = f"{self.base_url}/chat/completions"

        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    # ADD THESE TWO LINES BELOW
                    "HTTP-Referer": "http://localhost:8000", 
                    "X-Title": "Adaptive Goal Planner",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            logger.warning(f"LLM API request failed: {exc}")
            raise LLMClientError(
                "Unable to connect to LLM service.",
                status_code=503,
                error_code="llm_connection_error",
                retryable=True,
            ) from exc

        if response.status_code != 200:
            logger.warning(f"LLM API error: {response.status_code}")
            raise LLMClientError(
                f"LLM upstream returned HTTP {response.status_code}.",
                status_code=response.status_code,
                error_code="llm_upstream_error",
                retryable=response.status_code >= 500,
            )

        try:
            body = response.json()
        except ValueError as exc:
            logger.warning("LLM response parsing failed: invalid JSON body")
            raise LLMClientError(
                "LLM returned an invalid JSON response.",
                status_code=502,
                error_code="llm_invalid_response",
                retryable=True,
            ) from exc

        return response.status_code, body

    def analyze_goal(
        self,
        goal_text: str,
        categories: list[str],
        start_date=None,
        end_date=None,
        note: str | None = None,
    ) -> dict:
        if not self.api_key:
            logger.warning("LLM API key missing")
            raise LLMClientError(
                "LLM API key is missing in server configuration.",
                status_code=500,
                error_code="llm_config_error",
                retryable=False,
            )

        prompt = build_goal_category_prompt(categories)
        user_payload = {
            "goal_text": goal_text,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
            "note": note,
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nInput JSON:\n{json.dumps(user_payload)}",
                }
            ],
            "temperature": 0,
        }

        logger.info(f"DEBUG: Requesting model -> '{self.model}'")

        # Only one model needed
        try:
            _, body = self._call_generate_content(self.model, payload)
        except LLMClientError:
            raise

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning(f"LLM response parsing failed: {exc}")
            raise LLMClientError(
                "LLM response format is invalid.",
                status_code=502,
                error_code="llm_invalid_response",
                retryable=True,
            ) from exc

        parsed = self._parse_json(content)
        if not parsed:
            raise LLMClientError(
                "LLM response JSON is invalid or empty.",
                status_code=502,
                error_code="llm_invalid_response",
                retryable=True,
            )

        return parsed

    def _parse_json(self, content: str | None) -> dict | None:
        if not content:
            return None

        text = content.strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start : end + 1])
                    return parsed if isinstance(parsed, dict) else None
                except json.JSONDecodeError:
                    logger.warning("LLM response is not valid JSON")
                    return None

            logger.warning("LLM response is not valid JSON")
            return None

    def ping(self) -> None:
        if not self.api_key:
            raise LLMClientError(
                "LLM API key is missing in server configuration.",
                status_code=500,
                error_code="llm_config_error",
                retryable=False,
            )

        try:
            response = httpx.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise LLMClientError(
                "Unable to connect to LLM service.",
                status_code=503,
                error_code="llm_connection_error",
                retryable=True,
            ) from exc

        if response.status_code != 200:
            raise LLMClientError(
                f"LLM upstream returned HTTP {response.status_code}.",
                status_code=502,
                error_code="llm_upstream_error",
                retryable=response.status_code >= 500,
            )
