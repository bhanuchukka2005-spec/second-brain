"""
AI Second Brain — FastAPI Backend
Phase 2 of the production upgrade.

Run with:
    uvicorn api.main:app --reload --port 8000

Auto-generated API docs:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import health, auth, sessions, chat, study
from api.models.auth import init_user_table
from src.persistence.session_store import init_db
from src.logger import setup_logging
from src.config import config

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging(log_dir=config.log_dir, log_level=config.log_level)
logger = logging.getLogger(__name__)


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and user table on startup."""
    logger.info("Starting %s v%s", config.app_name, config.app_version)
    init_db()
    init_user_table()
    config.validate()
    logger.info("API ready — docs at http://localhost:8000/docs")
    yield
    logger.info("Shutting down %s", config.app_name)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="🧠 AI Second Brain API",
    description="""
Production-grade AI study companion backend.

## Features
- **Chat** with your notes using RAG (Retrieval Augmented Generation)
- **MCQ generation** with adaptive difficulty
- **Flashcards** with Anki-compatible export
- **Concept maps** as Mermaid diagrams
- **Summarization** and topic comparison
- **Personalized study plans**
- **7 LLM providers** + local Ollama (no API key needed)

## Authentication
All endpoints (except `/health`) require a Bearer token.
1. Register: `POST /auth/register`
2. Login: `POST /auth/login` → get token
3. Add header: `Authorization: Bearer <token>`
    """,
    version=config.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS (ready for React frontend in Phase 3) ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server
        "http://localhost:8501",   # Streamlit
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s %s → %s", request.method, request.url, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check logs for details."}
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(study.router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": config.app_name,
        "version": config.app_version,
        "docs": "/docs",
        "health": "/health",
    }
