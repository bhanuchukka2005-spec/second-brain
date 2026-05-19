"""Unit tests for flashcard_generator."""
import json
from src.features.flashcard_generator import parse_flashcards_from_text, export_to_csv, export_to_json

SAMPLE = """
FRONT: What is Docker?
BACK: A container platform.
---
FRONT: What is Kubernetes?
BACK: Container orchestration.
---
"""


class TestParseFlashcards:
    def test_parses_correct_number(self):
        assert len(parse_flashcards_from_text(SAMPLE)) == 2

    def test_keys_present(self):
        for c in parse_flashcards_from_text(SAMPLE):
            assert "front" in c and "back" in c

    def test_empty_returns_empty(self):
        assert parse_flashcards_from_text("") == []

    def test_malformed_returns_empty(self):
        assert parse_flashcards_from_text("no front or back here") == []


class TestExportFlashcards:
    def setup_method(self):
        self.cards = [{"front": "Q1", "back": "A1"}, {"front": "Q2", "back": "A2"}]

    def test_csv_has_header(self):
        assert "Front" in export_to_csv(self.cards)

    def test_csv_has_data(self):
        csv = export_to_csv(self.cards)
        assert "Q1" in csv and "A1" in csv

    def test_json_valid(self):
        parsed = json.loads(export_to_json(self.cards))
        assert len(parsed) == 2
        assert parsed[0]["front"] == "Q1"

    def test_empty_csv_has_header(self):
        assert "Front" in export_to_csv([])

    def test_empty_json(self):
        assert json.loads(export_to_json([])) == []
