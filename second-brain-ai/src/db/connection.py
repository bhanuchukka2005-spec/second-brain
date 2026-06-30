"""
PostgreSQL connection management using psycopg2 connection pool.
All DB operations go through get_conn() context manager.
"""
import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "port":     int(os.getenv("PG_PORT", "5432")),
    "dbname":   os.getenv("PG_DB", "second_brain"),
    "user":     os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
}

_pool: Optional[pool.ThreadedConnectionPool] = None


def init_pool() -> None:
    """Initialize the connection pool. Call once at app startup."""
    global _pool
    try:
        _pool = pool.ThreadedConnectionPool(minconn=1, maxconn=10, **DB_CONFIG)
        logger.info("PostgreSQL pool initialized: host=%s db=%s", DB_CONFIG["host"], DB_CONFIG["dbname"])
    except Exception as e:
        logger.error("Failed to connect to PostgreSQL: %s", e)
        raise RuntimeError(
            f"Cannot connect to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}. "
            f"Make sure PostgreSQL is running and database '{DB_CONFIG['dbname']}' exists.\nError: {e}"
        )


@contextmanager
def get_conn() -> Generator:
    """Context manager that returns a DB connection from the pool."""
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def execute(sql: str, params=None) -> list:
    """Execute a query and return all rows as dicts."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            try:
                return [dict(r) for r in cur.fetchall()]
            except Exception:
                return []


def execute_one(sql: str, params=None):
    """Execute a query and return one row as dict or None."""
    rows = execute(sql, params)
    return rows[0] if rows else None


def execute_write(sql: str, params=None):
    """Execute INSERT/UPDATE/DELETE and return value if RETURNING is used."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            try:
                return cur.fetchone()[0]
            except Exception:
                return None