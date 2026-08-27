"""STEP 7: Evidence Link orchestration.

Flow (reusing existing STEP 4 / STEP 6 services, no duplicate search logic):

    query -> search_trace() -> Git Candidate Top 5 + SearchContext
          -> analyze_ppt_from_context() -> Change Item Candidate Top N
          -> get_or_compute_change_link() for each (git, change_item) pair
          -> Primary Evidence Gate + Min Score filter
          -> Query Relevance Gate (core keyword / explicit path|code)
          -> sort by final_rank_score -> Evidence Link Top N

Link Strength (link_score / LINK_SCORE_CONFIG) is unchanged.
Query Relevance is computed separately and only affects Evidence ranking.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.link_score_config import (
    DIFF_EXCERPT_CONTEXT_LINES,
    TRACE_CHANGE_ITEM_LINK_LIMIT,
    TRACE_EVIDENCE_LINK_LIMIT,
    TRACE_LINK_MIN_SCORE,
)
from app.core.logging import get_logger
from app.schemas.trace import GitCandidate, QueryMatchReasonItem
from app.services.change_item_cache_service import get_change_item_by_id
from app.services.change_item_candidate_service import ChangeItemCandidate
from app.services.change_link_service import get_or_compute_change_link
from app.services.equipment_name_utils import (
    document_basename,
    is_document_for_equipment,
)
from app.services.equipment_service import get_equipment
from app.services.link_score_service import MatchReason
from app.services.ppt_analysis_service import PptAnalysisError, analyze_ppt_from_context
from app.services.query_relevance_service import (
    QueryIntent,
    QueryMatchReason,
    QueryRelevanceResult,
    evaluate_change_item_query_relevance,
    evaluate_git_query_relevance,
    evaluate_link_query_relevance,
    split_evidence_query_intent,
)
from app.services.trace_service import TraceSearchError, get_commit_change_diff, search_trace

logger = get_logger()

_DIFF_ANCHOR_TYPES = frozenset(
    {
        "same_function_exact",
        "diff_change_title",
        "diff_other_field",
        "diff_source_function",
        "csr_exact",
    }
)


class EvidenceLinkError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class EvidenceLink:
    git_candidate: GitCandidate
    change_item: ChangeItemCandidate
    link_score: int
    match_reasons: list[MatchReason] = field(default_factory=list)
    diff_excerpt: str | None = None
    query_relevance_score: int = 0
    query_relevance_level: str = "없음"
    query_match_reasons: list[QueryMatchReason] = field(default_factory=list)
    final_rank_score: int = 0


@dataclass
class EvidenceResult:
    equipment_id: int
    query: str
    query_keywords: list[str]
    weak_query_terms: list[str]
    request_functions: list[str]
    request_files: list[str]
    path_scopes: list[str]
    git_candidates: list[GitCandidate]
    change_item_candidates: list[ChangeItemCandidate]
    evidence_links: list[EvidenceLink]
    change_item_link_candidate_count: int
    fallback_documents_parsed: int
    change_item_total: int
    equipment_filter_excluded: int = 0
    query_relevance_excluded_links: int = 0
    equipment_name: str | None = None


def _extract_diff_excerpt(diff: str | None, anchor: str | None, context_lines: int) -> str | None:
    """Match line +/- N lines only — not a full diff parser (STEP 7 section 17)."""
    if not diff or not anchor:
        return None
    lines = diff.splitlines()
    for idx, line in enumerate(lines):
        if anchor in line:
            start = max(0, idx - context_lines)
            end = min(len(lines), idx + context_lines + 1)
            return "\n".join(lines[start:end])
    return None


def _build_diff_excerpt(
    git_candidate: GitCandidate, reasons: list[MatchReason]
) -> str | None:
    anchor = next(
        (r.git_value for r in reasons if r.type in _DIFF_ANCHOR_TYPES and r.git_value),
        None,
    )
    if not anchor:
        return None
    diff = get_commit_change_diff(git_candidate.commit_id, git_candidate.file_path)
    return _extract_diff_excerpt(diff, anchor, DIFF_EXCERPT_CONTEXT_LINES)


def _to_query_match_items(reasons: list[QueryMatchReason]) -> list[QueryMatchReasonItem]:
    return [
        QueryMatchReasonItem(
            keyword=r.keyword,
            field=r.field,
            value=r.value,
            score=r.score,
            strength=r.strength,
        )
        for r in reasons
    ]


def _enrich_git_candidate(
    git: GitCandidate,
    intent: QueryIntent,
    *,
    request_file_path: str | None,
    selected_code: str | None,
) -> GitCandidate:
    rel = evaluate_git_query_relevance(
        git,
        intent,
        request_file_path=request_file_path,
        selected_code=selected_code,
    )
    return git.model_copy(
        update={
            "query_match_reasons": _to_query_match_items(rel.match_reasons),
            "query_relevance_score": rel.score,
            "query_relevance_level": rel.level,
        }
    )


def _attach_change_item_relevance(
    item: ChangeItemCandidate,
    rel: QueryRelevanceResult,
) -> ChangeItemCandidate:
    item.query_match_reasons = list(rel.match_reasons)
    item.query_relevance_score = rel.score
    item.query_relevance_level = rel.level
    return item


def build_evidence(
    equipment_id: int,
    query: str,
    file_path: str | None = None,
    selected_code: str | None = None,
) -> EvidenceResult:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise EvidenceLinkError("장비를 찾을 수 없습니다.")

    intent = split_evidence_query_intent(query, file_path, selected_code)

    try:
        trace_result = search_trace(
            equipment_id=equipment_id,
            query=query,
            file_path=file_path,
            selected_code=selected_code,
        )
    except TraceSearchError as exc:
        raise EvidenceLinkError(exc.message) from exc

    git_candidates = [
        _enrich_git_candidate(
            g,
            intent,
            request_file_path=file_path,
            selected_code=selected_code,
        )
        for g in trace_result.git_candidates
    ]

    try:
        analysis = analyze_ppt_from_context(equipment_id, trace_result.search_context)
    except PptAnalysisError as exc:
        raise EvidenceLinkError(exc.message) from exc

    # Evidence API: Change Item Candidate 반환 직전 장비 필터 재적용.
    excluded_docs: set[str] = set()
    filtered_change_items: list[ChangeItemCandidate] = []
    for item in analysis.change_item_candidates:
        path = (item.file_path or item.file_name or "").strip()
        item_eid = getattr(item, "equipment_id", None)
        if item_eid is not None and int(item_eid) != int(equipment_id):
            name = document_basename(path) or (item.file_name or "")
            if name:
                excluded_docs.add(name)
            continue
        if is_document_for_equipment(path, equipment.name):
            filtered_change_items.append(item)
        else:
            name = document_basename(path) or (item.file_name or "")
            if name:
                excluded_docs.add(name)

    change_item_candidates = filtered_change_items[:TRACE_CHANGE_ITEM_LINK_LIMIT]
    for item in change_item_candidates:
        if getattr(item, "equipment_id", None) is None:
            item.equipment_id = equipment_id
        rel = evaluate_change_item_query_relevance(
            item,
            intent,
            request_file_path=file_path,
            selected_code=selected_code,
        )
        _attach_change_item_relevance(item, rel)

    scored_pairs: list[
        tuple[int, GitCandidate, ChangeItemCandidate, object, QueryRelevanceResult]
    ] = []
    query_relevance_excluded = 0

    for git_rank, git_candidate in enumerate(git_candidates):
        for item_candidate in change_item_candidates:
            if not is_document_for_equipment(
                item_candidate.file_path or item_candidate.file_name,
                equipment.name,
            ):
                continue
            row = get_change_item_by_id(item_candidate.change_item_cache_id)
            if row is None:
                continue
            if row.equipment_id is not None and int(row.equipment_id) != int(equipment_id):
                name = document_basename(row.file_path) or (row.file_name or "")
                if name:
                    excluded_docs.add(name)
                continue
            if not is_document_for_equipment(
                row.file_path or row.file_name, equipment.name
            ):
                name = document_basename(row.file_path) or (row.file_name or "")
                if name:
                    excluded_docs.add(name)
                continue
            result = get_or_compute_change_link(git_candidate, row)
            if not result.passes_gate or result.score < TRACE_LINK_MIN_SCORE:
                continue

            link_rel = evaluate_link_query_relevance(
                git_candidate,
                item_candidate,
                intent,
                request_file_path=file_path,
                selected_code=selected_code,
            )
            if not link_rel.passes_gate:
                query_relevance_excluded += 1
                continue

            scored_pairs.append(
                (git_rank, git_candidate, item_candidate, result, link_rel)
            )

    scored_pairs.sort(
        key=lambda pair: (
            -(pair[4].score + pair[3].score),  # final_rank_score
            -pair[4].score,  # query relevance
            -pair[3].score,  # link strength
            pair[0],
            -pair[2].candidate_score,
            pair[1].commit_id,
            pair[2].change_item_cache_id,
        )
    )
    top_pairs = scored_pairs[:TRACE_EVIDENCE_LINK_LIMIT]

    evidence_links = [
        EvidenceLink(
            git_candidate=git_candidate,
            change_item=item_candidate,
            link_score=result.score,
            match_reasons=result.match_reasons,
            diff_excerpt=_build_diff_excerpt(git_candidate, result.match_reasons),
            query_relevance_score=link_rel.score,
            query_relevance_level=link_rel.level,
            query_match_reasons=link_rel.match_reasons,
            final_rank_score=link_rel.score + result.score,
        )
        for _rank, git_candidate, item_candidate, result, link_rel in top_pairs
    ]

    equipment_filter_excluded = analysis.equipment_filter_excluded + len(excluded_docs)

    logger.info(
        "Evidence link built equipment_id=%s git_candidates=%s change_items=%s links=%s "
        "equipment_filter_excluded=%s query_relevance_excluded=%s core_keywords=%s",
        equipment_id,
        len(git_candidates),
        len(change_item_candidates),
        len(evidence_links),
        equipment_filter_excluded,
        query_relevance_excluded,
        [*intent.request_functions, *intent.request_files, *intent.query_keywords],
    )

    return EvidenceResult(
        equipment_id=equipment_id,
        query=query,
        query_keywords=list(intent.query_keywords),
        weak_query_terms=list(intent.weak_query_terms),
        request_functions=list(intent.request_functions),
        request_files=list(intent.request_files),
        path_scopes=list(intent.path_scopes),
        git_candidates=git_candidates,
        change_item_candidates=change_item_candidates,
        evidence_links=evidence_links,
        change_item_link_candidate_count=len(change_item_candidates),
        fallback_documents_parsed=analysis.fallback_documents_parsed,
        change_item_total=analysis.change_item_total,
        equipment_filter_excluded=equipment_filter_excluded,
        query_relevance_excluded_links=query_relevance_excluded,
        equipment_name=equipment.name,
    )
