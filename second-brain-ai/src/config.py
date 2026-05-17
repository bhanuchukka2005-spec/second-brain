"""
Central configuration management.
All settings loaded from environment variables / .env file.
Never hardcode secrets — use this module everywhere.
"""
import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()  # loads .env file if present

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    # App
    app_name: str = "AI Second Brain"
    app_version: str = "2.0.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Storage
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "data/sessions.db"))
    upload_dir: str = field(default_factory=lambda: os.getenv("UPLOAD_DIR", "data/uploads"))
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # RAG settings
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50")))
    retrieval_top_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "5")))
    retrieval_top_k_ollama: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K_OLLAMA", "3")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "1500")))
    max_tokens_ollama: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS_OLLAMA", "600")))

    # Retry settings
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_base_delay: float = field(default_factory=lambda: float(os.getenv("RETRY_BASE_DELAY", "1.0")))

    def validate(self) -> None:
        """Validate config on startup."""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        if self.chunk_size <= 0:
            raise ValueError("CHUNK_SIZE must be positive")
        if self.retrieval_top_k <= 0:
            raise ValueError("RETRIEVAL_TOP_K must be positive")
        logger.info("Config validated successfully")


# Singleton instance
config = AppConfig()
