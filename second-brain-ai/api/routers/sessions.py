"""
Session management — PostgreSQL + persistent ChromaDB.
Sessions survive backend restarts. Users only see their own sessions.
"""
import logging
import tempfile
import os
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List

from api.models.schemas import SessionResponse, SessionListResponse
from api.dependencies import CurrentUser
from src.db.vector_store import PersistentChromaStore, register_store
from src.db.session_store import (
    save_session, list_sessions, get_session,
    delete_session, load_chat_history, update_session_chroma_path,
)
from src.utils.retry import validate_file_upload, validate_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _fmt(s: dict) -> SessionResponse:
    fn = s["file_names"]
    if isinstance(fn, str):
        fn = json.loads(fn)
    return SessionResponse(
        id=s["id"],
        name=s["name"],
        created_at=s.get("created_at", datetime.utcnow().isoformat()),
        file_names=fn,
        chunk_count=s.get("chunk_count", 0),
    )


@router.get("", response_model=SessionListResponse, summary="List all sessions for current user")
async def list_all_sessions(current_user: CurrentUser) -> SessionListResponse:
    sessions = list_sessions(user_id=current_user["id"])
    return SessionListResponse(sessions=[_fmt(s) for s in sessions], total=len(sessions))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a session")
async def remove_session(session_id: int, current_user: CurrentUser):
    session = get_session(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    delete_session(session_id, current_user["id"])
    logger.info("Session deleted: id=%d user=%s", session_id, current_user["username"])


@router.post(
    "/{session_id}/index",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index files. Use session_id=0 to create a new session.",
)
async def index_files(
    session_id: int,
    current_user: CurrentUser,
    files: List[UploadFile] = File(default=[]),
    session_name: str = Form(default=""),
    youtube_url: str = Form(default=""),
) -> SessionResponse:
    """
    Upload PDF, PPTX, or TXT files and/or a YouTube URL.
    Data is persisted to disk — sessions survive backend restarts.
    """
    if not files and not youtube_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one file or a YouTube URL.",
        )

    all_docs = []
    file_names = []

    # Process uploaded files
    for file in files:
        content = await file.read()
        filename = file.filename or "unknown"
        validate_file_upload(filename, len(content))
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            class _FW:
                def __init__(self, n, p, sz):
                    self.name = n
                    self._path = p
                    self.size = sz
                def read(self):
                    with open(self._path, "rb") as f:
                        return f.read()

            from src.ingestion.loader import load_documents
            all_docs.extend(load_documents([_FW(filename, tmp_path, len(content))]))
            file_names.append(filename)
        finally:
            os.unlink(tmp_path)

    # Process YouTube URL
    if youtube_url.strip():
        validate_youtube_url(youtube_url.strip())
        from src.features.youtube_loader import fetch_transcript, get_video_title
        all_docs.extend(fetch_transcript(youtube_url.strip()))
        file_names.append(f"YouTube: {get_video_title(youtube_url.strip())}")

    if not all_docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No content could be extracted from the provided files.",
        )

    # Save to PostgreSQL first to get real session ID
    name = session_name.strip() or f"Session ({len(file_names)} files)"
    sid = save_session(
        name=name,
        file_names=file_names,
        chunk_count=len(all_docs),
        user_id=current_user["id"],
    )

    # Index into persistent ChromaDB using real session ID
    store = PersistentChromaStore(session_id=sid)
    store.index(all_docs)
    register_store(sid, store)
    update_session_chroma_path(sid, store.path)

    logger.info("Indexed %d chunks session=%d user=%s", len(all_docs), sid, current_user["username"])

    return SessionResponse(
        id=sid, name=name,
        created_at=datetime.utcnow().isoformat(),
        file_names=file_names, chunk_count=len(all_docs),
    )


@router.get("/{session_id}/history", summary="Get chat history for a session")
async def get_history(session_id: int, current_user: CurrentUser) -> dict:
    session = get_session(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    history = load_chat_history(session_id)
    return {"history": history, "session_id": session_id, "total": len(history)}