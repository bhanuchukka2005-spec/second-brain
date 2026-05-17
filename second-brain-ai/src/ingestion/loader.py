import tempfile
import os
from typing import List
from PyPDF2 import PdfReader
from pptx import Presentation


def load_documents(uploaded_files) -> List[dict]:
    """
    Accepts Streamlit uploaded file objects.
    Returns a list of {text, source} dicts (chunked).
    """
    all_chunks = []

    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name

        try:
            if ext == "pdf":
                text = _read_pdf(tmp_path)
            elif ext == "pptx":
                text = _read_pptx(tmp_path)
            elif ext == "txt":
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            else:
                continue

            chunks = _chunk_text(text, source=file.name)
            all_chunks.extend(chunks)
        finally:
            os.unlink(tmp_path)

    return all_chunks


def _read_pdf(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_pptx(path: str) -> str:
    prs = Presentation(path)
    texts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
    return "\n".join(texts)


def _chunk_text(text: str, source: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append({"text": chunk, "source": source})
        i += chunk_size - overlap
    return chunks
