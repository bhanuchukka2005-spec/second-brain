"""
PostgreSQL-backed user management with JWT auth.
Supports both username/password and Google OAuth accounts.
"""
import hashlib
import hmac
import base64
import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Optional

from src.db.connection import execute_one, execute_write

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-in-production-use-a-long-random-string")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        decoded = base64.b64decode(hashed.encode())
        salt, stored_key = decoded[:32], decoded[32:]
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        return hmac.compare_digest(key, stored_key)
    except Exception:
        return False


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (4 - len(data) % 4))


def create_access_token(user_id: int, username: str) -> str:
    header = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id), "username": username,
        "exp": int(expire.timestamp()), "iat": int(datetime.utcnow().timestamp()),
    }
    body = _b64e(json.dumps(payload).encode())
    signing_input = f"{header}.{body}"
    signature = _b64e(hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, signature = parts
        signing_input = f"{header}.{body}"
        expected = _b64e(hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_b64d(body))
        if datetime.utcnow().timestamp() > payload.get("exp", 0):
            return None
        return payload
    except Exception:
        return None


def create_user(username: str, password: str) -> Optional[dict]:
    try:
        uid = execute_write(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username.lower(), hash_password(password))
        )
        return {"id": uid, "username": username.lower(), "created_at": datetime.utcnow().isoformat()}
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return None
        raise


def get_user_by_username(username: str) -> Optional[dict]:
    return execute_one(
        "SELECT id, username, password_hash, created_at::text AS created_at FROM users WHERE username = %s",
        (username.lower(),)
    )


def get_user_by_id(user_id: int) -> Optional[dict]:
    return execute_one(
        "SELECT id, username, created_at::text AS created_at FROM users WHERE id = %s",
        (user_id,)
    )


def init_user_table() -> None:
    """No-op — table created by schema.py init_db()."""
    pass


def _slugify_username(name: str, email: str) -> str:
    """Generate a clean username from Google name/email, ensuring uniqueness."""
    base = re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_"))
    if not base:
        base = email.split("@")[0].lower()
    base = base[:40] or "user"

    candidate = base
    suffix = 1
    while get_user_by_username(candidate):
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


def get_user_by_google_sub(google_sub: str) -> Optional[dict]:
    return execute_one(
        """
        SELECT id, username, email, avatar_url, created_at::text AS created_at
        FROM users WHERE google_sub = %s
        """,
        (google_sub,)
    )


def get_or_create_google_user(email: str, name: str, google_sub: str, picture: str = "") -> dict:
    """
    Find an existing Google-linked user, or create a new one.
    Does not auto-link to existing password accounts with the same email
    (security: prevents account takeover via email spoofing).
    """
    existing = get_user_by_google_sub(google_sub)
    if existing:
        logger.info("Existing Google user logged in: %s", existing["username"])
        return existing

    username = _slugify_username(name, email)
    uid = execute_write(
        """
        INSERT INTO users (username, google_sub, email, avatar_url)
        VALUES (%s, %s, %s, %s) RETURNING id
        """,
        (username, google_sub, email, picture)
    )
    logger.info("New Google user created: %s (%s)", username, email)
    return {
        "id": uid, "username": username, "email": email,
        "avatar_url": picture, "created_at": datetime.utcnow().isoformat(),
    }