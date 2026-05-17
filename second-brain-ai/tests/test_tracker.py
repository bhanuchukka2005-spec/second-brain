"""
Unit tests for WeakTopicTracker.
Run: pytest tests/ -v
"""
from src.utils.tracker import WeakTopicTracker


class TestWeakTopicTracker:

    def setup_method(self):
        """Fresh tracker for each test."""
        self.tracker = WeakTopicTracker()

    def test_initial_state_empty(self):
        assert not self.tracker.has_data()
        assert self.tracker.total_questions() == 0
        assert self.tracker.get_weak_topics() == []

    def test_log_single_question(self):
        self.tracker.log_question("what is ansible")
        assert self.tracker.has_data()
        assert self.tracker.total_questions() == 1

    def test_log_multiple_questions(self):
        questions = [
            "explain docker containers",
            "what is kubernetes orchestration",
            "how does docker networking work",
        ]
        for q in questions:
            self.tracker.log_question(q)
        assert self.tracker.total_questions() == 3

    def test_stop_words_filtered(self):
        self.tracker.log_question("what is the difference between a and b")
        topics = self.tracker.get_weak_topics()
        topic_names = [t[0] for t in topics]
        # Stop words should not appear
        for stop_word in ["what", "is", "the", "between", "and"]:
            assert stop_word not in topic_names

    def test_frequent_topic_ranks_higher(self):
        for _ in range(5):
            self.tracker.log_question("explain ansible playbooks")
        self.tracker.log_question("what is docker")

        topics = self.tracker.get_weak_topics()
        top_topic = topics[0][0]
        assert top_topic in ("ansible", "playbooks", "explain")

    def test_get_top_topic_names_returns_strings(self):
        self.tracker.log_question("kubernetes pods and services")
        names = self.tracker.get_top_topic_names(3)
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)

    def test_get_top_topic_names_respects_limit(self):
        for i in range(20):
            self.tracker.log_question(f"topic{i} concept{i} definition{i}")
        names = self.tracker.get_top_topic_names(5)
        assert len(names) <= 5

    def test_empty_question_handled(self):
        self.tracker.log_question("")
        assert self.tracker.total_questions() == 1
        # Should not crash, may produce no keywords
