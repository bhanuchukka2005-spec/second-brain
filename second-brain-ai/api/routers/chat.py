"""
Chat endpoints — PostgreSQL-backed, rate limited per user.
Chat calls a real LLM (possibly a paid API), so limits here directly
protect against runaway API cost, not just abuse.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from api.models.schemas import ChatRequest, ChatResponse
from api.dependencies import CurrentUser, get_brain
from src.db.session_store import save_chat_message, get_session
from src.utils.rate_limiter import rate_limit_key_for_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Both /ask and /ask/stream share one budget under the "chat" scope so a
# user can't dodge the limit by alternating between the two endpoints.
CHAT_MAX_REQUESTS = 20
CHAT_WINDOW_SECONDS = 60


@router.post("/ask", response_model=ChatResponse, summary="Ask a question about your notes")
async def ask(body: ChatRequest, current_user: CurrentUser) -> ChatResponse:
    """
    Ask a question about indexed notes (RAG).
    Only the session owner can query their session.
    Rate limited to 20 requests/minute per user.
    """
    rate_limit_key_for_user(current_user["id"], "chat", CHAT_MAX_REQUESTS, CHAT_WINDOW_SECONDS)

    session = get_session(body.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    try:
        brain = get_brain(body.session_id, body.provider, body.api_key, body.ollama_model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider error: {e}")

    answer, sources = brain.ask(body.question)
    save_chat_message(body.session_id, "user", body.question)
    save_chat_message(body.session_id, "assistant", answer)

    logger.info("Chat: session=%d user=%s provider=%s", body.session_id, current_user["username"], body.provider)
    return ChatResponse(answer=answer, sources=sources, session_id=body.session_id)


@router.post("/ask/stream", summary="Streaming chat for Ollama provider")
async def ask_stream(body: ChatRequest, current_user: CurrentUser):
    """
    Stream the AI response token by token.
    Only supported with the Ollama (local) provider.
    Shares the same rate budget as /ask.
    """
    rate_limit_key_for_user(current_user["id"], "chat", CHAT_MAX_REQUESTS, CHAT_WINDOW_SECONDS)

    if body.provider != "ollama":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is only supported with the Ollama provider."
        )

    session = get_session(body.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    try:
        brain = get_brain(body.session_id, body.provider, body.api_key, body.ollama_model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Ollama error: {e}")

    chunks = brain.store.query(body.question, n_results=2)
    if not chunks:
        async def no_ctx():
            yield "I couldn't find relevant information in your notes."
        return StreamingResponse(no_ctx(), media_type="text/plain")

    ctx_words = chunks[0]["text"].split()[:300]
    prompt = f"Notes: {' '.join(ctx_words)}\n\nQ: {body.question}\nA:"
    save_chat_message(body.session_id, "user", body.question)

    def token_gen():
        full = []
        from src.llm.ollama_client import stream_ollama
        for token in stream_ollama(brain.model, prompt, max_tokens=400):
            full.append(token)
            yield token
        save_chat_message(body.session_id, "assistant", "".join(full))

    return StreamingResponse(token_gen(), media_type="text/plain")