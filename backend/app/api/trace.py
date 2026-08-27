from fastapi import APIRouter, HTTPException

from app.schemas.trace import (
    ChangeItemCandidateItem,
    EvidenceDebugInfo,
    EvidenceLinkItem,
    EvidenceRequest,
    EvidenceResponse,
    MatchReasonItem,
    PptAnalysisRequest,
    PptAnalysisResponse,
    PptCandidateItem,
    PptCandidateRequest,
    PptCandidateResponse,
    ProcessedDocumentItem,
    QueryMatchReasonItem,
    SlideCandidateItem,
    SourceFunctionItem,
    TraceSearchRequest,
    TraceSearchResponse,
)
from app.services.change_item_candidate_service import ChangeItemCandidate
from app.services.evidence_service import EvidenceLink, EvidenceLinkError, build_evidence
from app.services.link_score_service import MatchReason
from app.services.ppt_analysis_service import PptAnalysisError, analyze_ppt
from app.services.ppt_candidate_service import PptCandidateSearchError, search_ppt_candidates
from app.services.query_relevance_service import QueryMatchReason
from app.services.trace_service import TraceSearchError, search_trace

router = APIRouter(prefix="/api/trace", tags=["trace"])


def _map_query_match_reason(reason: QueryMatchReason | QueryMatchReasonItem) -> QueryMatchReasonItem:
    if isinstance(reason, QueryMatchReasonItem):
        return reason
    return QueryMatchReasonItem(
        keyword=reason.keyword,
        field=reason.field,
        value=reason.value,
        score=reason.score,
        strength=reason.strength,
    )


def _map_change_item_candidate(c: ChangeItemCandidate) -> ChangeItemCandidateItem:
    return ChangeItemCandidateItem(
        change_item_cache_id=c.change_item_cache_id,
        document_cache_id=c.document_cache_id,
        slide_no=c.slide_no,
        file_path=c.file_path,
        file_name=c.file_name,
        item_no=c.item_no,
        change_title=c.change_title,
        csr_no=c.csr_no,
        business_background=c.business_background,
        current_status=c.current_status,
        as_is=c.as_is,
        to_be=c.to_be,
        source_functions=[
            SourceFunctionItem(
                file_path=sf.get("file_path"),
                functions=sf.get("functions") or [],
                raw_text=sf.get("raw_text") or "",
            )
            for sf in c.source_functions
        ],
        test_cases=c.test_cases,
        applicable_scopes=c.applicable_scopes,
        matched_keywords=c.matched_keywords,
        candidate_score=c.candidate_score,
        from_cache_search=c.from_cache_search,
        from_fallback=c.from_fallback,
        query_match_reasons=[
            _map_query_match_reason(r) for r in (c.query_match_reasons or [])
        ],
        query_relevance_score=getattr(c, "query_relevance_score", 0) or 0,
        query_relevance_level=getattr(c, "query_relevance_level", None) or "없음",
    )


def _map_match_reason(reason: MatchReason) -> MatchReasonItem:
    return MatchReasonItem(
        type=reason.type,
        score=reason.score,
        git_value=reason.git_value,
        change_item_value=reason.change_item_value,
        distance_days=reason.distance_days,
        match_level=reason.match_level,
    )


def _map_evidence_link(link: EvidenceLink) -> EvidenceLinkItem:
    return EvidenceLinkItem(
        git_commit_id=link.git_candidate.commit_id,
        git_repository_id=link.git_candidate.repository_id,
        git_commit_hash=link.git_candidate.commit_hash,
        git_file_path=link.git_candidate.file_path,
        change_item_cache_id=link.change_item.change_item_cache_id,
        document_cache_id=link.change_item.document_cache_id,
        link_score=link.link_score,
        match_reasons=[_map_match_reason(r) for r in link.match_reasons],
        diff_excerpt=link.diff_excerpt,
        query_relevance_score=link.query_relevance_score,
        query_relevance_level=link.query_relevance_level,
        query_match_reasons=[_map_query_match_reason(r) for r in link.query_match_reasons],
        final_rank_score=link.final_rank_score,
    )


@router.post("/search", response_model=TraceSearchResponse)
def trace_search(request: TraceSearchRequest) -> TraceSearchResponse:
    try:
        return search_trace(
            equipment_id=request.equipment_id,
            query=request.query.strip(),
            file_path=request.file_path.strip() if request.file_path else None,
            selected_code=request.selected_code,
        )
    except TraceSearchError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.post("/ppt-candidates", response_model=PptCandidateResponse)
