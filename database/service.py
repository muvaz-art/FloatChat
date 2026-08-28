from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from app.query_plan import QueryPlan
from database.connection import get_db_engine
from database.queries import build_measurement_select


class PostgresExecutor:
    """Read-only executor that uses the same validated QueryPlan as demo mode."""
    def __init__(self, engine=None):
        self.engine = engine or get_db_engine()
        if self.engine is None:
            raise RuntimeError("PostgreSQL is not available")

    def execute(self, plan: QueryPlan) -> tuple[pd.DataFrame, pd.DataFrame]:
        plan = QueryPlan.model_validate(plan)
        sql, params = build_measurement_select(plan)
        with self.engine.connect() as connection:
            measurements = pd.read_sql(text(sql), connection, params=params)
        floats = measurements[["float_id", "latitude", "longitude", "status", "region"]].drop_duplicates("float_id")
        return floats, measurements
