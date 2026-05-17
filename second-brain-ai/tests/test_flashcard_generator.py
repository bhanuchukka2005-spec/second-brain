"""
Unit tests for flashcard_generator module.
"""
from src.features.flashcard_generator import (
    parse_flashcards_from_text,
    export_to_csv,
    export_to_json,
)

SAMPLE_FLASHCARD_TEXT = """
FRONT: What is a Docker container?
BACK: A lightweight, standalone executable package that includes everything needed to run an application.
---
FRONT: What is the difference between CMD and ENTRYPOINT in Docker?
BACK: CMD provides default arguments that can be overridden, while ENTRYPOINT defines the main command that always runs.
---
FRONT: What is Docker Compose?
BACK: A tool for defining and running multi-container Docker applications using a YAML file.
---
"""


class TestParseFlashcards:

    def test_parses_correct_number(self):
        cards = parse_flashcards_from_text(SAMPLE_FLASHCARD_TEXT)
        assert len(cards) == 3

    def test_front_content_extracted(self):
        cards = parse_flashcards_from_text(SAMPLE_FLASHCARD_TEXT)
        assert "Docker container" in cards[0]["front"]

    def test_back_content_extracted(self):
        cards = parse_flashcards_from_text(SAMPLE_FLASHCARD_TEXT)
        assert len(cards[0]["back"]) > 10

    def test_empty_text_returns_empty_list(self):
        assert parse_flashcards_from_text("") == []

    def test_malformed_text_returns_empty(self):
        assert parse_flashcards_from_text("no front or back markers here") == []

    def test_card_has_required_keys(self):
        cards = parse_flashcards_from_text(SAMPLE_FLASHCARD_TEXT)
        for card in cards:
            assert "front" in card
            assert "back" in card


class TestExportFlashcards:

    def setup_method(self):
        self.cards = [
            {"front": "What is Ansible?", "back": "An automation tool"},
            {"front": "What is Terraform?", "back": "Infrastructure as code tool"},
        ]

    def test_csv_export_contains_header(self):
        csv = export_to_csv(self.cards)
        assert "Front" in csv
        assert "Back" in csv

    def test_csv_export_contains_data(self):
        csv = export_to_csv(self.cards)
        assert "Ansible" in csv
        assert "Terraform" in csv

    def test_json_export_is_valid(self):
        import json
        result = export_to_json(self.cards)
        parsed = json.loads(result)
        assert len(parsed) == 2

    def test_json_export_preserves_content(self):
        import json
        result = export_to_json(self.cards)
        parsed = json.loads(result)
        assert parsed[0]["front"] == "What is Ansible?"

    def test_empty_cards_csv(self):
        csv = export_to_csv([])
        assert "Front" in csv  # Header still present

    def test_empty_cards_json(self):
        import json
        result = export_to_json([])
        assert json.loads(result) == []
