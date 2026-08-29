from __future__ import annotations

import json
from pathlib import Path
import re
import hashlib
import numpy as np


class LocalVectorStore:
    """Persistent semantic store with optional FAISS acceleration."""
    def __init__(self, path: str = "data/vector_store.json", dimensions: int = 384):
        self.path = Path(path)
        self.dimensions = dimensions
        self.documents: list[dict] = []
        self.index = None
        try:
            import faiss
            self._faiss = faiss
        except ImportError:
            self._faiss = None

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=float)
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            vector[int.from_bytes(digest[:8], "little") % self.dimensions] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def add_documents(self, documents: list[dict]) -> None:
        existing = {doc["id"]: doc for doc in self.documents}
        for document in documents:
            existing[document["id"]] = {"id": document["id"], "text": document["text"]}
        self.documents = list(existing.values())
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        if self._faiss is None or not self.documents:
            self.index = None
            return
        vectors = np.vstack([self._embed(doc["text"]) for doc in self.documents]).astype("float32")
        self.index = self._faiss.IndexFlatIP(self.dimensions)
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        query_vector = self._embed(query)
        if self.index is not None:
            scores, positions = self.index.search(query_vector.reshape(1, -1).astype("float32"), min(top_k, len(self.documents)))
            return [dict(self.documents[position], score=round(float(score), 4)) for score, position in zip(scores[0], positions[0]) if position >= 0]
        scored = [(float(np.dot(query_vector, self._embed(doc["text"]))), doc) for doc in self.documents]
        return [dict(doc, score=round(score, 4)) for score, doc in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"dimensions": self.dimensions, "documents": self.documents}, indent=2), encoding="utf-8")
        if self.index is not None:
            self._faiss.write_index(self.index, str(self.path.with_suffix(".faiss")))

    def load(self) -> "LocalVectorStore":
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.dimensions = payload.get("dimensions", self.dimensions)
            self.documents = payload.get("documents", [])
            index_path = self.path.with_suffix(".faiss")
            if self._faiss is not None and index_path.exists():
                self.index = self._faiss.read_index(str(index_path))
            else:
                self._rebuild_index()
        return self

    def clear(self) -> None:
        self.documents = []
        if self.path.exists():
            self.path.unlink()
        index_path = self.path.with_suffix(".faiss")
        if index_path.exists():
            index_path.unlink()
        self.index = None
