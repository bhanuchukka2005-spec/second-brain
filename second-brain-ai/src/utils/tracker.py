"""Tracks which topics the student asks about most."""
from collections import Counter
import re
from typing import List

STOP_WORDS = {
    "what", "is", "the", "a", "an", "how", "why", "when", "where", "who",
    "does", "do", "can", "could", "tell", "me", "about", "explain", "my",
    "notes", "in", "of", "and", "or", "to", "from", "with", "for", "on",
    "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "this", "that", "these", "those", "it", "its", "i", "you", "your",
    "difference", "between", "also", "just", "like", "use", "used", "using",
    "get", "got", "make", "made", "give", "given", "show", "shows", "know",
}


class WeakTopicTracker:
    def __init__(self):
        self.question_log: List[str] = []
        self.keyword_counter: Counter = Counter()

    def log_question(self, question: str):
        self.question_log.append(question)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
        keywords = [w for w in words if w not in STOP_WORDS]
        self.keyword_counter.update(keywords)

    def get_weak_topics(self, top_n: int = 10) -> List[tuple]:
        return self.keyword_counter.most_common(top_n)

    def get_top_topic_names(self, top_n: int = 5) -> List[str]:
        return [topic for topic, _ in self.get_weak_topics(top_n)]

    def has_data(self) -> bool:
        return len(self.question_log) > 0

    def total_questions(self) -> int:
        return len(self.question_log)
