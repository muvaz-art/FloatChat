from rag.pipeline import RAGPipeline
from rag.vector_store import LocalVectorStore


def test_local_rag_retrieves_schema_context(tmp_path):
    pipeline = RAGPipeline(LocalVectorStore(str(tmp_path / "vectors.json")))
    results = pipeline.retrieve_context("How do I find salinity by depth?")
    assert results
    assert any("Salinity" in item["text"] or "measurements" in item["text"] for item in results)
