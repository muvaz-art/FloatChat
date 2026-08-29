from __future__ import annotations

import os
import urllib.request

from rag.pipeline import RAGPipeline
from rag.vector_store import LocalVectorStore


def main() -> None:
    checks = {"rag": False, "streamlit": False}
    rag = RAGPipeline(LocalVectorStore(os.getenv("VECTOR_STORE_PATH", "data/vector_store.json")))
    checks["rag"] = bool(rag.retrieve_context("ARGO salinity profile"))
    port = os.getenv("STREAMLIT_PORT", "8501")
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=3)
        checks["streamlit"] = True
    except OSError:
        checks["streamlit"] = False
    for name, passed in checks.items():
        print(f"{name}: {'OK' if passed else 'UNAVAILABLE'}")
    if not checks["rag"]:
        raise SystemExit("RAG health check failed")
    if not checks["streamlit"]:
        raise SystemExit("Streamlit health check failed")


if __name__ == "__main__":
    main()
