"""
Study features — MCQ, flashcards, summarize, compare, concept map, study plan, scores.
All LLM-calling endpoints share one rate limit budget via _get_brain(),
so a user can't dodge the limit by spreading requests across features.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from api.models.schemas import (
    MCQRequest, MCQResponse, MCQQuestion,
    FlashcardRequest, FlashcardResponse, Flashcard,
    SummarizeRequest, SummarizeResponse,
    CompareRequest, CompareResponse,
    ConceptMapRequest, ConceptMapResponse,
    StudyPlanRequest, StudyPlanResponse,
    QuizScoreRequest, QuizScoreResponse,
)
from api.dependencies import CurrentUser, get_brain
from src.db.session_store import (
    save_flashcards as db_save_flashcards,
    save_quiz_score as db_save_quiz_score,
    load_quiz_scores,
    get_session,
)
from src.utils.rate_limiter import rate_limit_key_for_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/study", tags=["Study Features"])

STUDY_MAX_REQUESTS = 15
STUDY_WINDOW_SECONDS = 60


def _get_brain(body, current_user):
    """Verify session ownership, enforce rate limit, and return brain instance."""
    rate_limit_key_for_user(current_user["id"], "study", STUDY_MAX_REQUESTS, STUDY_WINDOW_SECONDS)

    session = get_session(body.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    try:
        return get_brain(body.session_id, body.provider, body.api_key, body.ollama_model)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider error: {e}")


@router.post("/mcq", response_model=MCQResponse, summary="Generate adaptive MCQs")
async def generate_mcqs(body: MCQRequest, current_user: CurrentUser) -> MCQResponse:
    brain = _get_brain(body, current_user)
    _, parsed = brain.generate_mcqs_structured(body.topic, body.num_questions, body.wrong_topics)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate MCQs. Try uploading more notes or a different topic."
        )
    questions = [
        MCQQuestion(
            question=q["question"],
            options=q["options"],
            answer=q["answer"],
            explanation=q.get("explanation", "")
        ) for q in parsed
    ]
    logger.info("MCQs generated: session=%d count=%d", body.session_id, len(questions))
    return MCQResponse(questions=questions, topic=body.topic, total=len(questions))


@router.post("/flashcards", response_model=FlashcardResponse, summary="Generate Anki-compatible flashcards")
async def generate_flashcards(body: FlashcardRequest, current_user: CurrentUser) -> FlashcardResponse:
    brain = _get_brain(body, current_user)
    cards = brain.generate_flashcards(body.topic, body.num_cards)
    if not cards:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate flashcards. Upload more notes first."
        )
    db_save_flashcards(body.session_id, cards, body.topic)
    return FlashcardResponse(
        cards=[Flashcard(front=c["front"], back=c["back"]) for c in cards],
        total=len(cards),
        topic=body.topic,
    )


@router.post("/summarize", response_model=SummarizeResponse, summary="Summarize your notes")
async def summarize(body: SummarizeRequest, current_user: CurrentUser) -> SummarizeResponse:
    brain = _get_brain(body, current_user)
    summary = brain.summarize(body.topic or "")
    return SummarizeResponse(summary=summary, topic=body.topic or "", session_id=body.session_id)


@router.post("/compare", response_model=CompareResponse, summary="Compare two topics")
async def compare_topics(body: CompareRequest, current_user: CurrentUser) -> CompareResponse:
    brain = _get_brain(body, current_user)
    comparison = brain.compare_topics(body.topic_a, body.topic_b)
    return CompareResponse(comparison=comparison, topic_a=body.topic_a, topic_b=body.topic_b)


@router.post("/concept-map", response_model=ConceptMapResponse, summary="Generate a Mermaid concept map")
async def concept_map(body: ConceptMapRequest, current_user: CurrentUser) -> ConceptMapResponse:
    brain = _get_brain(body, current_user)
    mermaid = brain.generate_concept_map(body.topic or "")
    if not mermaid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate concept map. Try a more specific topic."
        )
    return ConceptMapResponse(mermaid=mermaid, topic=body.topic or "")


@router.post("/study-plan", response_model=StudyPlanResponse, summary="Generate a personalized study plan")
async def study_plan(body: StudyPlanRequest, current_user: CurrentUser) -> StudyPlanResponse:
    brain = _get_brain(body, current_user)
    plan = brain.generate_study_plan(body.weak_topics)
    return StudyPlanResponse(plan=plan, weak_topics=body.weak_topics)


@router.post(
    "/quiz-score",
    response_model=QuizScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a quiz score",
)
async def save_score(body: QuizScoreRequest, current_user: CurrentUser) -> QuizScoreResponse:
    # No LLM call here, just a DB write — no rate limit needed.
    session = get_session(body.session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    db_save_quiz_score(body.session_id, body.score, body.total, body.topic)
    pct = round(body.score / body.total * 100, 1)
    logger.info(
        "Quiz score saved: session=%d score=%d/%d (%.1f%%)",
        body.session_id, body.score, body.total, pct
    )
    return QuizScoreResponse(
        id=0, score=body.score, total=body.total,
        percentage=pct, topic=body.topic,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/quiz-scores/{session_id}", summary="Get quiz score history")
async def get_scores(session_id: int, current_user: CurrentUser) -> dict:
    session = get_session(session_id, current_user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    scores = load_quiz_scores(session_id)
    for s in scores:
        s["percentage"] = round(s["score"] / s["total"] * 100, 1)
    return {"scores": scores, "session_id": session_id, "total": len(scores)}