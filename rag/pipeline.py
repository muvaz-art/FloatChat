from __future__ import annotations

from rag.documents import DOCUMENTS
from rag.vector_store import LocalVectorStore


class RAGPipeline:
    def __init__(self, store: LocalVectorStore | None = None):
        self.store = store or LocalVectorStore()
        self.store.load()
        if not self.store.documents:
            self.store.add_documents(DOCUMENTS)
            self.store.save()

    def retrieve_context(self, question: str, top_k: int = 4) -> list[dict]:
        return self.store.search(question, top_k=top_k)

    def context_text(self, question: str, top_k: int = 4) -> str:
        return "\n".join(item["text"] for item in self.retrieve_context(question, top_k))
