"""
Persistent ChromaDB vector store.
Each session gets its own collection stored on disk at data/chroma/{session_id}/
Collections survive backend restarts — no need to re-index after restarting.
"""
import os
import logging
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

CHROMA_BASE_DIR = os.getenv("CHROMA_DIR", "data/chroma")


def _get_chroma_path(session_id: int) -> str:
    path = os.path.join(CHROMA_BASE_DIR, str(session_id))
    os.makedirs(path, exist_ok=True)
    return path


class PersistentChromaStore:
    """ChromaDB store that persists to disk and survives backend restarts."""

    def __init__(self, session_id: int):
        self.session_id = session_id
        self.chroma_path = _get_chroma_path(session_id)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=f"session_{session_id}",
            embedding_function=self.ef
        )
        logger.info(
            "ChromaStore ready: session=%d path=%s docs=%d",
            session_id, self.chroma_path, self.collection.count()
        )

    def index(self, docs: List[dict]) -> None:
        if not docs:
            return
        existing = set()
        try:
            existing = set(self.collection.get()["ids"])
        except Exception:
            pass

        texts, metadatas, ids = [], [], []
        for i, doc in enumerate(docs):
            doc_id = f"doc_{i}"
            if doc_id not in existing:
                texts.append(doc["text"])
                metadatas.append({"source": doc["source"]})
                ids.append(doc_id)

        if texts:
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
            logger.info("Indexed %d new chunks for session=%d", len(texts), self.session_id)

    def query(self, query_text: str, n_results: int = 5) -> List[dict]:
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(query_texts=[query_text], n_results=min(n_results, count))
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        return [{"text": d, "source": m.get("source", "")} for d, m in zip(docs, metas)]

    def count(self) -> int:
        return self.collection.count()

    @property
    def path(self) -> str:
        return self.chroma_path


_store_registry: Dict[int, PersistentChromaStore] = {}


def get_or_load_store(session_id: int) -> PersistentChromaStore:
    """Get from cache or load from disk — works immediately after restart."""
    if session_id not in _store_registry:
        store = PersistentChromaStore(session_id)
        _store_registry[session_id] = store
        logger.info("Loaded store from disk: session=%d docs=%d", session_id, store.count())
    return _store_registry[session_id]


def register_store(session_id: int, store: PersistentChromaStore) -> None:
    _store_registry[session_id] = store


def store_exists_on_disk(session_id: int) -> bool:
    path = os.path.join(CHROMA_BASE_DIR, str(session_id))
    return os.path.isdir(path) and len(os.listdir(path)) > 0