import re

"""
Concept map generator.
Takes notes context and produces a Mermaid diagram string
that Streamlit can render as an interactive mind map.
"""


def parse_mermaid_from_response(raw: str) -> str:
    """Extract mermaid block from LLM response."""
    match = re.search(r"```mermaid\s*(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If LLM returned raw mermaid without fences
    if "graph" in raw or "mindmap" in raw:
        return raw.strip()
    return ""


def get_concept_map_prompt(context: str, topic: str = "") -> str:
    focus = f"Focus on the topic: {topic}." if topic.strip() else "Cover the key concepts."
    return f"""You are an expert educator. Based on the study material below, create a concept map as a Mermaid mindmap diagram.

Rules:
- Use mindmap syntax (mindmap keyword)
- Root node should be the main subject
- Max 3 levels deep
- Max 20 nodes total
- Node text must be short (3-5 words max)
- Return ONLY the mermaid code block, nothing else

{focus}

STUDY MATERIAL:
{context}

Return:
```mermaid
mindmap
  root((Main Topic))
    ...
```"""
