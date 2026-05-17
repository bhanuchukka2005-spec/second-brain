"""
JWT authentication utilities.
Handles token creation, verification, and user password hashing.
"""
import logging
import hashlib
import hmac
import base64
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Secret key — in production, set via environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-use-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h
USER_DB_PATH = os.getenv("DB_PATH", "data/sessions.db")


# ── Password hashing (no bcrypt dependency — uses PBKDF2) ────────────────────

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 (stdlib, no extra deps)."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        decoded = base64.b64decode(hashed.encode())
        salt = decoded[:32]
        stored_key = decoded[32:]
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        return hmac.compare_digest(key, stored_key)
    except Exception:
        return False


# ── JWT (pure stdlib — no PyJWT dependency) ───────────────────────────────────

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)


def create_access_token(user_id: int, username: str) -> str:
    """Create a signed JWT access token."""
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
    }
    body = _b64encode(json.dumps(payload).encode())
    signing_input = f"{header}.{body}"
    signature = _b64encode(
        hmac.new(
            SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256
        ).digest()
    )
    logger.debug("Token created for user_id=%d", user_id)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    Returns payload dict or None if invalid/expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header, body, signature = parts
        signing_input = f"{header}.{body}"
        expected_sig = _b64encode(
            hmac.new(
                SECRET_KEY.encode(),
                signing_input.encode(),
                hashlib.sha256
            ).digest()
        )

        if not hmac.compare_digest(signature, expected_sig):
            logger.warning("JWT signature mismatch")
            return None

        payload = json.loads(_b64decode(body))

        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            logger.warning("JWT token expired for user=%s", payload.get("username"))
            return None

        return payload

    except Exception as e:
        logger.error("JWT decode error: %s", e)
        return None


# ── User DB operations ────────────────────────────────────────────────────────

def _get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(USER_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_table():
    """Create users table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info("User table initialized")


def create_user(username: str, password: str) -> Optional[dict]:
    """
    Create a new user. Returns user dict or None if username taken.
    """
    conn = _get_conn()
    try:
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), now)
        )
        conn.commit()
        return {"id": cur.lastrowid, "username": username, "created_at": now}
    except sqlite3.IntegrityError:
        logger.warning("Username already taken: %s", username)
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[dict]:
    """Fetch user record by username."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Fetch user record by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
