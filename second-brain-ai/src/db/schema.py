"""
Database schema for AI Second Brain.
Run automatically on backend startup via init_db().
"""
import logging
from src.db.connection import get_conn

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    username     VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         VARCHAR(200) NOT NULL,
    file_names   JSONB NOT NULL DEFAULT '[]',
    chunk_count  INTEGER DEFAULT 0,
    chroma_path  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS chat_history (
    id         SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id);

CREATE TABLE IF NOT EXISTS flashcards (
    id         SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    front      TEXT NOT NULL,
    back       TEXT NOT NULL,
    topic      VARCHAR(200) DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quiz_scores (
    id         SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    score      INTEGER NOT NULL CHECK (score >= 0),
    total      INTEGER NOT NULL CHECK (total > 0),
    topic      VARCHAR(200) DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_session ON quiz_scores(session_id);
"""


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
        logger.info("PostgreSQL schema initialized successfully")
    except Exception as e:
        logger.error("Schema initialization failed: %s", e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Creating tables in PostgreSQL...")
    init_db()
    print("✅ Done!")