import os
import sqlalchemy

def get_db_engine():
    """Establishes PostgreSQL connection with safe fallback handling."""
    db_url = os.getenv("DATABASE_URL", "postgresql://floatchat_user:floatchat_pass@localhost:5432/floatchat_db")
    try:
        engine = sqlalchemy.create_engine(db_url, connect_args={"connect_timeout": 2})
        return engine
    except Exception:
        return None
