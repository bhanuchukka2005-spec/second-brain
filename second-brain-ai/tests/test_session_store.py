"""
Unit tests for session_store SQLite persistence layer.
Uses a temporary in-memory/temp DB for isolation.
"""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    """Redirect DB to a temp file for each test."""
    db_file = str(tmp_path / "test_sessions.db")
    with patch("src.persistence.session_store.DB_PATH", db_file):
        from src.persistence.session_store import init_db
        init_db()
        yield db_file


class TestSessionStore:

    def test_save_and_list_session(self):
        from src.persistence.session_store import save_session, list_sessions
        sid = save_session("Test Session", ["notes.pdf"], 100)
        assert isinstance(sid, int)
        sessions = list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["name"] == "Test Session"

    def test_delete_session(self):
        from src.persistence.session_store import save_session, list_sessions, delete_session
        sid = save_session("To Delete", ["file.pdf"], 50)
        assert len(list_sessions()) == 1
        delete_session(sid)
        assert len(list_sessions()) == 0

    def test_save_and_load_chat_history(self):
        from src.persistence.session_store import (
            save_session, save_chat_message, load_chat_history
        )
        sid = save_session("Chat Test", ["notes.pdf"], 10)
        save_chat_message(sid, "user", "What is Docker?")
        save_chat_message(sid, "assistant", "Docker is a containerization platform.")

        history = load_chat_history(sid)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert "Docker" in history[0]["content"]

    def test_save_and_load_flashcards(self):
        from src.persistence.session_store import (
            save_session, save_flashcards, load_flashcards
        )
        sid = save_session("Flashcard Test", ["notes.pdf"], 10)
        cards = [
            {"front": "What is Kubernetes?", "back": "Container orchestration"},
            {"front": "What is Helm?", "back": "Package manager for Kubernetes"},
        ]
        save_flashcards(sid, cards, "kubernetes")
        loaded = load_flashcards(sid)
        fronts = [c["front"] for c in loaded]
        assert len(loaded) == 2
        assert "What is Kubernetes?" in fronts
        assert "What is Helm?" in fronts

    def test_save_and_load_quiz_scores(self):
        from src.persistence.session_store import (
            save_session, save_quiz_score, load_quiz_scores
        )
        sid = save_session("Quiz Test", ["notes.pdf"], 10)
        save_quiz_score(sid, 8, 10, "ansible")
        save_quiz_score(sid, 6, 10, "docker")

        scores = load_quiz_scores(sid)
        assert len(scores) == 2
        assert scores[0]["score"] == 6  # most recent first

    def test_delete_cascades_to_history(self):
        from src.persistence.session_store import (
            save_session, save_chat_message, load_chat_history, delete_session
        )
        sid = save_session("Cascade Test", ["notes.pdf"], 10)
        save_chat_message(sid, "user", "Hello")
        delete_session(sid)
        history = load_chat_history(sid)
        assert len(history) == 0

    def test_multiple_sessions_isolated(self):
        from src.persistence.session_store import (
            save_session, save_chat_message, load_chat_history
        )
        sid1 = save_session("Session 1", ["a.pdf"], 10)
        sid2 = save_session("Session 2", ["b.pdf"], 20)
        save_chat_message(sid1, "user", "Message for session 1")
        save_chat_message(sid2, "user", "Message for session 2")

        h1 = load_chat_history(sid1)
        h2 = load_chat_history(sid2)
        assert len(h1) == 1
        assert len(h2) == 1
        assert "session 1" in h1[0]["content"]
        assert "session 2" in h2[0]["content"]