def ppt_candidates(request: PptCandidateRequest) -> PptCandidateResponse:
    try:
        result = search_ppt_candidates(
            equipment_id=request.equipment_id,
            keywords=request.keywords,
            date_from=request.date_from,
            date_to=request.date_to,
        )
    except PptCandidateSearchError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return PptCandidateResponse(
        equipment_id=result.equipment_id,
        scanned_files=result.scanned_files,
        ppt_candidates=[
            PptCandidateItem(
                file_path=c.file_path,
                file_name=c.file_name,
                modified_at=c.modified_at,
                file_size=c.file_size,
                candidate_score=c.candidate_score,
                match_reasons=c.match_reasons,
            )
            for c in result.ppt_candidates
        ],
    )


@router.post("/ppt-analysis", response_model=PptAnalysisResponse)
def ppt_analysis(request: PptAnalysisRequest) -> PptAnalysisResponse:
    try:
        result = analyze_ppt(
            equipment_id=request.equipment_id,
            keywords=request.keywords,
            date_from=request.date_from,
            date_to=request.date_to,
        )
    except PptAnalysisError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return PptAnalysisResponse(
        equipment_id=result.equipment_id,
        ppt_candidate_count=result.ppt_candidate_count,
        processed_documents=result.processed_documents,
        cache_hits=result.cache_hits,
        cache_misses=result.cache_misses,
        parse_failures=result.parse_failures,
        documents=[
            ProcessedDocumentItem(
                document_cache_id=d.document_cache_id,
                file_path=d.file_path,
                file_name=d.file_name,
                slide_count=d.slide_count,
                cache_hit=d.cache_hit,
            )
            for d in result.documents
        ],
        slide_candidates=[
            SlideCandidateItem(
                document_cache_id=s.document_cache_id,
                slide_cache_id=s.slide_cache_id,
                file_path=s.file_path,
                file_name=s.file_name,
                slide_number=s.slide_number,
                title=s.title,
                content=s.content,
                matched_keywords=s.matched_keywords,
                candidate_score=s.candidate_score,
                from_cache_search=s.from_cache_search,
            )
            for s in result.slide_candidates
        ],
        change_item_candidates=[
            ChangeItemCandidateItem(
                change_item_cache_id=c.change_item_cache_id,
                document_cache_id=c.document_cache_id,
                slide_no=c.slide_no,
                file_path=c.file_path,
                file_name=c.file_name,
                item_no=c.item_no,
                change_title=c.change_title,
                csr_no=c.csr_no,
                business_background=c.business_background,
                current_status=c.current_status,
                as_is=c.as_is,
                to_be=c.to_be,
                source_functions=[
                    SourceFunctionItem(
                        file_path=sf.get("file_path"),
                        functions=sf.get("functions") or [],
                        raw_text=sf.get("raw_text") or "",
                    )
                    for sf in c.source_functions
                ],
                test_cases=c.test_cases,
                applicable_scopes=c.applicable_scopes,
                matched_keywords=c.matched_keywords,
                candidate_score=c.candidate_score,
                from_cache_search=c.from_cache_search,
                from_fallback=c.from_fallback,
            )
            for c in result.change_item_candidates
        ],
        fallback_documents_parsed=result.fallback_documents_parsed,
        change_item_total=result.change_item_total,
        equipment_filter_excluded=result.equipment_filter_excluded,
    )


@router.post("/evidence", response_model=EvidenceResponse)
def trace_evidence(request: EvidenceRequest) -> EvidenceResponse:
    try:
        result = build_evidence(
            equipment_id=request.equipment_id,
            query=request.query.strip(),
            file_path=request.file_path.strip() if request.file_path else None,
            selected_code=request.selected_code,
        )
    except EvidenceLinkError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return EvidenceResponse(
        equipment_id=result.equipment_id,
        query=result.query,
        query_keywords=result.query_keywords,
        weak_query_terms=result.weak_query_terms,
        request_functions=result.request_functions,
        request_files=result.request_files,
        path_scopes=result.path_scopes,
        git_candidates=result.git_candidates,
        change_item_candidates=[
            _map_change_item_candidate(c) for c in result.change_item_candidates
        ],
        evidence_links=[_map_evidence_link(link) for link in result.evidence_links],
        debug=EvidenceDebugInfo(
            change_item_link_candidate_count=result.change_item_link_candidate_count,
            fallback_documents_parsed=result.fallback_documents_parsed,
            change_item_total=result.change_item_total,
            equipment_filter_excluded=result.equipment_filter_excluded,
            equipment_filter_reason="filename equipment mismatch",
            query_relevance_excluded_links=result.query_relevance_excluded_links,
            query_keywords=result.query_keywords,
            weak_query_terms=result.weak_query_terms,
            request_functions=result.request_functions,
            request_files=result.request_files,
            path_scopes=result.path_scopes,
        ),
    )
