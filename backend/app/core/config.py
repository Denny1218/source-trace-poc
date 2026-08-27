import os
from pathlib import Path

from dotenv import load_dotenv

# Project root: equipment-change-trace/
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8010"))

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(PROJECT_ROOT / "data" / "equipment_change_trace.db"),
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
# STEP 8: Ollama Evidence Grounded Answer. Ollama 장애 시에도 Git/근거 검색은
# 계속 동작해야 하므로(원칙 13) 이 설정들은 AI 분석 단계에만 영향을 준다.
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").strip().lower() != "false"
# Default 60s (code default). Ops diagnosis may raise to 120 via .env —
# do not change the code default without measuring tiny-prompt latency first.
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))
# Tiny /api/trace/ollama-test uses this when set; else falls back to OLLAMA_TIMEOUT_SECONDS.
OLLAMA_TEST_TIMEOUT_SECONDS = float(
    os.getenv("OLLAMA_TEST_TIMEOUT_SECONDS", str(OLLAMA_TIMEOUT_SECONDS))
)

# Top Evidence Links only (원칙 15/16/17). TRACE_ANSWER_EVIDENCE_LIMIT aliases
# OLLAMA_MAX_EVIDENCE when set (ops diagnosis: try 1).
_evidence_limit_raw = (
    os.getenv("TRACE_ANSWER_EVIDENCE_LIMIT")
    or os.getenv("OLLAMA_MAX_EVIDENCE")
    or "3"
)
OLLAMA_MAX_EVIDENCE = int(_evidence_limit_raw)
TRACE_ANSWER_EVIDENCE_LIMIT = OLLAMA_MAX_EVIDENCE

# Prompt size knobs for STEP 8 only (Evidence search/link unchanged).
TRACE_ANSWER_MAX_DIFF_CHARS = int(os.getenv("TRACE_ANSWER_MAX_DIFF_CHARS", "1200"))
TRACE_ANSWER_MAX_FIELD_CHARS = int(os.getenv("TRACE_ANSWER_MAX_FIELD_CHARS", "400"))
TRACE_ANSWER_MAX_PROMPT_CHARS = int(os.getenv("TRACE_ANSWER_MAX_PROMPT_CHARS", "12000"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "app.log"

REPOSITORIES_ROOT = PROJECT_ROOT / "data" / "repositories"

# Yona server default read-only Git account for all remote Git access.
# User-pasted URL usernames are ignored. Password via Git Credential Manager (manager helper).
YONA_DEFAULT_USERNAME = (
    os.getenv("YONA_DEFAULT_USERNAME", "").strip()
    or os.getenv("YONA_GIT_USERNAME", "").strip()
    or None
)
# Deprecated alias — use YONA_DEFAULT_USERNAME
YONA_GIT_USERNAME = YONA_DEFAULT_USERNAME

PPT_CANDIDATE_LIMIT = int(os.getenv("PPT_CANDIDATE_LIMIT", "30"))
PPT_CANDIDATE_DATE_RANGE_DAYS = int(os.getenv("PPT_CANDIDATE_DATE_RANGE_DAYS", "90"))
