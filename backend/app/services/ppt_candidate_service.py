"""PPT file candidate search based on path metadata (no PPT parsing)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from app.core.logging import get_logger
from app.core.ppt_candidate_config import PPT_CANDIDATE_LIMIT, PPT_CANDIDATE_SCORE_CONFIG
from app.schemas.trace import SearchContext
from app.services.equipment_service import get_equipment
from app.services.document_path_utils import is_pptx_candidate
from app.services.equipment_name_utils import (
    filename_matches_equipment,
    is_document_for_equipment,
)
from app.services.ppt_date_parser import (
    SHORT_UPPER_TOKENS,
    extract_dates_from_path,
    parse_date_from_text,
    parse_iso_date,
    range_center,
)

logger = get_logger()


class PptCandidateSearchError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class PptCandidateResult:
    file_path: str
    file_name: str
    modified_at: str
    file_size: int
    candidate_score: int
    match_reasons: list[str]


@dataclass
class PptCandidateSearchResult:
    equipment_id: int
    scanned_files: int
    ppt_candidates: list[PptCandidateResult]
    equipment_filter_excluded: int = 0


def _normalize(text: str) -> str:
    return text.lower()


def _scorable_keywords(keywords: list[str]) -> list[str]:
    """Filter keywords for matching — trust STEP 4 extractor, add min-length guard."""
    result: list[str] = []
    for kw in keywords:
        if not kw or not kw.strip():
            continue
        kw = kw.strip()
        if any("\uac00" <= c <= "\ud7a3" for c in kw):
            if len(kw) >= 2:
                result.append(kw)
            continue
        if kw.upper() in SHORT_UPPER_TOKENS:
            result.append(kw)
            continue
        if kw.isupper() and len(kw) >= 2:
            result.append(kw)
            continue
        if len(kw) >= 3:
            result.append(kw)
    return result


def _date_proximity_score(
    file_date: date | None,
    date_from: str | None,
    date_to: str | None,
    max_score: int,
) -> int:
    """Score by distance from range center. Approximate when only date range exists."""
    if file_date is None or not date_from or not date_to:
        return 0

    start = parse_iso_date(date_from)
    end = parse_iso_date(date_to)
    if file_date < start or file_date > end:
        return 0

    center = range_center(date_from, date_to)
    half_range = max((end - start).days, 1)
    distance = abs((file_date - center).days)
    ratio = max(0.0, 1.0 - distance / half_range)
    return int(round(max_score * ratio))


def _keyword_in_text(keyword: str, text: str) -> bool:
    return _normalize(keyword) in _normalize(text)


def _equipment_context_match(equipment_name: str, text: str) -> bool:
    """Legacy score helper — prefer filename_matches_equipment for hard filters."""
    return filename_matches_equipment(text, equipment_name)


def _iter_pptx_files(root: Path):
    for path in root.rglob("*"):
        try:
            if path.is_file() and is_pptx_candidate(path):
                yield path
        except OSError as exc:
            logger.warning(
                "PPT candidate file skipped path=%s exception_type=%s",
                path,
                type(exc).__name__,
            )


def _score_file(
    file_path: Path,
    document_root: Path,
    equipment_name: str,
    keywords: list[str],
    date_from: str | None,
    date_to: str | None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    cfg = PPT_CANDIDATE_SCORE_CONFIG

    rel_folder = ""
    try:
        rel = file_path.relative_to(document_root)
        rel_folder = str(rel.parent).replace("\\", "/")
    except ValueError:
        rel_folder = ""

    filename_date, folder_date = extract_dates_from_path(str(file_path), str(document_root))
    # Prefer filename date over folder date for date score
    best_date = filename_date or folder_date

    date_score = _date_proximity_score(best_date, date_from, date_to, cfg["filename_date"])
    if date_score > 0:
        score += date_score
        if filename_date:
            reasons.append("filename_date")
        elif folder_date:
            reasons.append("folder_date")

    filename_text = file_path.stem
    folder_text = rel_folder

    for kw in keywords:
        if _keyword_in_text(kw, filename_text):
            score += cfg["filename_keyword"]
            if "filename_keyword" not in reasons:
                reasons.append("filename_keyword")
            break

    for kw in keywords:
        if folder_text and _keyword_in_text(kw, folder_text):
            score += cfg["folder_keyword"]
            if "folder_keyword" not in reasons:
                reasons.append("folder_keyword")
            break

    if _equipment_context_match(equipment_name, file_path.name):
        score += cfg["equipment_context"]
        reasons.append("equipment_context")

    return min(score, 100), reasons


def _score_modified_at(
    modified_at: datetime,
    date_from: str | None,
    date_to: str | None,
    reasons: list[str],
    current_score: int,
) -> tuple[int, list[str]]:
    """Weak auxiliary score — does not dominate total."""
    if not date_from or not date_to:
        return current_score, reasons

    cfg = PPT_CANDIDATE_SCORE_CONFIG
    mod_date = modified_at.date()
    start = parse_iso_date(date_from)
    end = parse_iso_date(date_to)
    if mod_date < start or mod_date > end:
        return current_score, reasons

    center = range_center(date_from, date_to)
    half_range = max((end - start).days, 1)
    distance = abs((mod_date - center).days)
    ratio = max(0.0, 1.0 - distance / half_range)
    mod_score = int(round(cfg["modified_at"] * ratio))
    if mod_score > 0:
        current_score = min(current_score + mod_score, 100)
        if "modified_at" not in reasons:
            reasons.append("modified_at")
    return current_score, reasons


def search_ppt_candidates(
    equipment_id: int,
    keywords: list[str],
    date_from: str | None,
    date_to: str | None,
    limit: int | None = None,
) -> PptCandidateSearchResult:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise PptCandidateSearchError("장비를 찾을 수 없습니다.")

    doc_path = Path(equipment.document_path)
    if not doc_path.exists():
        raise PptCandidateSearchError("변경내역서 경로를 찾을 수 없습니다.")
    if not doc_path.is_dir():
        raise PptCandidateSearchError("변경내역서 경로는 폴더여야 합니다.")
    if not os.access(doc_path, os.R_OK):
        raise PptCandidateSearchError("변경내역서 폴더를 읽을 수 없습니다.")

    scorable_kw = _scorable_keywords(keywords)
    max_results = limit if limit is not None else PPT_CANDIDATE_LIMIT

    logger.info(
        "PPT candidate search started equipment_id=%s keyword_count=%s has_date_range=%s",
        equipment_id,
        len(scorable_kw),
        bool(date_from and date_to),
    )

    scanned = 0
    equipment_filter_excluded = 0
    candidates: list[PptCandidateResult] = []

    for file_path in _iter_pptx_files(doc_path):
        scanned += 1
        if not is_document_for_equipment(str(file_path), equipment.name):
            equipment_filter_excluded += 1
            continue
        try:
            stat = file_path.stat()
            modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(
                microsecond=0
            )
            file_size = stat.st_size
        except OSError as exc:
            logger.warning(
                "PPT candidate file skipped path=%s exception_type=%s",
                file_path,
                type(exc).__name__,
            )
            continue

        score, reasons = _score_file(
            file_path,
            doc_path,
            equipment.name,
            scorable_kw,
            date_from,
            date_to,
        )
        score, reasons = _score_modified_at(modified_at, date_from, date_to, reasons, score)

        primary_reasons = {
            "filename_date",
            "folder_date",
            "filename_keyword",
            "folder_keyword",
        }
        if score == 0 or not any(r in reasons for r in primary_reasons):
            continue

        candidates.append(
            PptCandidateResult(
                file_path=str(file_path.resolve()),
                file_name=file_path.name,
                modified_at=modified_at.isoformat(),
                file_size=file_size,
                candidate_score=score,
                match_reasons=reasons,
            )
        )

    candidates.sort(key=lambda c: (-c.candidate_score, c.file_name.lower()))
    top = candidates[:max_results]

    logger.info(
        "PPT candidate search completed equipment_id=%s scanned_files=%s "
        "equipment_filter_excluded=%s candidate_count=%s",
        equipment_id,
        scanned,
        equipment_filter_excluded,
        len(top),
    )

    return PptCandidateSearchResult(
        equipment_id=equipment_id,
        scanned_files=scanned,
        ppt_candidates=top,
        equipment_filter_excluded=equipment_filter_excluded,
    )


def search_ppt_candidates_from_context(
    equipment_id: int,
    search_context: SearchContext,
    limit: int | None = None,
) -> PptCandidateSearchResult:
    """Reuse STEP 4 SearchContext without re-deriving keywords/dates."""
    return search_ppt_candidates(
        equipment_id=equipment_id,
        keywords=search_context.keywords,
        date_from=search_context.date_from,
        date_to=search_context.date_to,
        limit=limit,
    )


def list_scored_ppt_files_for_fallback(
    equipment_id: int,
    keywords: list[str],
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[PptCandidateResult]:
    """List ALL pptx files (no candidate gate) ordered for progressive fallback.

    Order: metadata score desc, then stable file path. This ensures documents
    that failed the metadata candidate gate (e.g. internal-keyword-only docs)
    are still reachable, and older documents are never permanently excluded.
    """
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise PptCandidateSearchError("장비를 찾을 수 없습니다.")

    doc_path = Path(equipment.document_path)
    if not doc_path.exists() or not doc_path.is_dir():
        return []
    if not os.access(doc_path, os.R_OK):
        return []

    scorable_kw = _scorable_keywords(keywords)
    results: list[PptCandidateResult] = []

    for file_path in _iter_pptx_files(doc_path):
        if not is_document_for_equipment(str(file_path), equipment.name):
            continue
        try:
            stat = file_path.stat()
            modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(
                microsecond=0
            )
            file_size = stat.st_size
        except OSError:
            continue

        score, reasons = _score_file(
            file_path, doc_path, equipment.name, scorable_kw, date_from, date_to
        )
        score, reasons = _score_modified_at(modified_at, date_from, date_to, reasons, score)

        results.append(
            PptCandidateResult(
                file_path=str(file_path.resolve()),
                file_name=file_path.name,
                modified_at=modified_at.isoformat(),
                file_size=file_size,
                candidate_score=score,
                match_reasons=reasons,
            )
        )

    results.sort(key=lambda c: (-c.candidate_score, c.file_path.lower()))
    return results
