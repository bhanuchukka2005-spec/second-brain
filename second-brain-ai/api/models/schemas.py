"""
Pydantic schemas for all API request/response models.
FastAPI uses these for automatic validation and OpenAPI docs generation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores and hyphens allowed)")
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class SessionResponse(BaseModel):
    id: int
    name: str
    created_at: str
    file_names: List[str]
    chunk_count: int


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: int
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid = {"groq", "gemini", "openai", "anthropic", "mistral", "cohere", "together", "ollama"}
        if v not in valid:
            raise ValueError(f"Provider must be one of: {valid}")
        return v


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: int


class ChatHistoryResponse(BaseModel):
    history: List[dict]
    session_id: int


# ── Study Features ────────────────────────────────────────────────────────────

class MCQRequest(BaseModel):
    session_id: int
    topic: str = Field(default="", max_length=200)
    num_questions: int = Field(default=10, ge=1, le=20)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")
    wrong_topics: List[str] = Field(default_factory=list)


class MCQQuestion(BaseModel):
    question: str
    options: dict
    answer: str
    explanation: str


class MCQResponse(BaseModel):
    questions: List[MCQQuestion]
    topic: str
    total: int


class FlashcardRequest(BaseModel):
    session_id: int
    topic: str = Field(default="", max_length=200)
    num_cards: int = Field(default=15, ge=1, le=50)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardResponse(BaseModel):
    cards: List[Flashcard]
    total: int
    topic: str


class SummarizeRequest(BaseModel):
    session_id: int
    topic: str = Field(default="", max_length=200)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")


class SummarizeResponse(BaseModel):
    summary: str
    topic: str
    session_id: int


class CompareRequest(BaseModel):
    session_id: int
    topic_a: str = Field(..., min_length=1, max_length=200)
    topic_b: str = Field(..., min_length=1, max_length=200)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")


class CompareResponse(BaseModel):
    comparison: str
    topic_a: str
    topic_b: str


class ConceptMapRequest(BaseModel):
    session_id: int
    topic: str = Field(default="", max_length=200)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")


class ConceptMapResponse(BaseModel):
    mermaid: str
    topic: str


class StudyPlanRequest(BaseModel):
    session_id: int
    weak_topics: List[str] = Field(..., min_length=1)
    provider: str = Field(default="groq")
    api_key: str = Field(default="")
    ollama_model: str = Field(default="llama3.2")


class StudyPlanResponse(BaseModel):
    plan: str
    weak_topics: List[str]


# ── Quiz Scores ───────────────────────────────────────────────────────────────

class QuizScoreRequest(BaseModel):
    session_id: int
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)
    topic: str = Field(default="")


class QuizScoreResponse(BaseModel):
    id: int
    score: int
    total: int
    percentage: float
    topic: str
    timestamp: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_available: bool
    database: str
