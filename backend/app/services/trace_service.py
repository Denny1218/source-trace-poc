"""Trace search: Git Candidate ranking and Search Context generation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.logging import get_logger
from app.core.trace_config import (
    SEARCH_CONTEXT_DATE_WINDOW_DAYS,
    TOP_CANDIDATE_LIMIT,
    TRACE_SCORE_CONFIG,
)
from app.db.database import get_connection
from app.schemas.trace import GitCandidate, SearchContext, TraceSearchResponse
from app.services.equipment_service import get_equipment
from app.services.keyword_extractor import extract_keywords, symbol_keywords

logger = get_logger()


class TraceSearchError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def _paths_match(stored: str, requested: str) -> bool:
    s = _normalize_path(stored)
    r = _normalize_path(requested)
    if s == r:
        return True
    return s.endswith("/" + r) or r.endswith("/" + s) or s.split("/")[-1] == r.split("/")[-1]


def _contains_keyword(text: str | None, keywords: list[str]) -> str | None:
    if not text:
        return None
    lower = text.lower()
    for kw in keywords:
        if kw.lower() in lower or kw in text:
            return kw
    return None


def _score_candidate(
    commit_message: str,
    change_file_path: str,
    diff: str | None,
    keywords: list[str],
    symbols: list[str],
    request_file_path: str | None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    if request_file_path and _paths_match(change_file_path, request_file_path):
        score += TRACE_SCORE_CONFIG["file_path"]
        reasons.append("file_path")

    if symbols and diff:
        for sym in symbols:
            if sym in diff:
                score += TRACE_SCORE_CONFIG["diff_symbol"]
                reasons.append("diff_symbol")
                break

    if _contains_keyword(commit_message, keywords):
        score += TRACE_SCORE_CONFIG["commit_message"]
        if "commit_message_keyword" not in reasons:
            reasons.append("commit_message_keyword")

    if diff and _contains_keyword(diff, keywords):
        score += TRACE_SCORE_CONFIG["diff_keyword"]
        if "diff_keyword" not in reasons:
            reasons.append("diff_keyword")

    # Query/file context: file name keyword match without explicit file_path param
    file_name = change_file_path.replace("\\", "/").split("/")[-1]
    for kw in keywords:
        if kw.lower() == file_name.lower() or kw.lower() == file_name.rsplit(".", 1)[0].lower():
            score += TRACE_SCORE_CONFIG["context"]
            if "query_keyword" not in reasons:
                reasons.append("query_keyword")
            break

    if not reasons and keywords:
        # Generic query keyword in message or diff already partially covered;
        # mark query_keyword if any keyword matched message/diff/file
        matched = False
        for kw in keywords:
            if (
                kw in (commit_message or "")
                or kw in (diff or "")
                or kw.lower() in change_file_path.lower()
            ):
                matched = True
                break
        if matched:
            reasons.append("query_keyword")

    return min(score, 100), reasons


def _fetch_commit_changes(equipment_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                gr.id AS repository_id,
                gr.name AS repository_name,
                gc.id AS commit_id,
                gc.commit_hash,
                gc.commit_date,
                gc.message,
                gch.file_path,
                gch.diff
            FROM git_commit gc
            JOIN git_repository gr ON gr.id = gc.repository_id
            JOIN git_change gch ON gch.commit_id = gc.id
            WHERE gr.equipment_id = ?
            ORDER BY gc.commit_date DESC
            """,
            (equipment_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_commit_change_diff(commit_id: int, file_path: str) -> str | None:
    """Fetch the diff text for a specific (commit, file) Git Candidate.

    Reused by STEP 7 Link Score / Evidence Context — `GitCandidate` (the API
    response model) intentionally omits `diff` to keep `/api/trace/search`
    payloads small, so callers that need diff text look it up on demand."""
    record = get_git_change_record(commit_id, file_path)
    return record["diff"] if record else None


def get_git_change_record(commit_id: int, file_path: str) -> dict | None:
    """Return git_change row for exact (commit_id, file_path) — never shared across commits."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id, commit_id, file_path, diff, additions, deletions, change_type
            FROM git_change
            WHERE commit_id = ? AND file_path = ?
            LIMIT 1
            """,
            (commit_id, file_path),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _find_git_change_by_path(commit_id: int, file_path: str) -> dict | None:
    """Match git_change rows when candidate path differs from stored path (suffix/basename)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, commit_id, file_path, diff, additions, deletions, change_type
            FROM git_change
            WHERE commit_id = ?
            """,
            (commit_id,),
        ).fetchall()
        for row in rows:
            rec = dict(row)
            if _paths_match(rec["file_path"], file_path):
                return rec
        return None
    finally:
        conn.close()


