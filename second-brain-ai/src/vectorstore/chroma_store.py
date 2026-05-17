from typing import List
import chromadb
from chromadb.utils import embedding_functions


class ChromaStore:
    def __init__(self, collection_name: str = "second_brain"):
        self.client = chromadb.Client()
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        self.collection = self.client.create_collection(
            name=collection_name,
            embedding_function=self.ef
        )

    def index(self, docs: List[dict]):
        if not docs:
            return
        texts = [d["text"] for d in docs]
        metadatas = [{"source": d["source"]} for d in docs]
        ids = [f"doc_{i}" for i in range(len(docs))]
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, n_results: int = 5) -> List[dict]:
        """Returns list of {text, source} dicts."""
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, count)
        )
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        return [{"text": d, "source": m.get("source", "")} for d, m in zip(docs, metas)]
