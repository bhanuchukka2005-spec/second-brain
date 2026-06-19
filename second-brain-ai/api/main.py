"""
AI Second Brain — FastAPI Backend (Phase 4: PostgreSQL)
Run: uvicorn api.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import health, auth, sessions, chat, study
from src.db.connection import init_pool
from src.db.schema import init_db
from src.logger import setup_logging
from src.config import config

setup_logging(log_dir=config.log_dir, log_level=config.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", config.app_name, config.app_version)
    init_pool()        # Connect to PostgreSQL
    init_db()          # Create tables if not exist
    config.validate()  # Create data/ and logs/ dirs
    logger.info("API ready → http://localhost:8000/docs")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="🧠 AI Second Brain API",
    description="""
Production-grade AI study companion — Phase 4 with PostgreSQL persistence.

## What's new in Phase 4
- **PostgreSQL** replaces SQLite — data persists forever
- **Persistent ChromaDB** — sessions survive backend restarts
- **Multi-user** — each user sees only their own sessions
- **User isolation** — complete data separation per user

## Authentication
1. Register: `POST /auth/register`
2. Login: `POST /auth/login` → get token
3. Add header: `Authorization: Bearer <token>`
    """,
    version=config.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled: %s %s → %s", request.method, request.url, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(study.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": config.app_name, "version": config.app_version, "docs": "/docs"}
