"""
Unit tests for Pydantic schema validation.
Verifies that invalid inputs are rejected before hitting route handlers.
"""
import pytest
from pydantic import ValidationError
from api.models.schemas import (
    RegisterRequest,
    ChatRequest,
    MCQRequest,
    FlashcardRequest,
    CompareRequest,
    QuizScoreRequest,
)


class TestRegisterRequest:

    def test_valid_registration(self):
        r = RegisterRequest(username="bhanu123", password="strongpass")
        assert r.username == "bhanu123"

    def test_username_lowercased(self):
        r = RegisterRequest(username="BhanuPrakash", password="strongpass")
        assert r.username == "bhanuprakash"

    def test_username_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="ab", password="strongpass")

    def test_password_too_short_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="bhanu", password="short")

    def test_username_with_special_chars_rejected(self):
        with pytest.raises(ValidationError):
            RegisterRequest(username="bhanu@123!", password="strongpass")

    def test_username_with_underscore_allowed(self):
        r = RegisterRequest(username="bhanu_prakash", password="strongpass")
        assert r.username == "bhanu_prakash"

    def test_username_with_hyphen_allowed(self):
        r = RegisterRequest(username="bhanu-prakash", password="strongpass")
        assert r.username == "bhanu-prakash"


class TestChatRequest:

    def test_valid_chat_request(self):
        r = ChatRequest(
            question="What is Docker?",
            session_id=1,
            provider="groq",
            api_key="a" * 50
        )
        assert r.question == "What is Docker?"

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="", session_id=1)

    def test_invalid_provider_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                question="What is Docker?",
                session_id=1,
                provider="invalid_provider"
            )

    def test_all_valid_providers_accepted(self):
        valid_providers = [
            "groq", "gemini", "openai", "anthropic",
            "mistral", "cohere", "together", "ollama"
        ]
        for p in valid_providers:
            r = ChatRequest(question="Test?", session_id=1, provider=p)
            assert r.provider == p

    def test_question_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(question="x" * 2001, session_id=1)


class TestMCQRequest:

    def test_valid_mcq_request(self):
        r = MCQRequest(session_id=1, num_questions=10)
        assert r.num_questions == 10

    def test_zero_questions_rejected(self):
        with pytest.raises(ValidationError):
            MCQRequest(session_id=1, num_questions=0)

    def test_too_many_questions_rejected(self):
        with pytest.raises(ValidationError):
            MCQRequest(session_id=1, num_questions=21)

    def test_default_values(self):
        r = MCQRequest(session_id=1)
        assert r.num_questions == 10
        assert r.topic == ""
        assert r.wrong_topics == []


class TestFlashcardRequest:

    def test_valid_flashcard_request(self):
        r = FlashcardRequest(session_id=1, num_cards=15)
        assert r.num_cards == 15

    def test_zero_cards_rejected(self):
        with pytest.raises(ValidationError):
            FlashcardRequest(session_id=1, num_cards=0)

    def test_too_many_cards_rejected(self):
        with pytest.raises(ValidationError):
            FlashcardRequest(session_id=1, num_cards=51)


class TestCompareRequest:

    def test_valid_compare_request(self):
        r = CompareRequest(session_id=1, topic_a="Docker", topic_b="Kubernetes")
        assert r.topic_a == "Docker"
        assert r.topic_b == "Kubernetes"

    def test_empty_topic_a_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(session_id=1, topic_a="", topic_b="Kubernetes")

    def test_empty_topic_b_rejected(self):
        with pytest.raises(ValidationError):
            CompareRequest(session_id=1, topic_a="Docker", topic_b="")


class TestQuizScoreRequest:

    def test_valid_score(self):
        r = QuizScoreRequest(session_id=1, score=8, total=10)
        assert r.score == 8

    def test_negative_score_rejected(self):
        with pytest.raises(ValidationError):
            QuizScoreRequest(session_id=1, score=-1, total=10)

    def test_zero_total_rejected(self):
        with pytest.raises(ValidationError):
            QuizScoreRequest(session_id=1, score=0, total=0)
