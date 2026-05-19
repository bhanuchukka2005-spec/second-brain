"""Adaptive quiz engine — parses MCQ text and tracks difficulty."""
import re
from typing import List


def parse_mcqs(raw_text: str) -> List[dict]:
    questions = []
    blocks = re.split(r"\n(?=Q\d+\.)", raw_text.strip())
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        q: dict = {"question": "", "options": {}, "answer": "", "explanation": ""}
        for line in lines:
            if re.match(r"Q\d+\.", line):
                q["question"] = re.sub(r"Q\d+\.\s*", "", line)
            elif re.match(r"^[A-D]\)", line):
                key = line[0]
                q["options"][key] = line[3:].strip()
            elif line.lower().startswith("answer:"):
                q["answer"] = line.split(":", 1)[1].strip().upper()[:1]
            elif line.lower().startswith("explanation:"):
                q["explanation"] = line.split(":", 1)[1].strip()
        if q["question"] and q["options"] and q["answer"]:
            questions.append(q)
    return questions


def get_difficulty_prompt(wrong_topics: List[str]) -> str:
    if not wrong_topics:
        return ""
    return f"\nMake questions harder on these topics where the student struggled: {', '.join(wrong_topics)}."
