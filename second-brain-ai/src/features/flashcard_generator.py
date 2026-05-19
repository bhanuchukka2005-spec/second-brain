"""Flashcard generator — Anki-compatible CSV/JSON export."""
import csv
import io
import json
import re
from typing import List


def parse_flashcards_from_text(raw: str) -> List[dict]:
    cards = []
    blocks = re.split(r"-{3,}", raw)
    for block in blocks:
        front_match = re.search(r"FRONT:\s*(.+?)(?=BACK:|$)", block, re.DOTALL | re.IGNORECASE)
        back_match = re.search(r"BACK:\s*(.+?)$", block, re.DOTALL | re.IGNORECASE)
        if front_match and back_match:
            cards.append({
                "front": front_match.group(1).strip(),
                "back": back_match.group(1).strip()
            })
    return cards


def export_to_csv(cards: List[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Front", "Back"])
    for card in cards:
        writer.writerow([card["front"], card["back"]])
    return output.getvalue()


def export_to_json(cards: List[dict]) -> str:
    return json.dumps(cards, indent=2)
