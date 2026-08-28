import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

def get_db_engine():
    """Establishes PostgreSQL connection with safe fallback handling."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            user=os.getenv("POSTGRES_USER", "floatchat_user"),
            password=os.getenv("POSTGRES_PASSWORD", "floatchat_pass"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "floatchat_db"),
        )
    try:
        engine = sqlalchemy.create_engine(db_url, connect_args={"connect_timeout": 2})
        return engine
    except Exception:
        return None
