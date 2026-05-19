"""Centralized logging with rotating file handler."""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    os.makedirs(log_dir, exist_ok=True)
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    fmt_console = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
    fmt_file = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s")

    console = logging.StreamHandler()
    console.setLevel(log_level_int)
    console.setFormatter(fmt_console)

    file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt_file)

    if not root_logger.handlers:
        root_logger.addHandler(console)
        root_logger.addHandler(file_handler)

    for noisy in ("chromadb", "httpx", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
