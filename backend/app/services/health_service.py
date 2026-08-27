import shutil
import subprocess

import httpx

from app.core.config import OLLAMA_BASE_URL
from app.core.logging import get_logger
from app.db.database import check_database

logger = get_logger()


def check_git() -> str:
    """Return 'available' if git CLI is usable, otherwise 'unavailable'."""
    if shutil.which("git") is None:
        return "unavailable"
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        if result.returncode == 0:
            return "available"
        logger.warning("Git version check failed: %s", result.stderr)
        return "unavailable"
    except Exception as exc:
        logger.error("Git check failed: %s", exc)
        return "unavailable"


def check_ollama() -> str:
    """Return 'available' if Ollama responds, otherwise 'unavailable'."""
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
            if response.status_code == 200:
                return "available"
        logger.info("Ollama unavailable: status=%s", response.status_code)
        return "unavailable"
    except Exception as exc:
        logger.info("Ollama unavailable: %s", exc)
        return "unavailable"


def get_health_status() -> dict:
    database = check_database()
    git = check_git()
    ollama = check_ollama()

    status = "ok" if database == "ok" else "degraded"

    return {
        "status": status,
        "database": database,
        "git": git,
        "ollama": ollama,
    }