def _fetch_live_commit_file_diff(commit_id: int, file_path: str) -> str | None:
    """Fallback: read exact file patch from local Git repo when DB diff is missing/incomplete."""
    try:
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT gc.commit_hash, gr.id AS repository_id
                FROM git_commit gc
                JOIN git_repository gr ON gr.id = gc.repository_id
                WHERE gc.id = ?
                LIMIT 1
                """,
                (commit_id,),
            ).fetchone()
            if not row:
                return None
            commit_hash = row["commit_hash"]
            repository_id = int(row["repository_id"])
        finally:
            conn.close()
    except Exception:
        return None

    try:
        from app.services.git_repository_service import get_working_path
        from app.services.git_service import fetch_commit_file_diff

        repo_path = get_working_path(repository_id)
        return fetch_commit_file_diff(repo_path, commit_hash, file_path)
    except Exception as exc:
        logger.info(
            "live git diff fallback skipped commit_id=%s file=%s err=%s",
            commit_id,
            file_path,
            type(exc).__name__,
        )
        return None


def resolve_git_change_record(
    commit_id: int,
    file_path: str,
    *,
    scope_path: str | None = None,
    allow_live_fallback: bool = True,
) -> tuple[dict | None, str]:
    """Resolve git_change for a commit with path alias and optional live Git fallback.

    Returns ``(record, diff_source)`` where diff_source is one of:
    ``exact_git_change``, ``path_alias_git_change``, ``live_git_show``, ``unavailable``.
    """
    record = get_git_change_record(commit_id, file_path)
    if record:
        return record, "exact_git_change"

    for alt in {scope_path, file_path}:
        if not alt or alt == file_path:
            continue
        alt_rec = get_git_change_record(commit_id, alt)
        if alt_rec:
            return alt_rec, "path_alias_git_change"

    alias = _find_git_change_by_path(commit_id, file_path)
    if alias:
        return alias, "path_alias_git_change"

    if allow_live_fallback:
        for path_try in dict.fromkeys(p for p in (file_path, scope_path) if p):
            live = _fetch_live_commit_file_diff(commit_id, path_try)
            if live:
                synthetic = {
                    "id": None,
                    "commit_id": commit_id,
                    "file_path": path_try,
                    "diff": live,
                    "additions": None,
                    "deletions": None,
                    "change_type": "modified",
                }
                return synthetic, "live_git_show"

    return None, "unavailable"


def _build_search_context(
    base_keywords: list[str], candidates: list[GitCandidate]
) -> SearchContext:
    keywords = set(base_keywords)
    for c in candidates:
        keywords.add(c.file_path.replace("\\", "/").split("/")[-1])
        stem = c.file_path.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
        keywords.add(stem)
        for reason in c.match_reasons:
            if reason == "diff_symbol":
                for kw in base_keywords:
                    if _UPPER_OR_IDENT(kw):
                        keywords.add(kw)

    dates: list[datetime] = []
    for c in candidates:
        try:
            dt = datetime.fromisoformat(c.commit_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dates.append(dt)
        except ValueError:
            continue

    if dates:
        min_d = min(dates)
        max_d = max(dates)
        window = timedelta(days=SEARCH_CONTEXT_DATE_WINDOW_DAYS)
        date_from = (min_d - window).date().isoformat()
        date_to = (max_d + window).date().isoformat()
    else:
        today = datetime.now(timezone.utc).date()
        date_from = (today - timedelta(days=SEARCH_CONTEXT_DATE_WINDOW_DAYS)).isoformat()
        date_to = (today + timedelta(days=SEARCH_CONTEXT_DATE_WINDOW_DAYS)).isoformat()

    return SearchContext(
        keywords=sorted(keywords),
        date_from=date_from,
        date_to=date_to,
    )


def _UPPER_OR_IDENT(kw: str) -> bool:
    return kw.isupper() or (len(kw) >= 3 and kw[0].isupper())


def search_trace(
    equipment_id: int,
    query: str,
    file_path: str | None = None,
    selected_code: str | None = None,
) -> TraceSearchResponse:
    if get_equipment(equipment_id) is None:
        raise TraceSearchError("장비를 찾을 수 없습니다.")

    keywords = extract_keywords(query, file_path, selected_code)
    symbols = symbol_keywords(keywords)

    logger.info(
        "Trace search started equipment_id=%s keyword_count=%s has_file_path=%s",
        equipment_id,
        len(keywords),
        bool(file_path),
    )

    rows = _fetch_commit_changes(equipment_id)
    scored: list[GitCandidate] = []
    seen: set[tuple[int, str]] = set()

    for row in rows:
        key = (row["commit_id"], row["file_path"])
        if key in seen:
            continue
        seen.add(key)

        score, reasons = _score_candidate(
            row["message"],
            row["file_path"],
            row["diff"],
            keywords,
            symbols,
            file_path,
        )

        if score == 0:
            continue

        scored.append(
            GitCandidate(
                repository_id=row["repository_id"],
                repository_name=row["repository_name"],
                commit_id=row["commit_id"],
                commit_hash=row["commit_hash"],
                commit_date=row["commit_date"],
                message=row["message"],
                file_path=row["file_path"],
                score=score,
                match_reasons=reasons,
            )
        )

    scored.sort(key=lambda c: (c.score, c.commit_date), reverse=True)
    top = scored[:TOP_CANDIDATE_LIMIT]

    search_context = _build_search_context(keywords, top)

    logger.info(
        "Trace search completed equipment_id=%s candidate_count=%s",
        equipment_id,
        len(top),
    )

    return TraceSearchResponse(
        equipment_id=equipment_id,
        query=query,
        git_candidates=top,
        search_context=search_context,
    )
