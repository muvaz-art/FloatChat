from rag.pipeline import RAGPipeline


def retrieve_schema_context(query: str, top_k: int = 4) -> str:
    """Retrieve relevant ARGO documentation for a question."""
    return RAGPipeline().context_text(query, top_k=top_k)
