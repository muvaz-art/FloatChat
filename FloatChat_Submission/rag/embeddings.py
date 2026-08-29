from rag.vector_store import LocalVectorStore


def generate_metadata_embedding(text: str):
    """Generate a deterministic local embedding compatible with the vector store."""
    return LocalVectorStore()._embed(text).tolist()
