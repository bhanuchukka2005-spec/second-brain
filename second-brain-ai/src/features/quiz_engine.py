"""
Adaptive quiz engine.
Parses MCQ text into structured questions and tracks score.
Gets harder based on wrong answers.
"""
import re
from typing import List


def parse_mcqs(raw_text: str) -> List[dict]:
    """
    Parse LLM-generated MCQ text into structured list of dicts.
    Each dict: {question, options: {A,B,C,D}, answer, explanation}
    """
    questions = []
    # Split on Q1., Q2. etc.
    blocks = re.split(r"\n(?=Q\d+\.)", raw_text.strip())

    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue

        q = {"question": "", "options": {}, "answer": "", "explanation": ""}

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
    """Return an instruction to make questions harder on specific weak topics."""
    if not wrong_topics:
        return ""
    return f"\nMake questions harder on these topics where the student struggled: {', '.join(wrong_topics)}."
