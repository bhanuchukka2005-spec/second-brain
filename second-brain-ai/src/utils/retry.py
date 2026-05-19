"""
Retry utilities with exponential backoff + input validation.
Use @retry_with_backoff on any LLM API call.
"""
import time
import logging
import functools
import re
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator: retries a function on specified exceptions
    with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Don't retry on auth errors
                    if any(kw in error_str for kw in (
                        "invalid api key", "unauthorized", "forbidden", "authentication"
                    )):
                        logger.error("Auth error — not retrying: %s", e)
                        raise

                    if attempt == max_retries:
                        logger.error(
                            "All %d retries exhausted for %s. Last error: %s",
                            max_retries, func.__name__, e
                        )
                        raise

                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.1fs...",
                        attempt, max_retries, func.__name__, e, delay
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exception  # type: ignore

        return wrapper
    return decorator


def validate_api_key(api_key: str, provider: str) -> None:
    """
    Basic structural validation of API keys.
    Raises ValueError with a helpful message if invalid.
    """
    if not api_key or not api_key.strip():
        raise ValueError(
            f"API key for {provider} is empty. Please enter a valid key."
        )

    key = api_key.strip()

    # Check for spaces first
    if " " in key:
        raise ValueError(
            f"API key for {provider} contains spaces. Please check it's correct."
        )

    # Relaxed minimum lengths — different providers have different key formats
    min_lengths = {
        "groq":      20,
        "openai":    20,
        "anthropic": 20,
        "gemini":    15,
        "mistral":   15,
        "cohere":    15,
        "together":  15,
    }

    min_len = min_lengths.get(provider, 10)
    if len(key) < min_len:
        raise ValueError(
            f"API key for {provider} looks too short ({len(key)} chars). "
            f"Please check you copied the full key."
        )


def validate_file_upload(file_name: str, file_size_bytes: int, max_mb: int = 50) -> None:
    """Validate uploaded file before processing."""
    allowed_extensions = {".pdf", ".pptx", ".txt"}
    ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    if ext not in allowed_extensions:
        raise ValueError(
            f"File '{file_name}' has unsupported type '{ext}'. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    max_bytes = max_mb * 1024 * 1024
    if file_size_bytes > max_bytes:
        raise ValueError(
            f"File '{file_name}' is too large "
            f"({file_size_bytes / 1024 / 1024:.1f}MB). Max allowed: {max_mb}MB."
        )


def validate_youtube_url(url: str) -> None:
    """Validate YouTube URL before processing."""
    if not url or not url.strip():
        raise ValueError("YouTube URL cannot be empty.")
    pattern = r"(youtube\.com/watch\?v=|youtu\.be/)[0-9A-Za-z_-]{11}"
    if not re.search(pattern, url):
        raise ValueError(
            f"'{url}' doesn't look like a valid YouTube URL. "
            "Expected format: https://youtube.com/watch?v=XXXXXXXXXXX"
        )
