"""Health check endpoints."""
from fastapi import APIRouter
from api.models.schemas import HealthResponse
from src.llm.ollama_client import is_ollama_running
from src.config import config
import sqlite3

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    Returns service health status.
    Use this to verify the API is running before making other calls.
    """
    # Check DB connectivity
    try:
        conn = sqlite3.connect(config.db_path)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok",
        version=config.app_version,
        ollama_available=is_ollama_running(),
        database=db_status,
    )
