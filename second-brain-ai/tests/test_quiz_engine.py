"""Unit tests for quiz_engine MCQ parser."""
from src.features.quiz_engine import parse_mcqs, get_difficulty_prompt

SAMPLE = """
Q1. What is Ansible used for?
A) Database management
B) Configuration management and automation
C) Network monitoring
D) Code compilation
Answer: B
Explanation: Ansible is used for configuration management.

Q2. What format do Playbooks use?
A) JSON
B) XML
C) YAML
D) TOML
Answer: C
Explanation: Ansible Playbooks are written in YAML.
"""


class TestParseMCQs:
    def test_parses_correct_number(self):
        assert len(parse_mcqs(SAMPLE)) == 2

    def test_question_text_extracted(self):
        assert "Ansible" in parse_mcqs(SAMPLE)[0]["question"]

    def test_all_options_present(self):
        assert set(parse_mcqs(SAMPLE)[0]["options"].keys()) == {"A", "B", "C", "D"}

    def test_correct_answer_extracted(self):
        qs = parse_mcqs(SAMPLE)
        assert qs[0]["answer"] == "B"
        assert qs[1]["answer"] == "C"

    def test_empty_text_returns_empty(self):
        assert parse_mcqs("") == []

    def test_malformed_returns_empty(self):
        assert parse_mcqs("random text no format") == []


class TestGetDifficultyPrompt:
    def test_empty_returns_empty(self):
        assert get_difficulty_prompt([]) == ""

    def test_topics_in_prompt(self):
        p = get_difficulty_prompt(["docker", "kubernetes"])
        assert "docker" in p and "kubernetes" in p
