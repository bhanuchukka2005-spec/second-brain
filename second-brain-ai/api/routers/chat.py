"""
Chat endpoints.
POST /chat/ask        — ask a question (returns full response)
POST /chat/ask/stream — ask a question (streams response token by token)
"""
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from api.models.schemas import ChatRequest, ChatResponse
from api.dependencies import CurrentUser, get_brain
from src.persistence.session_store import save_chat_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question about your notes"
)
async def ask(body: ChatRequest, current_user: CurrentUser) -> ChatResponse:
    """
    Ask a question about the indexed notes in a session.
    The AI answers using only content from your uploaded material (RAG).
    Includes source attribution showing which files the answer came from.
    """
    try:
        brain = get_brain(
            session_id=body.session_id,
            provider=body.provider,
            api_key=body.api_key,
            ollama_model=body.ollama_model,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initialize AI provider: {e}"
        )

    answer, sources = brain.ask(body.question)

    # Persist to chat history
    save_chat_message(body.session_id, "user", body.question)
    save_chat_message(body.session_id, "assistant", answer)

    logger.info(
        "Chat answer: session=%d user=%s provider=%s",
        body.session_id, current_user["username"], body.provider
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=body.session_id
    )


@router.post(
    "/ask/stream",
    summary="Ask a question with streaming response (Ollama only)",
    response_class=StreamingResponse
)
async def ask_stream(body: ChatRequest, current_user: CurrentUser):
    """
    Stream the AI response token by token.
    Only supported with Ollama (local) provider.
    Returns text/event-stream — consume with EventSource in the frontend.
    """
    if body.provider != "ollama":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is only supported with the Ollama provider."
        )

    try:
        brain = get_brain(
            session_id=body.session_id,
            provider=body.provider,
            api_key=body.api_key,
            ollama_model=body.ollama_model,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to initialize Ollama: {e}"
        )

    # Retrieve context
    chunks = brain.store.query(body.question, n_results=2)
    if not chunks:
        async def no_context():
            yield "I couldn't find relevant information in your notes."
        return StreamingResponse(no_context(), media_type="text/plain")

    ctx_words = chunks[0]["text"].split()[:300]
    context = " ".join(ctx_words)
    prompt = f"Notes: {context}\n\nQ: {body.question}\nA:"

    save_chat_message(body.session_id, "user", body.question)

    def token_generator():
        full_response = []
        from src.llm.ollama_client import stream_ollama
        for token in stream_ollama(brain.model, prompt, max_tokens=400):
            full_response.append(token)
            yield token
        # Save full response to history after streaming
        save_chat_message(body.session_id, "assistant", "".join(full_response))

    logger.info(
        "Streaming chat: session=%d user=%s",
        body.session_id, current_user["username"]
    )

    return StreamingResponse(token_generator(), media_type="text/plain")
