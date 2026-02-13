from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from pathlib import Path


_db_url = settings.DATABASE_URL
if _db_url is None:
    raise ValueError(
        "DATABASE_URL is not set. Configure DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in .env"
    )
engine = create_engine(
    _db_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ===== DB 2: SQLite file ở project root =====
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/db/session.py -> project-root
SQLITE_PATH = BASE_DIR / "ping_results.db"

engine_sqlite = create_engine(
    f"sqlite:///{SQLITE_PATH}",
    connect_args={"check_same_thread": False},  # quan trọng khi chạy FastAPI
    pool_pre_ping=True,
)

SessionSQLite = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_sqlite,
)
