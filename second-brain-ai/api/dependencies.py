"""
Shared FastAPI dependencies — updated for PostgreSQL + persistent ChromaDB.
"""
import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.db.user_store import decode_access_token, get_user_by_id
from src.db.vector_store import get_or_load_store, PersistentChromaStore
from src.utils.tracker import WeakTopicTracker
from src.llm.brain import SecondBrain

logger = logging.getLogger(__name__)
security = HTTPBearer()

_brain_registry: dict[str, SecondBrain] = {}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def get_store(session_id: int) -> PersistentChromaStore:
    """
    Get or load a ChromaDB store from disk.
    Works even after backend restart — no re-indexing needed.
    """
    try:
        store = get_or_load_store(session_id)
        if store.count() == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Session {session_id} has no indexed content. "
                    "Please upload and index files first."
                )
            )
        return store
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found: {e}"
        )


def get_brain(
    session_id: int,
    provider: str,
    api_key: str,
    ollama_model: str = "llama3.2",
) -> SecondBrain:
    cache_key = f"{session_id}:{provider}:{api_key[:8] if api_key else 'local'}"
    if cache_key not in _brain_registry:
        store = get_store(session_id)
        tracker = WeakTopicTracker()
        try:
            brain = SecondBrain(
                store=store,
                tracker=tracker,
                provider=provider,
                api_key=api_key,
                ollama_model=ollama_model,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        _brain_registry[cache_key] = brain
        logger.info("Brain created: session=%d provider=%s", session_id, provider)
    return _brain_registry[cache_key]
