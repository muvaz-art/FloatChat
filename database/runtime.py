from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from database.connection import get_db_engine


def load_postgres_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    engine = get_db_engine()
    if engine is None:
        raise RuntimeError("PostgreSQL engine could not be created")
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        floats = pd.read_sql(text("SELECT float_id, latitude, longitude, status, max_depth, region, source_file FROM floats"), connection)
        profiles = pd.read_sql(text("SELECT profile_id, float_id, timestamp, latitude, longitude, source_file FROM profiles"), connection)
        measurements = pd.read_sql(text("SELECT profile_id, depth, pressure, temperature, salinity, oxygen, chlorophyll, bbp700, nitrate, ph FROM measurements LIMIT 100000"), connection)
    measurements = measurements.merge(profiles[["profile_id", "float_id", "timestamp", "latitude", "longitude"]], on="profile_id", how="left")
    return floats, profiles, measurements
