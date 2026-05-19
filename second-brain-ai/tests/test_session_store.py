"""Unit tests for SQLite session store."""
from unittest.mock import patch
import tempfile
import os


def get_db_path(tmp_path):
    return os.path.join(tmp_path, "test.db")


class TestSessionStore:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = get_db_path(self.tmp)
        with patch("src.persistence.session_store.DB_PATH", self.db_path):
            from src.persistence.session_store import init_db
            init_db()

    def _run(self, fn):
        with patch("src.persistence.session_store.DB_PATH", self.db_path):
            return fn()

    def test_save_and_list(self):
        def fn():
            from src.persistence.session_store import save_session, list_sessions
            sid = save_session("Test", ["a.pdf"], 10)
            sessions = list_sessions()
            assert any(s["id"] == sid for s in sessions)
        self._run(fn)

    def test_delete_session(self):
        def fn():
            from src.persistence.session_store import save_session, list_sessions, delete_session
            sid = save_session("Delete", ["b.pdf"], 5)
            delete_session(sid)
            assert not any(s["id"] == sid for s in list_sessions())
        self._run(fn)

    def test_chat_history(self):
        def fn():
            from src.persistence.session_store import save_session, save_chat_message, load_chat_history
            sid = save_session("Chat", ["c.pdf"], 5)
            save_chat_message(sid, "user", "Hello")
            save_chat_message(sid, "assistant", "Hi")
            h = load_chat_history(sid)
            assert len(h) == 2
            assert h[0]["role"] == "user"
        self._run(fn)

    def test_flashcards(self):
        def fn():
            from src.persistence.session_store import save_session, save_flashcards, load_flashcards
            sid = save_session("FC", ["d.pdf"], 5)
            cards = [{"front": "Q1", "back": "A1"}, {"front": "Q2", "back": "A2"}]
            save_flashcards(sid, cards, "test")
            loaded = load_flashcards(sid)
            fronts = [c["front"] for c in loaded]
            assert "Q1" in fronts and "Q2" in fronts
        self._run(fn)

    def test_quiz_scores(self):
        def fn():
            from src.persistence.session_store import save_session, save_quiz_score, load_quiz_scores
            sid = save_session("Quiz", ["e.pdf"], 5)
            save_quiz_score(sid, 8, 10, "docker")
            scores = load_quiz_scores(sid)
            assert scores[0]["score"] == 8
        self._run(fn)

    def test_delete_cascades(self):
        def fn():
            from src.persistence.session_store import (
                save_session, save_chat_message, load_chat_history, delete_session
            )
            sid = save_session("Cascade", ["f.pdf"], 5)
            save_chat_message(sid, "user", "test")
            delete_session(sid)
            assert load_chat_history(sid) == []
        self._run(fn)

    def test_sessions_isolated(self):
        def fn():
            from src.persistence.session_store import save_session, save_chat_message, load_chat_history
            s1 = save_session("S1", ["a.pdf"], 5)
            s2 = save_session("S2", ["b.pdf"], 5)
            save_chat_message(s1, "user", "for s1")
            save_chat_message(s2, "user", "for s2")
            assert len(load_chat_history(s1)) == 1
            assert len(load_chat_history(s2)) == 1
        self._run(fn)
