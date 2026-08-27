"""STEP 7: on-demand Evidence Link computation with lazy `change_link` cache reuse.

Only called for the bounded Git Top 5 x Change Item Top N pairing performed
by `evidence_service.py` — never for a full Cartesian product over the whole
database (see PROJECT_SPEC v2 STEP 7 section 11)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.core.link_score_config import LINKER_VERSION
from app.core.logging import get_logger
from app.db.database import get_connection
from app.schemas.trace import GitCandidate
from app.services.change_item_cache_service import ChangeItemCacheRow
from app.services.link_score_service import (
    ChangeItemEvidenceInput,
    GitEvidenceInput,
    LinkScoreResult,
    MatchReason,
    compute_link_score,
    evaluate_gate,
)
from app.services.trace_service import get_commit_change_diff

logger = get_logger()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_source_functions(raw_json: str) -> list[dict]:
    if not raw_json:
        return []
    try:
        data = json.loads(raw_json)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _build_change_item_input(row: ChangeItemCacheRow) -> ChangeItemEvidenceInput:
    return ChangeItemEvidenceInput(
        change_title=row.change_title,
        csr_no=row.csr_no,
        business_background=row.business_background,
        current_status=row.current_status,
        as_is=row.as_is,
        to_be=row.to_be,
        raw_text=row.raw_text,
        source_functions=_load_source_functions(row.source_functions_json),
        file_name=row.file_name,
    )


def _row_to_result(row: sqlite3.Row) -> LinkScoreResult:
    raw_reasons = json.loads(row["match_reasons_json"]) if row["match_reasons_json"] else []
    reasons = [MatchReason(**r) for r in raw_reasons]
    return LinkScoreResult(
        score=row["link_score"],
        match_reasons=reasons,
        passes_gate=evaluate_gate(reasons),
    )


def get_or_compute_change_link(
    git_candidate: GitCandidate,
    change_item_row: ChangeItemCacheRow,
) -> LinkScoreResult:
    """Reuse a cached rule-based Link Score when available, else compute + persist.

    Link Score depends only on intrinsic Git commit/file content and intrinsic
    Change Item content — never on the user's search query — so caching per
    (commit, file, change_item, linker_version) is always valid regardless of
    which query produced this pairing."""
    conn = get_connection()
    try:
        cached = conn.execute(
            """
            SELECT link_score, match_reasons_json
            FROM change_link
            WHERE git_commit_id = ? AND git_file_path = ?
              AND change_item_cache_id = ? AND linker_version = ?
            """,
            (
                git_candidate.commit_id,
                git_candidate.file_path,
                change_item_row.id,
                LINKER_VERSION,
            ),
        ).fetchone()
        if cached is not None:
            return _row_to_result(cached)
    finally:
        conn.close()

    diff = get_commit_change_diff(git_candidate.commit_id, git_candidate.file_path)
    git_input = GitEvidenceInput(
        file_path=git_candidate.file_path,
        message=git_candidate.message,
        diff=diff,
        commit_date=git_candidate.commit_date,
    )
    item_input = _build_change_item_input(change_item_row)
    result = compute_link_score(git_input, item_input)

    _store_change_link(git_candidate, change_item_row.id, result)
    return result


def _store_change_link(
    git_candidate: GitCandidate,
    change_item_cache_id: int,
    result: LinkScoreResult,
) -> None:
    now = _now_iso()
    reasons_json = json.dumps(
        [r.to_dict() for r in result.match_reasons], ensure_ascii=False
    )
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO change_link
                (git_commit_id, git_file_path, change_item_cache_id, link_score,
                 match_reasons_json, linker_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (git_commit_id, git_file_path, change_item_cache_id, linker_version)
            DO UPDATE SET
                link_score = excluded.link_score,
                match_reasons_json = excluded.match_reasons_json,
                updated_at = excluded.updated_at
            """,
            (
                git_candidate.commit_id,
                git_candidate.file_path,
                change_item_cache_id,
                result.score,
                reasons_json,
                LINKER_VERSION,
                now,
                now,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # FK race (e.g. change_item deleted between compute and store) — the
        # link is simply not cached; the caller already has the computed
        # result in-memory for this request.
        conn.rollback()
        logger.warning(
            "change_link store skipped (integrity) commit_id=%s change_item_cache_id=%s",
            git_candidate.commit_id,
            change_item_cache_id,
        )
    finally:
        conn.close()


def delete_links_for_change_item(change_item_cache_id: int) -> None:
    """Explicit helper for callers that want to force-invalidate without
    waiting for FK cascade (e.g. future re-linking tools). Not required for
    normal operation — cascade delete already handles this automatically."""
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM change_link WHERE change_item_cache_id = ?",
            (change_item_cache_id,),
        )
        conn.commit()
    finally:
        conn.close()
