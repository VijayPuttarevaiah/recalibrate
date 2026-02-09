from fastapi import APIRouter, HTTPException
from utils.groq_client import GroqClient
from utils.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()


@router.get("/health/groq")
def groq_health_check():
    client = GroqClient()
    ok, detail = client.ping()
    if not ok:
        logger.warning(f"Groq health check failed: {detail}")
        raise HTTPException(status_code=503, detail=detail)
    return {"status": "ok"}
