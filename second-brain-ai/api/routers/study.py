"""
Study feature endpoints.
POST /study/mcq          — generate adaptive MCQs
POST /study/flashcards   — generate flashcards
POST /study/summarize    — summarize notes
POST /study/compare      — compare two topics
POST /study/concept-map  — generate Mermaid concept map
POST /study/study-plan   — generate personalized study plan
POST /study/quiz-score   — save a quiz score
GET  /study/quiz-scores/{session_id} — get quiz score history
"""
import logging
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
from src.persistence.session_store import (
    save_flashcards as db_save_flashcards,
    save_quiz_score as db_save_quiz_score,
    load_quiz_scores,
)
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/study", tags=["Study Features"])


def _get_brain(body):
    """Helper to get brain from any study request body."""
    try:
        return get_brain(
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


@router.post(
    "/mcq",
    response_model=MCQResponse,
    summary="Generate adaptive MCQs from your notes"
)
async def generate_mcqs(body: MCQRequest, current_user: CurrentUser) -> MCQResponse:
    """
    Generate multiple choice questions from indexed notes.
    Adaptive: pass wrong_topics to make questions harder on weak areas.
    """
    brain = _get_brain(body)
    _, parsed = brain.generate_mcqs_structured(
        topic=body.topic,
        num_questions=body.num_questions,
        wrong_topics=body.wrong_topics,
    )

    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate MCQs. Try a different topic or upload more notes."
        )

    questions = [
        MCQQuestion(
            question=q["question"],
            options=q["options"],
            answer=q["answer"],
            explanation=q.get("explanation", "")
        )
        for q in parsed
    ]

    logger.info(
        "MCQs generated: session=%d count=%d user=%s",
        body.session_id, len(questions), current_user["username"]
    )

    return MCQResponse(
        questions=questions,
        topic=body.topic,
        total=len(questions)
    )


@router.post(
    "/flashcards",
    response_model=FlashcardResponse,
    summary="Generate Anki-compatible flashcards"
)
async def generate_flashcards(body: FlashcardRequest, current_user: CurrentUser) -> FlashcardResponse:
    """
    Generate flashcards from indexed notes.
    Cards are also saved to the session for later retrieval.
    """
    brain = _get_brain(body)
    cards = brain.generate_flashcards(topic=body.topic, num_cards=body.num_cards)

    if not cards:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate flashcards. Upload more notes first."
        )

    db_save_flashcards(body.session_id, cards, body.topic)

    logger.info(
        "Flashcards generated: session=%d count=%d user=%s",
        body.session_id, len(cards), current_user["username"]
    )

    return FlashcardResponse(
        cards=[Flashcard(front=c["front"], back=c["back"]) for c in cards],
        total=len(cards),
        topic=body.topic
    )


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize your notes"
)
async def summarize(body: SummarizeRequest, current_user: CurrentUser) -> SummarizeResponse:
    """Generate a concise summary of the indexed notes, optionally focused on a topic."""
    brain = _get_brain(body)
    summary = brain.summarize(topic=body.topic)
    return SummarizeResponse(
        summary=summary,
        topic=body.topic,
        session_id=body.session_id
    )


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare two topics from your notes"
)
async def compare_topics(body: CompareRequest, current_user: CurrentUser) -> CompareResponse:
    """
    Compare two topics side-by-side using retrieved note chunks.
    Returns similarities, differences, and key takeaways.
    """
    brain = _get_brain(body)
    comparison = brain.compare_topics(body.topic_a, body.topic_b)
    return CompareResponse(
        comparison=comparison,
        topic_a=body.topic_a,
        topic_b=body.topic_b
    )


@router.post(
    "/concept-map",
    response_model=ConceptMapResponse,
    summary="Generate a Mermaid concept map"
)
async def concept_map(body: ConceptMapRequest, current_user: CurrentUser) -> ConceptMapResponse:
    """
    Generate a Mermaid mindmap diagram from your notes.
    Paste the returned mermaid string into any Mermaid renderer.
    """
    brain = _get_brain(body)
    mermaid = brain.generate_concept_map(topic=body.topic)

    if not mermaid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not generate concept map. Try a more specific topic."
        )

    return ConceptMapResponse(mermaid=mermaid, topic=body.topic)


@router.post(
    "/study-plan",
    response_model=StudyPlanResponse,
    summary="Generate a personalized study plan"
)
async def study_plan(body: StudyPlanRequest, current_user: CurrentUser) -> StudyPlanResponse:
    """Generate a 7-day study plan based on the student's weak topics."""
    brain = _get_brain(body)
    plan = brain.generate_study_plan(weak_topics=body.weak_topics)
    return StudyPlanResponse(plan=plan, weak_topics=body.weak_topics)


@router.post(
    "/quiz-score",
    response_model=QuizScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a quiz score"
)
async def save_score(body: QuizScoreRequest, current_user: CurrentUser) -> QuizScoreResponse:
    """Save a quiz score for a session. Used to track progress over time."""
    db_save_quiz_score(
        session_id=body.session_id,
        score=body.score,
        total=body.total,
        topic=body.topic
    )
    pct = round(body.score / body.total * 100, 1)
    logger.info(
        "Quiz score saved: session=%d score=%d/%d (%.1f%%) user=%s",
        body.session_id, body.score, body.total, pct, current_user["username"]
    )
    return QuizScoreResponse(
        id=0,
        score=body.score,
        total=body.total,
        percentage=pct,
        topic=body.topic,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get(
    "/quiz-scores/{session_id}",
    summary="Get quiz score history for a session"
)
async def get_scores(session_id: int, current_user: CurrentUser) -> dict:
    """Returns all quiz scores for a session, most recent first."""
    scores = load_quiz_scores(session_id)
    for s in scores:
        s["percentage"] = round(s["score"] / s["total"] * 100, 1)
    return {"scores": scores, "session_id": session_id, "total": len(scores)}
