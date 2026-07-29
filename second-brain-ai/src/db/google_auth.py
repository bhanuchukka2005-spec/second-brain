"""
Google OAuth token verification.
Verifies the ID token Google sends to the frontend, using Google's
public token info endpoint — no extra Python package needed.
"""
import logging
import urllib.request
import urllib.error
import json
import os
from typing import Optional

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "195046896396-a620heggt6bibibvfgsm2jktpm20ln5g.apps.googleusercontent.com"
)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_google_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google ID token by calling Google's tokeninfo endpoint.
    Returns the decoded payload (email, name, sub, etc.) if valid, else None.
    """
    if not id_token or not id_token.strip():
        return None

    url = f"{GOOGLE_TOKENINFO_URL}?id_token={id_token.strip()}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        logger.warning("Google token verification failed: HTTP %s", e.code)
        return None
    except Exception as e:
        logger.error("Google token verification error: %s", e)
        return None

    if payload.get("aud") != GOOGLE_CLIENT_ID:
        logger.warning(
            "Google token audience mismatch: expected=%s got=%s",
            GOOGLE_CLIENT_ID, payload.get("aud")
        )
        return None

    if payload.get("email_verified") not in (True, "true"):
        logger.warning("Google email not verified for: %s", payload.get("email"))
        return None

    logger.info("Google token verified for: %s", payload.get("email"))
    return {
        "email": payload.get("email"),
        "name": payload.get("name", payload.get("email", "").split("@")[0]),
        "google_sub": payload.get("sub"),
        "picture": payload.get("picture", ""),
    }