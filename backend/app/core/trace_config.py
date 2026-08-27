"""Trace Git Candidate scoring configuration."""

TRACE_SCORE_CONFIG = {
    "file_path": 30,
    "diff_symbol": 25,
    "commit_message": 20,
    "diff_keyword": 20,
    "context": 5,
}

TOP_CANDIDATE_LIMIT = 5
SEARCH_CONTEXT_DATE_WINDOW_DAYS = 90
