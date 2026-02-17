import json
import os
import httpx
from exceptions.llm_exceptions import LLMClientError
from utils.goal_category_prompt_builder import build_goal_category_prompt
from utils.logging_config import LogManager

logger = LogManager.get_logger()


class LLMClient:
    def __init__(self, timeout_seconds: float = 12.0):
        self.provider = "google"
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOAL_CATEGORY_LLM_API_KEY")

        configured_model = os.getenv("GOAL_CATEGORY_LLM_MODEL") or os.getenv("LLM_MODEL") or "gemini-2.0-flash"
        self.model = self._normalize_model_name(configured_model)

        configured_base_url = os.getenv("GOAL_CATEGORY_LLM_BASE_URL") or os.getenv("LLM_BASE_URL") or ""
        if "generativelanguage.googleapis.com" in configured_base_url:
            self.base_url = configured_base_url.rstrip("/")
        else:
            # Avoid accidental OpenRouter/other base URLs for Google generateContent API.
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout_seconds = timeout_seconds

    def _normalize_model_name(self, model_name: str) -> str:
        normalized = model_name.strip()
        if normalized.startswith("models/"):
            normalized = normalized.split("models/", 1)[1]
        return normalized

    def _call_generate_content(self, model_name: str, payload: dict) -> tuple[int, dict]:
        normalized_model = self._normalize_model_name(model_name)
        url = f"{self.base_url}/models/{normalized_model}:generateContent?key={self.api_key}"
        try:
            response = httpx.post(
                url,
                headers={"Content-Type": "application/json"},
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
            message = f"LLM upstream returned HTTP {response.status_code}."
            retryable = response.status_code >= 500
            status_code = 502
            error_code = "llm_upstream_error"
            try:
                error_body = response.json()
                upstream_message = error_body.get("error", {}).get("message")
                if upstream_message:
                    message = upstream_message
                    lowered = upstream_message.lower()
                    if "quota" in lowered or "rate limit" in lowered or "rate-limits" in lowered:
                        error_code = "llm_quota_exceeded"
                        status_code = 429
                        retryable = True
                    elif "not found" in lowered or "not supported" in lowered:
                        error_code = "llm_model_not_found"
                        status_code = 502
                        retryable = False
            except ValueError:
                pass
            raise LLMClientError(
                message,
                status_code=status_code,
                error_code=error_code,
                retryable=retryable,
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
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{prompt}\n\nInput JSON:\n{json.dumps(user_payload)}"}],
                }
            ],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }

        # Retry with known supported variants if model selection is wrong/unavailable.
        candidate_models: list[str] = []
        for candidate in [self.model, "gemini-2.0-flash", "gemini-2.0-flash-lite"]:
            normalized = self._normalize_model_name(candidate)
            if normalized not in candidate_models:
                candidate_models.append(normalized)

        last_http_error: LLMClientError | None = None
        for model_name in candidate_models:
            try:
                _, body = self._call_generate_content(model_name, payload)
                break
            except LLMClientError as exc:
                if exc.error_code == "llm_model_not_found":
                    last_http_error = exc
                    continue
                raise
        else:
            if last_http_error:
                raise last_http_error
            raise LLMClientError("LLM request failed.", status_code=502, error_code="llm_upstream_error")

        try:
            parts = body["candidates"][0]["content"]["parts"]
            content = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
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
                f"{self.base_url}/models?key={self.api_key}",
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
