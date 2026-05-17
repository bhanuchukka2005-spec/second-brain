"""
Unit tests for quiz_engine MCQ parser.
"""
from src.features.quiz_engine import parse_mcqs, get_difficulty_prompt


SAMPLE_MCQ_TEXT = """
Q1. What is the main purpose of Ansible?
A) Database management
B) Configuration management and automation
C) Network monitoring
D) Code compilation
Answer: B
Explanation: Ansible is primarily used for configuration management and IT automation.

Q2. Which file format do Ansible Playbooks use?
A) JSON
B) XML
C) YAML
D) TOML
Answer: C
Explanation: Ansible Playbooks are written in YAML format.
"""


class TestParseMCQs:

    def test_parses_correct_number_of_questions(self):
        questions = parse_mcqs(SAMPLE_MCQ_TEXT)
        assert len(questions) == 2

    def test_question_text_extracted(self):
        questions = parse_mcqs(SAMPLE_MCQ_TEXT)
        assert "Ansible" in questions[0]["question"]

    def test_all_options_present(self):
        questions = parse_mcqs(SAMPLE_MCQ_TEXT)
        q = questions[0]
        assert set(q["options"].keys()) == {"A", "B", "C", "D"}

    def test_correct_answer_extracted(self):
        questions = parse_mcqs(SAMPLE_MCQ_TEXT)
        assert questions[0]["answer"] == "B"
        assert questions[1]["answer"] == "C"

    def test_explanation_extracted(self):
        questions = parse_mcqs(SAMPLE_MCQ_TEXT)
        assert "configuration management" in questions[0]["explanation"].lower()

    def test_empty_text_returns_empty_list(self):
        assert parse_mcqs("") == []

    def test_malformed_text_returns_empty_list(self):
        assert parse_mcqs("This is just random text with no MCQ format") == []

    def test_partial_question_skipped(self):
        partial = "Q1. Incomplete question\nA) Only one option"
        result = parse_mcqs(partial)
        assert len(result) == 0  # no answer field, should be skipped


class TestGetDifficultyPrompt:

    def test_empty_topics_returns_empty_string(self):
        assert get_difficulty_prompt([]) == ""

    def test_topics_included_in_prompt(self):
        prompt = get_difficulty_prompt(["docker", "kubernetes"])
        assert "docker" in prompt
        assert "kubernetes" in prompt

    def test_returns_string(self):
        assert isinstance(get_difficulty_prompt(["ansible"]), str)
