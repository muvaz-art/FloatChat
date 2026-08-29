from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import text

from database.connection import get_db_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize FloatChat PostgreSQL/PostGIS tables")
    parser.add_argument("--schema", type=Path, default=Path("database/init.sql"))
    args = parser.parse_args()
    engine = get_db_engine()
    if engine is None:
        raise SystemExit("Could not create a database engine. Check .env settings.")
    schema = args.schema.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.exec_driver_sql(schema)
        connection.execute(text("SELECT 1"))
    print("FloatChat database initialized successfully.")


if __name__ == "__main__":
    main()
