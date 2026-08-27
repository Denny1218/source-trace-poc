"""Slide candidate search from cached PPT slides (STEP 6, no Git-PPT link score)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.core.ppt_parse_config import SLIDE_CANDIDATE_LIMIT, SLIDE_CANDIDATE_SCORE_CONFIG
from app.services.ppt_cache_service import CachedDocument, SlideCacheRow
from app.services.ppt_candidate_service import _scorable_keywords

logger = get_logger()


@dataclass
class SlideCandidate:
    document_cache_id: int
    slide_cache_id: int
    file_path: str
    file_name: str
    slide_number: int
    title: str | None
    content: str | None
    matched_keywords: list[str]
    candidate_score: int
    from_cache_search: bool = False


def _normalize(text: str) -> str:
    return text.lower()


def _keyword_in_text(keyword: str, text: str) -> bool:
    if not text:
        return False
    return _normalize(keyword) in _normalize(text)


def _score_slide(
    slide: SlideCacheRow,
    file_name: str,
    keywords: list[str],
) -> tuple[int, list[str]]:
    cfg = SLIDE_CANDIDATE_SCORE_CONFIG
    matched: list[str] = []
    score = 0

    title_hit = any(
        slide.title and _keyword_in_text(kw, slide.title) for kw in keywords
    )
    if title_hit:
        score += cfg["title_keyword"]
        for kw in keywords:
            if slide.title and _keyword_in_text(kw, slide.title) and kw not in matched:
                matched.append(kw)

    content_hit = any(_keyword_in_text(kw, slide.content) for kw in keywords)
    if content_hit:
        score += cfg["content_keyword"]
        for kw in keywords:
            if _keyword_in_text(kw, slide.content) and kw not in matched:
                matched.append(kw)

    filename_hit = any(_keyword_in_text(kw, file_name) for kw in keywords)
    if filename_hit:
        score += cfg["filename_keyword"]
        for kw in keywords:
            if _keyword_in_text(kw, file_name) and kw not in matched:
                matched.append(kw)

    return score, matched


def search_slide_candidates(
    documents: list[CachedDocument],
    keywords: list[str],
    limit: int | None = None,
) -> list[SlideCandidate]:
    scorable = _scorable_keywords(keywords)
    max_results = limit if limit is not None else SLIDE_CANDIDATE_LIMIT
    results: list[SlideCandidate] = []

    for cached in documents:
        doc = cached.document
        for slide in cached.slides:
            score, matched = _score_slide(slide, doc.file_name, scorable)
            if score == 0:
                continue
            results.append(
                SlideCandidate(
                    document_cache_id=doc.id,
                    slide_cache_id=slide.id,
                    file_path=doc.file_path,
                    file_name=doc.file_name,
                    slide_number=slide.slide_number,
                    title=slide.title,
                    content=slide.content,
                    matched_keywords=matched,
                    candidate_score=score,
                    from_cache_search=False,
                )
            )

    results.sort(
        key=lambda c: (-c.candidate_score, c.file_name.lower(), c.slide_number)
    )
    top = results[:max_results]

    logger.info("Slide candidate search completed slide_candidate_count=%s", len(top))
    return top


def search_slide_candidates_from_cache(
    equipment_id: int,
    keywords: list[str],
    limit: int | None = None,
) -> list[SlideCandidate]:
    """Search all cached slides for equipment (independent of STEP 5 file candidate funnel)."""
    from app.services.ppt_cache_service import list_cached_slides_for_equipment

    scorable = _scorable_keywords(keywords)
    if not scorable:
        return []

    max_results = limit if limit is not None else SLIDE_CANDIDATE_LIMIT
    results: list[SlideCandidate] = []

    for row in list_cached_slides_for_equipment(equipment_id):
        score, matched = _score_slide(row.slide, row.file_name, scorable)
        if score == 0:
            continue
        results.append(
            SlideCandidate(
                document_cache_id=row.slide.document_cache_id,
                slide_cache_id=row.slide.id,
                file_path=row.file_path,
                file_name=row.file_name,
                slide_number=row.slide.slide_number,
                title=row.slide.title,
                content=row.slide.content,
                matched_keywords=matched,
                candidate_score=score,
                from_cache_search=True,
            )
        )

    results.sort(
        key=lambda c: (-c.candidate_score, c.file_name.lower(), c.slide_number)
    )
    top = results[:max_results]
    logger.info(
        "Slide cache keyword search equipment_id=%s slide_candidate_count=%s",
        equipment_id,
        len(top),
    )
    return top


def merge_slide_candidates(
    primary: list[SlideCandidate],
    secondary: list[SlideCandidate],
    limit: int | None = None,
) -> list[SlideCandidate]:
    """Merge by slide_cache_id; primary (funnel) wins on duplicate."""
    max_results = limit if limit is not None else SLIDE_CANDIDATE_LIMIT
    merged: dict[int, SlideCandidate] = {}
    for candidate in primary:
        merged[candidate.slide_cache_id] = candidate
    for candidate in secondary:
        merged.setdefault(candidate.slide_cache_id, candidate)
    results = list(merged.values())
    results.sort(
        key=lambda c: (-c.candidate_score, c.file_name.lower(), c.slide_number)
    )
    return results[:max_results]
