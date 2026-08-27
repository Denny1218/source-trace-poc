import sqlite3
from pathlib import Path

from app.core.config import DATABASE_PATH
from app.core.logging import get_logger
from app.db.migrations import run_migrations

logger = get_logger()


def get_db_path() -> Path:
    return Path(DATABASE_PATH)


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database() -> None:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        run_migrations(conn)
        logger.info("Database initialized path=%s", db_path)
    finally:
        conn.close()


def check_database() -> str:
    """Return 'ok' if database is accessible, otherwise 'error'."""
    try:
        db_path = get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("SELECT 1")
            return "ok"
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Database check failed: %s", exc)
        return "error"
