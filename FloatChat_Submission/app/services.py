from __future__ import annotations

import os

from app.query_engine import QueryEngine
from database.runtime import load_postgres_tables
from ingestion.demo_data import generate_demo_argo_data


def build_query_service(data_mode: str | None = None) -> tuple[QueryEngine, str]:
    mode = (data_mode or os.getenv("DATA_MODE", "demo")).lower()
    if mode == "postgres":
        return QueryEngine(*load_postgres_tables()), "REAL ARGO / POSTGRESQL"
    return QueryEngine(*generate_demo_argo_data(num_floats=80, profiles_per_float=3)), "DEMO / SYNTHETIC"
