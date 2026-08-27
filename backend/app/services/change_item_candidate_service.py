"""Change-item keyword search from structured cache (STEP 6)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.ppt_fallback_config import CHANGE_ITEM_CANDIDATE_LIMIT, CHANGE_ITEM_SCORE_CONFIG
from app.services.change_item_cache_service import ChangeItemCacheRow
from app.services.ppt_candidate_service import _scorable_keywords

logger = get_logger()


@dataclass
class ChangeItemCandidate:
    change_item_cache_id: int
    document_cache_id: int
    slide_no: int
    file_path: str
    file_name: str
    item_no: str | None
    change_title: str | None
    csr_no: str | None
    business_background: str | None
    current_status: str | None
    as_is: str | None
    to_be: str | None
    source_functions: list[dict]
    test_cases: list[str]
    applicable_scopes: list[str]
    raw_text: str
    matched_keywords: list[str]
    candidate_score: int
    from_cache_search: bool = False
    from_fallback: bool = False
    equipment_id: int | None = None
    # Evidence-only (not used by STEP 6 PPT analysis response mapping unless set).
    query_match_reasons: list = field(default_factory=list)
    query_relevance_score: int = 0
    query_relevance_level: str = "없음"


def _normalize(text: str) -> str:
    return text.lower()


def _keyword_in_text(keyword: str, text: str | None) -> bool:
    if not text:
        return False
    return _normalize(keyword) in _normalize(text)


def _load_json_list(raw: str) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _source_function_texts(source_functions: list[dict]) -> list[str]:
    texts: list[str] = []
    for entry in source_functions:
        raw = entry.get("raw_text")
        if raw:
            texts.append(str(raw))
        path = entry.get("file_path")
        if path:
            texts.append(str(path))
        for func in entry.get("functions") or []:
            texts.append(str(func))
    return texts


def _score_change_item(
    row: ChangeItemCacheRow,
    keywords: list[str],
) -> tuple[int, list[str]]:
    cfg = CHANGE_ITEM_SCORE_CONFIG
    matched: list[str] = []
    score = 0

    source_functions = _load_json_list(row.source_functions_json)
    source_texts = _source_function_texts(source_functions)

    field_checks: list[tuple[str, str | None, int]] = [
        ("change_title", row.change_title, cfg["change_title"]),
        ("csr_no", row.csr_no, cfg["csr_no"]),
        ("business_background", row.business_background, cfg["business_background"]),
        ("current_status", row.current_status, cfg["current_status"]),
        ("as_is", row.as_is, cfg["as_is"]),
        ("to_be", row.to_be, cfg["to_be"]),
        ("raw_text", row.raw_text, cfg["raw_text"]),
    ]

    for _name, value, weight in field_checks:
        if not value:
            continue
        if any(_keyword_in_text(kw, value) for kw in keywords):
            score += weight
            for kw in keywords:
                if _keyword_in_text(kw, value) and kw not in matched:
                    matched.append(kw)

    if any(_keyword_in_text(kw, text) for kw in keywords for text in source_texts):
        score += cfg["source_function"]
        for kw in keywords:
            if any(_keyword_in_text(kw, text) for text in source_texts) and kw not in matched:
                matched.append(kw)

    if row.file_name:
        for kw in keywords:
            if _keyword_in_text(kw, row.file_name) and kw not in matched:
                matched.append(kw)

    return score, matched


def _to_candidate(
    row: ChangeItemCacheRow,
    keywords: list[str],
    *,
    from_cache_search: bool = False,
    from_fallback: bool = False,
) -> ChangeItemCandidate | None:
    score, matched = _score_change_item(row, keywords)
    if score == 0:
        return None
    return ChangeItemCandidate(
        change_item_cache_id=row.id,
        document_cache_id=row.document_cache_id,
        slide_no=row.slide_no,
        file_path=row.file_path or "",
        file_name=row.file_name or "",
        item_no=row.item_no,
        change_title=row.change_title,
        csr_no=row.csr_no,
        business_background=row.business_background,
        current_status=row.current_status,
        as_is=row.as_is,
        to_be=row.to_be,
        source_functions=_load_json_list(row.source_functions_json),
        test_cases=_load_json_list(row.test_cases_json),
        applicable_scopes=_load_json_list(row.applicable_scopes_json),
        raw_text=row.raw_text,
        matched_keywords=matched,
        candidate_score=score,
        from_cache_search=from_cache_search,
        from_fallback=from_fallback,
        equipment_id=row.equipment_id,
    )


def search_change_item_candidates(
    rows: list[ChangeItemCacheRow],
    keywords: list[str],
    limit: int | None = None,
    *,
    from_cache_search: bool = False,
    from_fallback: bool = False,
) -> list[ChangeItemCandidate]:
    scorable = _scorable_keywords(keywords)
    if not scorable:
        return []

    max_results = limit if limit is not None else CHANGE_ITEM_CANDIDATE_LIMIT
    results: list[ChangeItemCandidate] = []
    for row in rows:
        candidate = _to_candidate(
            row,
            scorable,
            from_cache_search=from_cache_search,
            from_fallback=from_fallback,
        )
        if candidate is not None:
            results.append(candidate)

    results.sort(
        key=lambda c: (-c.candidate_score, c.file_name.lower(), c.slide_no)
    )
    top = results[:max_results]
    logger.info("Change item candidate search count=%s", len(top))
    return top


def merge_change_item_candidates(
    primary: list[ChangeItemCandidate],
    secondary: list[ChangeItemCandidate],
    limit: int | None = None,
) -> list[ChangeItemCandidate]:
    max_results = limit if limit is not None else CHANGE_ITEM_CANDIDATE_LIMIT
    merged: dict[int, ChangeItemCandidate] = {}
    for candidate in primary:
        merged[candidate.change_item_cache_id] = candidate
    for candidate in secondary:
        merged.setdefault(candidate.change_item_cache_id, candidate)
    results = list(merged.values())
    results.sort(
        key=lambda c: (-c.candidate_score, c.file_name.lower(), c.slide_no)
    )
    return results[:max_results]
