"""
PostgreSQL session store.
All operations are user-scoped — users only see their own data.
"""
import logging
import json
from typing import List, Optional
from src.db.connection import execute, execute_one, execute_write, get_conn

logger = logging.getLogger(__name__)


def save_session(name: str, file_names: List[str], chunk_count: int, user_id: int, chroma_path: str = "") -> int:
    sid = execute_write(
        """
        INSERT INTO sessions (user_id, name, file_names, chunk_count, chroma_path)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """,
        (user_id, name, json.dumps(file_names), chunk_count, chroma_path)
    )
    logger.info("Session created: id=%s user_id=%s", sid, user_id)
    return sid


def list_sessions(user_id: int) -> List[dict]:
    rows = execute(
        """
        SELECT id, name, file_names, chunk_count, chroma_path, created_at::text AS created_at
        FROM sessions WHERE user_id = %s ORDER BY created_at DESC
        """,
        (user_id,)
    )
    for r in rows:
        if isinstance(r["file_names"], str):
            r["file_names"] = json.loads(r["file_names"])
    return rows


def get_session(session_id: int, user_id: int) -> Optional[dict]:
    row = execute_one(
        """
        SELECT id, name, file_names, chunk_count, chroma_path, created_at::text AS created_at
        FROM sessions WHERE id = %s AND user_id = %s
        """,
        (session_id, user_id)
    )
    if row and isinstance(row["file_names"], str):
        row["file_names"] = json.loads(row["file_names"])
    return row


def update_session_chroma_path(session_id: int, chroma_path: str) -> None:
    execute_write("UPDATE sessions SET chroma_path = %s WHERE id = %s", (chroma_path, session_id))


def delete_session(session_id: int, user_id: int) -> None:
    execute_write("DELETE FROM sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
    logger.info("Session deleted: id=%s user_id=%s", session_id, user_id)


def save_chat_message(session_id: int, role: str, content: str) -> None:
    execute_write(
        "INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)",
        (session_id, role, content)
    )


def load_chat_history(session_id: int) -> List[dict]:
    return execute(
        "SELECT role, content, created_at::text AS timestamp FROM chat_history WHERE session_id = %s ORDER BY created_at",
        (session_id,)
    )


def save_flashcards(session_id: int, cards: List[dict], topic: str = "") -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for card in cards:
                cur.execute(
                    "INSERT INTO flashcards (session_id, front, back, topic) VALUES (%s, %s, %s, %s)",
                    (session_id, card["front"], card["back"], topic)
                )
    logger.info("Saved %d flashcards for session=%d", len(cards), session_id)


def load_flashcards(session_id: int) -> List[dict]:
    return execute(
        "SELECT front, back, topic FROM flashcards WHERE session_id = %s ORDER BY created_at DESC",
        (session_id,)
    )


def save_quiz_score(session_id: int, score: int, total: int, topic: str = "") -> None:
    execute_write(
        "INSERT INTO quiz_scores (session_id, score, total, topic) VALUES (%s, %s, %s, %s)",
        (session_id, score, total, topic)
    )


def load_quiz_scores(session_id: int) -> List[dict]:
    return execute(
        "SELECT score, total, topic, created_at::text AS timestamp FROM quiz_scores WHERE session_id = %s ORDER BY created_at DESC",
        (session_id,)
    )