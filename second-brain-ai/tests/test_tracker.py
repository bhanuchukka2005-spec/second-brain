"""Unit tests for WeakTopicTracker."""
from src.utils.tracker import WeakTopicTracker


class TestWeakTopicTracker:
    def setup_method(self):
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
        for q in ["explain docker", "what is kubernetes", "how does docker work"]:
            self.tracker.log_question(q)
        assert self.tracker.total_questions() == 3

    def test_stop_words_filtered(self):
        self.tracker.log_question("what is the difference between a and b")
        topics = [t[0] for t in self.tracker.get_weak_topics()]
        for sw in ["what", "is", "the", "difference", "between", "and"]:
            assert sw not in topics

    def test_frequent_topic_ranks_higher(self):
        for _ in range(5):
            self.tracker.log_question("explain ansible playbooks")
        self.tracker.log_question("what is docker")
        top = self.tracker.get_weak_topics()[0][0]
        assert top in ("ansible", "playbooks", "explain")

    def test_top_names_limit(self):
        for i in range(20):
            self.tracker.log_question(f"topic{i} concept{i} definition{i}")
        assert len(self.tracker.get_top_topic_names(5)) <= 5

    def test_empty_question_handled(self):
        self.tracker.log_question("")
        assert self.tracker.total_questions() == 1
