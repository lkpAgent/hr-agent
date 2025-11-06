import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Robustly load DATABASE_URL from app settings or environment
def load_database_url() -> str:
    # Ensure backend directory is on sys.path so `app.core.config` can be imported
    this_file = Path(__file__).resolve()
    backend_dir = this_file.parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.append(str(backend_dir))

    db_url = None
    try:
        from app.core.config import settings
        db_url = settings.DATABASE_URL
    except Exception:
        # Fallback to environment variables
        db_url = os.getenv("DATABASE_URL") or os.getenv("PG_CONNECTION_STRING")

    if not db_url:
        raise RuntimeError("DATABASE_URL not configured. Set env or app settings.")

    # Convert asyncpg URL to sync URL for SQLAlchemy create_engine
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return db_url

SQL_STATEMENTS = [
    """
    CREATE INDEX IF NOT EXISTS idx_lc_embedding_document_tsv
      ON langchain_pg_embedding
      USING GIN (to_tsvector('simple', document));
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_lc_embedding_cmetadata_gin
      ON langchain_pg_embedding
      USING GIN (cmetadata);
    """
]

def main():
    database_url = load_database_url()
    engine = create_engine(database_url)
    with engine.begin() as conn:
        for sql in SQL_STATEMENTS:
            conn.execute(text(sql))
    print("TSVector and JSONB indices ensured on langchain_pg_embedding")

if __name__ == "__main__":
    main()