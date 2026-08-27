"""On-demand PPT analysis orchestration (STEP 5 + STEP 6)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.core.ppt_fallback_config import (
    PPT_FALLBACK_BATCH_SIZE,
    PPT_FALLBACK_MAX_DOCUMENTS,
    PPT_FALLBACK_RESULT_LIMIT,
)
from app.core.ppt_parse_config import PPT_PARSE_LIMIT
from app.schemas.trace import SearchContext
from app.services.change_item_cache_service import (
    ensure_change_items_for_document,
    list_change_items_for_document,
    list_change_items_for_equipment,
    parse_and_store_change_items,
)
from app.services.change_item_candidate_service import (
    ChangeItemCandidate,
    merge_change_item_candidates,
    search_change_item_candidates,
)
from app.services.equipment_name_utils import (
    document_basename,
    is_document_for_equipment,
)
from app.services.equipment_service import get_equipment
from app.services.ppt_cache_service import (
    CachedDocument,
    get_or_parse_document,
    list_document_cache_by_equipment,
)
from app.services.ppt_candidate_service import (
    PptCandidateResult,
    PptCandidateSearchError,
    list_scored_ppt_files_for_fallback,
    search_ppt_candidates,
    search_ppt_candidates_from_context,
)
from app.services.slide_candidate_service import (
    SlideCandidate,
    merge_slide_candidates,
    search_slide_candidates,
    search_slide_candidates_from_cache,
)

logger = get_logger()


class PptAnalysisError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class ProcessedDocumentInfo:
    document_cache_id: int
    file_path: str
    file_name: str
    slide_count: int
    cache_hit: bool


@dataclass
class PptAnalysisResult:
    equipment_id: int
    ppt_candidate_count: int
    processed_documents: int
    cache_hits: int
    cache_misses: int
    parse_failures: int
    documents: list[ProcessedDocumentInfo]
    slide_candidates: list[SlideCandidate]
    change_item_candidates: list[ChangeItemCandidate] = field(default_factory=list)
    fallback_documents_parsed: int = 0
    change_item_total: int = 0
    equipment_filter_excluded: int = 0


def process_ppt_candidates(
    equipment_id: int,
    candidates: list[PptCandidateResult],
    keywords: list[str],
    *,
    parse_limit: int | None = None,
    parse_fn=None,
) -> tuple[list[CachedDocument], int, int, int, list[ProcessedDocumentInfo]]:
    """Parse or load cache for top candidates. Returns docs, hits, misses, failures, info."""
    limit = parse_limit if parse_limit is not None else PPT_PARSE_LIMIT
    sorted_candidates = sorted(
        candidates, key=lambda c: (-c.candidate_score, c.file_name.lower())
    )
    to_process = sorted_candidates[:limit]

    logger.info(
        "PPT parse requested equipment_id=%s candidate_count=%s parse_limit=%s",
        equipment_id,
        len(candidates),
        limit,
    )

    documents: list[CachedDocument] = []
    cache_hits = 0
    cache_misses = 0
    parse_failures = 0
    info_list: list[ProcessedDocumentInfo] = []

    kwargs = {}
    if parse_fn is not None:
        kwargs["parse_fn"] = parse_fn

    for candidate in to_process:
        cached, hit, failed = get_or_parse_document(
            equipment_id, candidate.file_path, **kwargs
        )
        if cached is None:
            parse_failures += 1
            continue

        if failed:
            parse_failures += 1

        if hit:
            cache_hits += 1
        else:
            cache_misses += 1

        documents.append(cached)
        info_list.append(
            ProcessedDocumentInfo(
                document_cache_id=cached.document.id,
                file_path=cached.document.file_path,
                file_name=cached.document.file_name,
                slide_count=cached.document.slide_count,
                cache_hit=hit,
            )
        )

    return documents, cache_hits, cache_misses, parse_failures, info_list


def analyze_ppt_from_context(
    equipment_id: int,
    search_context: SearchContext,
    *,
    parse_limit: int | None = None,
    parse_fn=None,
) -> PptAnalysisResult:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise PptAnalysisError("장비를 찾을 수 없습니다.")

    try:
        candidate_result = search_ppt_candidates_from_context(equipment_id, search_context)
    except PptCandidateSearchError as exc:
        raise PptAnalysisError(exc.message) from exc

    return _analyze_from_candidates(
        equipment_id,
        candidate_result.ppt_candidates,
        search_context.keywords,
        parse_limit=parse_limit,
        parse_fn=parse_fn,
        date_from=search_context.date_from,
        date_to=search_context.date_to,
        equipment_name=equipment.name,
        equipment_filter_excluded=candidate_result.equipment_filter_excluded,
    )


def analyze_ppt(
    equipment_id: int,
    keywords: list[str],
    date_from: str | None,
    date_to: str | None,
    *,
    parse_limit: int | None = None,
    parse_fn=None,
) -> PptAnalysisResult:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise PptAnalysisError("장비를 찾을 수 없습니다.")

    try:
        candidate_result = search_ppt_candidates(
            equipment_id=equipment_id,
            keywords=keywords,
            date_from=date_from,
            date_to=date_to,
        )
    except PptCandidateSearchError as exc:
        raise PptAnalysisError(exc.message) from exc

    return _analyze_from_candidates(
        equipment_id,
        candidate_result.ppt_candidates,
        keywords,
        parse_limit=parse_limit,
        parse_fn=parse_fn,
        date_from=date_from,
        date_to=date_to,
        equipment_name=equipment.name,
        equipment_filter_excluded=candidate_result.equipment_filter_excluded,
    )


def _ensure_change_items_for_processed(
    documents: list[CachedDocument],
) -> None:
    """Generate/refresh change items for funnel-parsed documents.

    Documents whose cache was (re)built this run (cache_hit is False) are force
    re-parsed so change items stay in sync with a changed document hash. Cache
    hits use the lazy path (parser_version gate)."""
    for cached in documents:
        doc = cached.document
        if not cached.cache_hit:
            parse_and_store_change_items(doc, file_path=doc.file_path)
        else:
            ensure_change_items_for_document(doc.id, file_path=doc.file_path)


def _path_for_equipment_filter(file_path: str | None, file_name: str | None) -> str:
    """Prefer full path (basename extracted later); fall back to file_name."""
    if file_path and str(file_path).strip():
        return str(file_path).strip()
    return (file_name or "").strip()


def _filter_change_items_for_equipment(
    candidates: list[ChangeItemCandidate],
    equipment_name: str,
    excluded_docs: set[str],
) -> list[ChangeItemCandidate]:
    kept: list[ChangeItemCandidate] = []
    for item in candidates:
        path = _path_for_equipment_filter(item.file_path, item.file_name)
        if is_document_for_equipment(path, equipment_name):
            kept.append(item)
        else:
            name = document_basename(path) or (item.file_name or "")
            if name:
                excluded_docs.add(name)
    return kept


def _filter_slides_for_equipment(
    candidates: list[SlideCandidate],
    equipment_name: str,
    excluded_docs: set[str],
) -> list[SlideCandidate]:
    kept: list[SlideCandidate] = []
    for item in candidates:
        path = _path_for_equipment_filter(item.file_path, item.file_name)
        if is_document_for_equipment(path, equipment_name):
            kept.append(item)
        else:
            name = document_basename(path) or (item.file_name or "")
            if name:
                excluded_docs.add(name)
    return kept


def _run_progressive_fallback(
    equipment_id: int,
    keywords: list[str],
    date_from: str | None,
    date_to: str | None,
    processed_paths: set[str],
    found: int,
    *,
    equipment_name: str = "",
) -> tuple[list[ChangeItemCandidate], int]:
    """Parse not-yet-analyzed PPTX in metadata-ranked batches until enough hits.

    Bounded by PPT_FALLBACK_MAX_DOCUMENTS. Returns (candidates, docs_parsed).
    Equipment filename filter is applied before returning hits.
    """
    if found >= PPT_FALLBACK_RESULT_LIMIT:
        return [], 0

    try:
        scored = list_scored_ppt_files_for_fallback(
            equipment_id, keywords, date_from, date_to
        )
    except PptCandidateSearchError:
        return [], 0

    # Defense in depth: list_scored already filters; re-check basename here.
    pending = [
        c
        for c in scored
        if c.file_path not in processed_paths
        and (
            not equipment_name
            or is_document_for_equipment(c.file_path, equipment_name)
        )
    ]
    if not pending:
        return [], 0

    logger.info(
        "PPT fallback started equipment_id=%s pending=%s found=%s",
        equipment_id,
        len(pending),
        found,
    )

    fallback_candidates: list[ChangeItemCandidate] = []
    docs_parsed = 0

    for start in range(0, len(pending), PPT_FALLBACK_BATCH_SIZE):
        if docs_parsed >= PPT_FALLBACK_MAX_DOCUMENTS:
            break
        batch = pending[start : start + PPT_FALLBACK_BATCH_SIZE]
        for candidate in batch:
            if docs_parsed >= PPT_FALLBACK_MAX_DOCUMENTS:
                break
            if equipment_name and not is_document_for_equipment(
                candidate.file_path, equipment_name
            ):
                continue
            cached, _hit, failed = get_or_parse_document(
                equipment_id, candidate.file_path
            )
            docs_parsed += 1
            if cached is None or failed:
                continue
            if equipment_name and not is_document_for_equipment(
                cached.document.file_path or cached.document.file_name,
                equipment_name,
            ):
                continue
            parse_and_store_change_items(cached.document, file_path=cached.document.file_path)
            rows = list_change_items_for_document(cached.document.id)
            hits = search_change_item_candidates(rows, keywords, from_fallback=True)
            if equipment_name:
                hits = [
                    h
                    for h in hits
                    if is_document_for_equipment(
                        _path_for_equipment_filter(h.file_path, h.file_name),
                        equipment_name,
                    )
                ]
            fallback_candidates.extend(hits)

        current = found + len({c.change_item_cache_id for c in fallback_candidates})
        if current >= PPT_FALLBACK_RESULT_LIMIT:
            break

    logger.info(
        "PPT fallback completed equipment_id=%s docs_parsed=%s new_hits=%s",
        equipment_id,
        docs_parsed,
        len(fallback_candidates),
    )
    return fallback_candidates, docs_parsed


def _analyze_from_candidates(
    equipment_id: int,
    candidates: list[PptCandidateResult],
    keywords: list[str],
    *,
    parse_limit: int | None = None,
    parse_fn=None,
    date_from: str | None = None,
    date_to: str | None = None,
    equipment_name: str = "",
    equipment_filter_excluded: int = 0,
) -> PptAnalysisResult:
    excluded_docs: set[str] = set()

    # 1차: PPT Candidate — re-apply basename filter (defense in depth).
    if equipment_name:
        kept_candidates: list[PptCandidateResult] = []
        for c in candidates:
            if is_document_for_equipment(c.file_path or c.file_name, equipment_name):
                kept_candidates.append(c)
            else:
                name = document_basename(c.file_path) or c.file_name
                if name:
                    excluded_docs.add(name)
        candidates = kept_candidates

    documents, cache_hits, cache_misses, parse_failures, info_list = process_ppt_candidates(
        equipment_id,
        candidates,
        keywords,
        parse_limit=parse_limit,
        parse_fn=parse_fn,
    )

    # Drop funnel docs that somehow bypassed candidate filtering.
    if equipment_name:
        kept_documents: list[CachedDocument] = []
        kept_info: list[ProcessedDocumentInfo] = []
        for cached, info in zip(documents, info_list):
            path = cached.document.file_path or cached.document.file_name
            if is_document_for_equipment(path, equipment_name):
                kept_documents.append(cached)
                kept_info.append(info)
            else:
                name = document_basename(path) or cached.document.file_name
                if name:
                    excluded_docs.add(name)
        documents = kept_documents
        info_list = kept_info

    funnel_slides = search_slide_candidates(documents, keywords)
    cache_slides = search_slide_candidates_from_cache(equipment_id, keywords)
    if equipment_name:
        cache_slides = _filter_slides_for_equipment(
            cache_slides, equipment_name, excluded_docs
        )
        funnel_slides = _filter_slides_for_equipment(
            funnel_slides, equipment_name, excluded_docs
        )
    slide_candidates = merge_slide_candidates(funnel_slides, cache_slides)

    logger.info(
        "PPT analysis slide merge equipment_id=%s funnel=%s cache=%s merged=%s",
        equipment_id,
        len(funnel_slides),
        len(cache_slides),
        len(slide_candidates),
    )

    # --- Change item structure: funnel docs + full equipment cache search ---
    _ensure_change_items_for_processed(documents)

    funnel_rows = [
        row
        for cached in documents
        for row in list_change_items_for_document(cached.document.id)
    ]
    if equipment_name:
        funnel_rows = [
            r
            for r in funnel_rows
            if is_document_for_equipment(
                _path_for_equipment_filter(r.file_path, r.file_name),
                equipment_name,
            )
        ]
    funnel_ci = search_change_item_candidates(funnel_rows, keywords)

    cache_rows = list_change_items_for_equipment(equipment_id)
    if equipment_name:
        kept_rows = []
        for r in cache_rows:
            path = _path_for_equipment_filter(r.file_path, r.file_name)
            if is_document_for_equipment(path, equipment_name):
                kept_rows.append(r)
            else:
                name = document_basename(path) or (r.file_name or "")
                if name:
                    excluded_docs.add(name)
        cache_rows = kept_rows
    cache_ci = search_change_item_candidates(cache_rows, keywords, from_cache_search=True)
    change_item_candidates = merge_change_item_candidates(funnel_ci, cache_ci)

    # --- Progressive fallback: only when initial hits are insufficient ---
    processed_paths = {
        row.file_path for row in list_document_cache_by_equipment(equipment_id)
    }
    fallback_ci, fallback_parsed = _run_progressive_fallback(
        equipment_id,
        keywords,
        date_from,
        date_to,
        processed_paths,
        len(change_item_candidates),
        equipment_name=equipment_name,
    )
    if fallback_ci:
        if equipment_name:
            fallback_ci = _filter_change_items_for_equipment(
                fallback_ci, equipment_name, excluded_docs
            )
        change_item_candidates = merge_change_item_candidates(
            change_item_candidates, fallback_ci
        )

    # 2차: Change Item Candidate 반환 직전 최종 hard filter (cache 여부 무관).
    if equipment_name:
        change_item_candidates = _filter_change_items_for_equipment(
            change_item_candidates, equipment_name, excluded_docs
        )
        slide_candidates = _filter_slides_for_equipment(
            slide_candidates, equipment_name, excluded_docs
        )

    equipment_filter_excluded = equipment_filter_excluded + len(excluded_docs)

    logger.info(
        "PPT analysis change item merge equipment_id=%s funnel=%s cache=%s fallback=%s "
        "merged=%s equipment_filter_excluded=%s",
        equipment_id,
        len(funnel_ci),
        len(cache_ci),
        len(fallback_ci) if fallback_ci else 0,
        len(change_item_candidates),
        equipment_filter_excluded,
    )

    return PptAnalysisResult(
        equipment_id=equipment_id,
        ppt_candidate_count=len(candidates),
        processed_documents=len(info_list),
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        parse_failures=parse_failures,
        documents=info_list,
        slide_candidates=slide_candidates,
        change_item_candidates=change_item_candidates,
        fallback_documents_parsed=fallback_parsed,
        change_item_total=len(change_item_candidates),
        equipment_filter_excluded=equipment_filter_excluded,
    )
