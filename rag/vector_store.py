from __future__ import annotations

import json
from pathlib import Path
import re
import numpy as np


class LocalVectorStore:
    """Small dependency-free persistent semantic store for project documentation."""
    def __init__(self, path: str = "data/vector_store.json", dimensions: int = 384):
        self.path = Path(path)
        self.dimensions = dimensions
        self.documents: list[dict] = []

    def _embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=float)
        tokens = re.findall(r"[a-z0-9_]+", text.lower())
        for token in tokens:
            vector[hash(token) % self.dimensions] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def add_documents(self, documents: list[dict]) -> None:
        existing = {doc["id"]: doc for doc in self.documents}
        for document in documents:
            existing[document["id"]] = {"id": document["id"], "text": document["text"]}
        self.documents = list(existing.values())

    def search(self, query: str, top_k: int = 4) -> list[dict]:
        query_vector = self._embed(query)
        scored = [(float(np.dot(query_vector, self._embed(doc["text"]))), doc) for doc in self.documents]
        return [dict(doc, score=round(score, 4)) for score, doc in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"dimensions": self.dimensions, "documents": self.documents}, indent=2), encoding="utf-8")

    def load(self) -> "LocalVectorStore":
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.dimensions = payload.get("dimensions", self.dimensions)
            self.documents = payload.get("documents", [])
        return self

    def clear(self) -> None:
        self.documents = []
        if self.path.exists():
            self.path.unlink()
