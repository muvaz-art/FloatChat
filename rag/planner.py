from rag.pipeline import RAGPipeline


def generate_rag_query_plan(query: str) -> dict:
    """Return a retrieval-grounded planning envelope for the application planner."""
    context = RAGPipeline().retrieve_context(query)
    return {"query": query, "retrieved_context": context, "context_text": "\n".join(item["text"] for item in context)}
