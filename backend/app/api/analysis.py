"""STEP 8: POST /api/trace/analyze — Ollama Evidence Grounded Answer.

Reuses STEP 7 ``build_evidence`` untouched (no re-scoring, no Gate/weight
changes) and only adds an AI summary layer on top via ``ollama_service``.

Also exposes GET /api/trace/ollama-test for Ollama-only latency diagnosis
(no Git/PPT/Evidence).
"""

from fastapi import APIRouter, HTTPException

from app.api.trace import _map_change_item_candidate, _map_evidence_link
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    EvidenceRefItem,
    OllamaTinyTestResponse,
)
from app.schemas.trace import EvidenceDebugInfo
from app.services.evidence_service import EvidenceLinkError, build_evidence
from app.services.ollama_service import analyze_evidence, run_ollama_tiny_test

router = APIRouter(prefix="/api/trace", tags=["analysis"])


@router.get("/ollama-test", response_model=OllamaTinyTestResponse)
def ollama_tiny_test() -> OllamaTinyTestResponse:
    """Ollama-only smoke test — independent of Evidence / Git / PPT."""
    result = run_ollama_tiny_test()
    return OllamaTinyTestResponse(
        ok=result.ok,
        model=result.model,
        elapsed_ms=result.elapsed_ms,
        response_preview=result.response_preview,
        error_type=result.error_type,
        base_url=result.base_url,
        timeout_seconds=result.timeout_seconds,
    )


@router.post("/analyze", response_model=AnalysisResponse)
def trace_analyze(request: AnalysisRequest) -> AnalysisResponse:
    try:
        evidence_result = build_evidence(
            equipment_id=request.equipment_id,
            query=request.query.strip(),
            file_path=request.file_path.strip() if request.file_path else None,
            selected_code=request.selected_code,
        )
    except EvidenceLinkError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc

    result = analyze_evidence(evidence_result, use_ollama=request.use_ollama)

    return AnalysisResponse(
        equipment_id=evidence_result.equipment_id,
        query=evidence_result.query,
        use_ollama=request.use_ollama,
        ai_used=result.ai_used,
        ai_available=result.ai_available,
        ai_error=result.error,
        summary=result.summary,
        reason=result.reason,
        confidence=result.confidence,
        inference=result.inference,
        answer=result.answer,
        answer_status=result.answer_status,
        evidence_summary=result.evidence_summary,
        evidence_answer=result.evidence_answer,
        evidence_reason=result.evidence_reason,
        ai_answer=result.ai_answer,
        evidence=[
            EvidenceRefItem(type=r.type, commit=r.commit, file=r.file, slide=r.slide)
            for r in result.evidence_refs
        ],
        parse_error=result.parse_error,
        ai_evidence_missing=result.ai_evidence_missing,
        git_candidates=evidence_result.git_candidates,
        change_item_candidates=[
            _map_change_item_candidate(c) for c in evidence_result.change_item_candidates
        ],
        evidence_links=[_map_evidence_link(link) for link in evidence_result.evidence_links],
        debug=EvidenceDebugInfo(
            change_item_link_candidate_count=evidence_result.change_item_link_candidate_count,
            fallback_documents_parsed=evidence_result.fallback_documents_parsed,
            change_item_total=evidence_result.change_item_total,
            equipment_filter_excluded=evidence_result.equipment_filter_excluded,
            equipment_filter_reason="filename equipment mismatch",
            query_relevance_excluded_links=evidence_result.query_relevance_excluded_links,
            query_keywords=evidence_result.query_keywords,
            weak_query_terms=evidence_result.weak_query_terms,
            request_functions=evidence_result.request_functions,
            request_files=evidence_result.request_files,
            path_scopes=evidence_result.path_scopes,
        ),
    )
