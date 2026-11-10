"""Central configuration management via environment variables."""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AppConfig:
    app_name: str = "AI Second Brain"
    app_version: str = "2.0.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "data/sessions.db"))
    upload_dir: str = field(default_factory=lambda: os.getenv("UPLOAD_DIR", "data/uploads"))
    log_dir: str = field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "500")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "50")))
    retrieval_top_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "5")))
    retrieval_top_k_ollama: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K_OLLAMA", "3")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "1500")))
    max_tokens_ollama: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS_OLLAMA", "600")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_base_delay: float = field(default_factory=lambda: float(os.getenv("RETRY_BASE_DELAY", "1.0")))

    def validate(self) -> None:
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

config = AppConfig()
