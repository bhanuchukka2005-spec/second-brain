"""
Session management endpoints.
GET    /sessions              — list all sessions
DELETE /sessions/{id}         — delete a session
POST   /sessions/{id}/index   — upload and index files (id=0 to create new)
GET    /sessions/{id}/history — get chat history
"""
import logging
import tempfile
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List
import json

from api.models.schemas import SessionResponse, SessionListResponse
from api.dependencies import CurrentUser, register_store
from src.vectorstore.chroma_store import ChromaStore
from src.persistence.session_store import (
    save_session, list_sessions, delete_session, load_chat_history
)
from src.utils.retry import validate_file_upload, validate_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _format_session(s: dict) -> SessionResponse:
    file_names = json.loads(s["file_names"]) if isinstance(s["file_names"], str) else s["file_names"]
    return SessionResponse(
        id=s["id"],
        name=s["name"],
        created_at=s["created_at"],
        file_names=file_names,
        chunk_count=s.get("chunk_count", 0)
    )


@router.get("", response_model=SessionListResponse, summary="List all sessions")
async def list_all_sessions(current_user: CurrentUser) -> SessionListResponse:
    """Returns all saved sessions."""
    sessions = list_sessions()
    formatted = [_format_session(s) for s in sessions]
    return SessionListResponse(sessions=formatted, total=len(formatted))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a session")
async def remove_session(session_id: int, current_user: CurrentUser):
    """Delete a session and all its associated data."""
    delete_session(session_id)
    logger.info("Session deleted: id=%d user=%s", session_id, current_user["username"])


@router.post(
    "/{session_id}/index",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index files. Use session_id=0 to create a new session."
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
    Pass session_id=0 to create a new session.
    After indexing, use the returned session id for chat, MCQs, etc.
    """
    if not files and not youtube_url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one file or a YouTube URL."
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
            # Use a file-like wrapper the loader can handle
            class _FileWrapper:
                def __init__(self, name: str, path: str):
                    self.name = name
                    self._path = path
                    self.size = len(content)

                def read(self) -> bytes:
                    with open(self._path, "rb") as f:
                        return f.read()

            from src.ingestion.loader import load_documents
            docs = load_documents([_FileWrapper(filename, tmp_path)])
            all_docs.extend(docs)
            file_names.append(filename)
        finally:
            os.unlink(tmp_path)

    # Process YouTube URL
    if youtube_url.strip():
        validate_youtube_url(youtube_url.strip())
        from src.features.youtube_loader import fetch_transcript, get_video_title
        yt_docs = fetch_transcript(youtube_url.strip())
        all_docs.extend(yt_docs)
        title = get_video_title(youtube_url.strip())
        file_names.append(f"YouTube: {title}")

    if not all_docs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No content could be extracted from the provided files."
        )

    # Index into ChromaDB
    store = ChromaStore()
    store.index(all_docs)

    # Save to SQLite — always create a new record
    name = session_name.strip() or f"Session ({len(file_names)} files)"
    sid = save_session(name, file_names, len(all_docs))

    # Register store under the real session ID
    register_store(sid, store)

    logger.info(
        "Indexed %d chunks from %d sources: session=%d user=%s",
        len(all_docs), len(file_names), sid, current_user["username"]
    )

    return SessionResponse(
        id=sid,
        name=name,
        created_at=datetime.utcnow().isoformat(),
        file_names=file_names,
        chunk_count=len(all_docs)
    )


@router.get("/{session_id}/history", summary="Get chat history for a session")
async def get_history(session_id: int, current_user: CurrentUser) -> dict:
    """Returns the full chat history for a session."""
    history = load_chat_history(session_id)
    return {"history": history, "session_id": session_id, "total": len(history)}
