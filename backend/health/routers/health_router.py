from fastapi import APIRouter, HTTPException
from exceptions.llm_exceptions import LLMClientError
from clients.llm_client import LLMClient
from core.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()


@router.get("/health/goal_category_llm")
def goal_category_llm_health_check():
    client = LLMClient()
    try:
        client.ping()
    except LLMClientError as exc:
        logger.warning(f"Goal category LLM health check failed: {exc.error_code}")
        raise HTTPException(
            status_code=exc.status_code, detail=exc.to_http_detail()
        ) from exc
    return {
        "status": "ok",
        "provider": client.provider,
        "model": client.model,
    }
