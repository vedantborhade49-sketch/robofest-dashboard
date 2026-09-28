import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

Base = declarative_base()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "aerosar.db")

engine = None
SessionLocal = None
_db_initialized = False


def resolve_db_path(db_path: str | None = None) -> str:
    """Resolve the SQLite database path from explicit args or environment config."""
    if db_path:
        resolved = db_path
    else:
        resolved = os.getenv("AEROSAR_DB_PATH") or os.getenv("APP_DB_PATH") or DEFAULT_DB_PATH

    db_dir = os.path.dirname(resolved)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    return resolved


def init_db(db_path: str | None = None) -> bool:
    global engine, SessionLocal, _db_initialized

    resolved_path = resolve_db_path(db_path)

    if _db_initialized and engine is not None and SessionLocal is not None:
        return True

    try:
        engine = create_engine(
            f"sqlite:///{resolved_path}",
            connect_args={"check_same_thread": False}
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        import app.database.models  # noqa

        Base.metadata.create_all(bind=engine)
        _db_initialized = True
        return True
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        return False


def get_session():
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
