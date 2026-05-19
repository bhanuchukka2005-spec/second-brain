"""SQLite persistence for sessions, chat history, flashcards, quiz scores."""
import sqlite3
import json
import os
from datetime import datetime
from typing import List

DB_PATH = os.getenv("DB_PATH", "data/sessions.db")


def _get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            file_names TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            topic TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            topic TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
    """)
    conn.commit()
    conn.close()


def save_session(name: str, file_names: List[str], chunk_count: int) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO sessions (name, created_at, file_names, chunk_count) VALUES (?, ?, ?, ?)",
        (name, datetime.now().isoformat(), json.dumps(file_names), chunk_count)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def list_sessions() -> List[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_session(session_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM flashcards WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM quiz_scores WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_chat_message(session_id: int, role: str, content: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def load_chat_history(session_id: int) -> List[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_flashcards(session_id: int, cards: List[dict], topic: str = ""):
    conn = _get_conn()
    for card in cards:
        conn.execute(
            "INSERT INTO flashcards (session_id, front, back, topic, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, card["front"], card["back"], topic, datetime.now().isoformat())
        )
    conn.commit()
    conn.close()


def load_flashcards(session_id: int) -> List[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT front, back, topic FROM flashcards WHERE session_id = ? ORDER BY created_at DESC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_quiz_score(session_id: int, score: int, total: int, topic: str = ""):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO quiz_scores (session_id, score, total, topic, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session_id, score, total, topic, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def load_quiz_scores(session_id: int) -> List[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT score, total, topic, timestamp FROM quiz_scores WHERE session_id = ? ORDER BY timestamp DESC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
