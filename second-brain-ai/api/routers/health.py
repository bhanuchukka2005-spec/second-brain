"""Health check endpoint — checks PostgreSQL and Ollama."""
from fastapi import APIRouter
from api.models.schemas import HealthResponse
from src.llm.ollama_client import is_ollama_running
from src.config import config
from src.db.connection import execute_one

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="API health check")
async def health_check() -> HealthResponse:
    """Returns service health. Use this to verify the API is running."""
    try:
        execute_one("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        version=config.app_version,
        ollama_available=is_ollama_running(),
        database=db_status,
    )