"""
Database schema for AI Second Brain.
Run automatically on backend startup via init_db().
"""
import logging
from src.db.connection import get_conn

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
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

# Adds Google OAuth columns (idempotent — safe on fresh or existing databases)
MIGRATION_GOOGLE_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='google_sub'
    ) THEN
        ALTER TABLE users ADD COLUMN google_sub VARCHAR(100) UNIQUE;
        ALTER TABLE users ADD COLUMN email VARCHAR(255);
        ALTER TABLE users ADD COLUMN avatar_url TEXT;
        ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub);
"""

# Adds password-reset token columns (idempotent)
MIGRATION_RESET_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='reset_token'
    ) THEN
        ALTER TABLE users ADD COLUMN reset_token VARCHAR(100);
        ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMPTZ;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_token);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique
    ON users(email) WHERE email IS NOT NULL;
"""


def init_db() -> None:
    """Create all tables, then apply migrations in order. Safe to call repeatedly."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
        logger.info("Base schema ensured")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(MIGRATION_GOOGLE_SQL)
        logger.info("Google OAuth columns ensured")

        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(MIGRATION_RESET_SQL)
        logger.info("Password reset columns ensured")

    except Exception as e:
        logger.error("Schema initialization failed: %s", e)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Creating tables in PostgreSQL...")
    init_db()
    print("Done!")