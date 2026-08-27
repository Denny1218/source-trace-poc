"""POC v2.3: Source Trace VS Code Extension analyze endpoint — `POST /api/trace/report`.

Reuses STEP 7 `build_evidence` and STEP 8 `analyze_evidence` untouched (no
re-scoring, no Gate/weight/Parser/Cache/DB Schema changes). This endpoint only:

- Accepts the Extension's direct request body
  ({equipment_id, query, file_path, selected_code, source_mode,
  detected_symbol, use_ollama}).
- Normalizes file_path / truncates selected_code before Evidence search.
- Synthesizes a searchable ``final_query_used`` from selected_code symbols /
  file mentions; pronoun-only questions with no context degrade to
  ``missing_context`` instead of searching filler words like "언제".
- Renders the STEP 8 result as the Extension's official Markdown.

This endpoint always returns 200 — equipment lookup failures, missing context,
and Ollama failures all degrade to a Markdown explanation instead of an HTTP
error, since a silent error would break the Extension's result document flow.

Note (PROJECT_SPEC v2.3 — Continue 연동 제거): this endpoint is the sole
official Backend contract for the Extension. It intentionally does not accept
the previous `/api/continue/trace` payload shape (`fullInput` / `options` /
`workspacePath`), does not track a per-request status/`request_id`, and does
not generate any Continue-only prompt wrapper. No compatibility alias for
`/api/continue/trace` is kept — see the removal completion report for why.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.trace import _map_evidence_link
from app.core.logging import get_logger
from app.schemas.trace_extension import (
    ExtensionEvidenceRefItem,
    ExtensionTraceRequest,
    ExtensionTraceResponse,
)
from app.services.evidence_service import EvidenceLinkError, build_evidence
from app.services.ollama_service import analyze_evidence
from app.services.trace_extension_service import (
    MISSING_CONTEXT_MESSAGE,
    apply_selected_symbol_guard,
    build_markdown_answer,
    build_search_query,
    detect_query_intent,
    extract_c_identifiers,
    extract_file_mention,
    extract_function_symbols,
    file_basename,
    merge_selected_code_symbols,
    normalize_file_path,
    normalize_query_text,
    preview_text,
    truncate_selected_code,
)

router = APIRouter(prefix="/api/trace", tags=["trace-report"])

logger = get_logger()


def _degraded_response(
    message: str,
    *,
    use_ollama: bool = True,
    equipment_id: int | None = None,
    answer_status: str = "adapter_error",
    equipment_resolved: bool = False,
    debug: dict | None = None,
) -> ExtensionTraceResponse:
    debug_info = {
        "equipment_resolved": equipment_resolved,
        "equipment_id": equipment_id,
        "answer_status": answer_status,
    }
    if debug:
        debug_info.update(debug)
        debug_info["answer_status"] = answer_status
    return ExtensionTraceResponse(
        name="장비 변경 이력 분석",
        description="Trace Backend 연동 안내",
        content=message,
        answer=message,
        confidence="low",
        evidence_summary=message,
        evidence_answer=message,
        evidence_reason=None,
        ai_answer=None,
        ai_used=False,
        use_ollama=use_ollama,
        answer_status=answer_status,
        citations=[],
        evidence_links=[],
        debug=debug_info,
    )


def _preview_query_line(text: str | None, limit: int = 120) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    one_line = " ".join(raw.split())
    return one_line[:limit] + "…" if len(one_line) > limit else one_line


@router.post("/report", response_model=ExtensionTraceResponse)
def trace_report(request: ExtensionTraceRequest) -> ExtensionTraceResponse:
    equipment_id = request.equipment_id
    use_ollama = request.use_ollama if request.use_ollama is not None else True

    raw_query = (request.query or "").strip()
    file_path = request.file_path
    selected_code, code_truncated = truncate_selected_code(request.selected_code)

    normalized_query_text = normalize_query_text(raw_query)
    extracted_symbols = extract_function_symbols(selected_code)
    selected_code_symbols = merge_selected_code_symbols(
        selected_code,
        extracted_symbols,
        detected_symbol=request.detected_symbol,
    )
    requested_symbols = selected_code_symbols or extract_c_identifiers(normalized_query_text)
    query_intent = detect_query_intent(raw_query)
    symbol_priority_applied = bool(requested_symbols)
    if not file_path:
        file_path = extract_file_mention(normalized_query_text)
    file_mention = file_basename(file_path) if not symbol_priority_applied else None
    final_query_used, query_build_source = build_search_query(
        raw_query, requested_symbols, file_mention
    )

    parse_debug = {
        "query_preview": preview_text(request.query, 100),
        "query_chars": len(request.query or ""),
        "normalized_query_text": preview_text(normalized_query_text, 300),
        "final_query_used": final_query_used,
        "final_file_path_used": None,
        "final_selected_code_chars": len(selected_code) if selected_code else 0,
        "selected_code_symbols": selected_code_symbols,
        "requested_symbols": requested_symbols,
        "direct_selected_code_preview": preview_text(selected_code, 100),
        "direct_selected_code_chars": len(selected_code) if selected_code else 0,
        "query_build_source": query_build_source,
        "query_intent": query_intent,
        "symbol_priority_applied": symbol_priority_applied,
        "file_path_used_as_scope_only": bool(symbol_priority_applied and file_path),
        "extension_source_mode": request.source_mode,
        "extension_detected_symbol": request.detected_symbol,
    }

    if equipment_id is None:
        return _degraded_response(
            "equipment_id가 설정되지 않았습니다. Source Trace Extension 설정에서 "
            "장비를 선택해 주세요.",
            use_ollama=use_ollama,
            debug=parse_debug,
        )

    if not raw_query and not selected_code and not file_path:
        return _degraded_response(
            "질문(query)이 비어 있습니다. 장비 변경 이력 조회 시 질문을 입력해 주세요.",
            use_ollama=use_ollama,
            equipment_id=equipment_id,
            equipment_resolved=True,
            debug=parse_debug,
        )

    # Pronoun/instruction-only question with no selectable context → do not
    # search on filler words like "언제" / "추가되었어".
    if not final_query_used or query_build_source == "missing_context":
        return _degraded_response(
            MISSING_CONTEXT_MESSAGE,
            use_ollama=use_ollama,
            equipment_id=equipment_id,
            answer_status="missing_context",
            equipment_resolved=True,
            debug=parse_debug,
        )

    normalized_path, path_method = normalize_file_path(file_path, equipment_id)
    parse_debug["final_file_path_used"] = normalized_path
    parse_debug["file_path_input"] = file_path
    parse_debug["file_path_normalized"] = normalized_path
    parse_debug["file_path_normalize_method"] = path_method

    try:
        evidence_result = build_evidence(
            equipment_id=equipment_id,
            query=final_query_used,
            file_path=normalized_path,
            selected_code=selected_code,
        )
    except EvidenceLinkError as exc:
        logger.info("Extension trace: build_evidence failed — %s", exc.message)
        return _degraded_response(
            exc.message,
            use_ollama=use_ollama,
            equipment_id=equipment_id,
            equipment_resolved=False,
            debug=parse_debug,
        )
    except Exception:  # Endpoint must never 500 the Extension result document.
        logger.exception("Extension trace: unexpected Evidence search failure")
        return _degraded_response(
            "변경 이력 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            use_ollama=use_ollama,
            equipment_id=equipment_id,
            equipment_resolved=False,
            debug=parse_debug,
        )

    primary_symbol = requested_symbols[0] if requested_symbols else None
    try:
        evidence_result, symbol_guard_applied = apply_selected_symbol_guard(
            evidence_result, primary_symbol
        )
    except Exception as exc:
        logger.info(
            "Extension trace formatting fallback reason=symbol_guard_failed "
            "query_intent=%s symbol=%s err=%s",
            query_intent,
            primary_symbol,
            type(exc).__name__,
        )
        symbol_guard_applied = False
    parse_debug["symbol_guard_applied"] = symbol_guard_applied
    try:
        if evidence_result.evidence_links:
            parse_debug["answer_top_title"] = getattr(
                evidence_result.evidence_links[0].change_item, "change_title", None
            )
            parse_debug["answer_link_count"] = len(evidence_result.evidence_links)
        else:
            parse_debug["answer_top_title"] = None
            parse_debug["answer_link_count"] = 0
    except Exception:
        parse_debug["answer_top_title"] = None

    try:
        result = analyze_evidence(evidence_result, use_ollama=use_ollama)
        markdown, history_debug = build_markdown_answer(
            evidence_result,
            result,
            use_ollama=use_ollama,
            query_intent=query_intent,
            primary_symbol=primary_symbol,
            symbol_guard_applied=symbol_guard_applied or symbol_priority_applied,
            file_path=normalized_path,
        )
        history_debug.pop("_lifecycle", None)
        analyzed_symbol = history_debug.get("analyzed_symbol") or primary_symbol
        parse_debug["requested_symbol"] = primary_symbol
        parse_debug["analyzed_symbol"] = analyzed_symbol
        if primary_symbol and analyzed_symbol and primary_symbol.lower() != analyzed_symbol.lower():
            mismatch_message = (
                "요청한 함수와 실제 분석된 함수가 일치하지 않아 결과 생성을 중단했습니다.\n\n"
                f"요청 Symbol: {primary_symbol}\n"
                f"분석 Symbol: {analyzed_symbol}"
            )
            return _degraded_response(
                mismatch_message,
                use_ollama=use_ollama,
                equipment_id=equipment_id,
                answer_status="symbol_mismatch",
                equipment_resolved=True,
                debug={**parse_debug, **(history_debug or {})},
            )

        debug_out = {
            "equipment_resolved": True,
            "equipment_id": equipment_id,
            "selected_code_truncated": code_truncated,
            "selected_code_chars": len(selected_code) if selected_code else 0,
            "answer_status": result.answer_status,
            **parse_debug,
            **(history_debug or {}),
        }

        try:
            mapped_links = [_map_evidence_link(link) for link in evidence_result.evidence_links]
        except Exception as exc:
            logger.info(
                "Extension trace formatting fallback reason=map_evidence_links "
                "query_intent=%s symbol=%s err=%s",
                query_intent,
                primary_symbol,
                type(exc).__name__,
            )
            mapped_links = []

        return ExtensionTraceResponse(
            name="장비 변경 이력 분석",
            description=f"'{evidence_result.query}' 분석 결과",
            content=markdown,
            answer=markdown,
            confidence=result.confidence or "low",
            evidence_summary=result.evidence_summary or markdown,
            evidence_answer=result.evidence_answer or markdown,
            evidence_reason=result.evidence_reason,
            ai_answer=result.ai_answer,
            ai_used=bool(result.ai_used),
            use_ollama=use_ollama,
            answer_status=result.answer_status or "ok",
            citations=[
                ExtensionEvidenceRefItem(
                    type=r.type, commit=r.commit, file=r.file, slide=r.slide
                )
                for r in (result.evidence_refs or [])
            ],
            evidence_links=mapped_links,
            debug=debug_out,
        )
    except Exception as exc:
        # Evidence already built — never 500 the Extension result document.
        logger.info(
            "Extension trace formatting fallback reason=%s query_intent=%s symbol=%s",
            type(exc).__name__,
            query_intent,
            primary_symbol,
        )
        logger.exception("Extension trace: response formatting failed after Evidence built")
        fallback_content = (
            "## 변경 이력 분석 결과\n\n"
            "### 요약\n"
            "관련 Evidence는 조회되었으나 응답 포맷 중 오류가 발생했습니다. "
            "Web UI Evidence Link 화면에서 동일 질의를 확인하거나 잠시 후 다시 시도해 주세요.\n\n"
            f"- final_query_used: `{final_query_used}`\n"
            f"- selected_code_symbols: {selected_code_symbols or '(없음)'}\n"
            f"- evidence_links: {len(getattr(evidence_result, 'evidence_links', []) or [])}\n"
        )
        parse_debug["answer_status"] = "adapter_format_error"
        parse_debug["format_error"] = type(exc).__name__
        return _degraded_response(
            fallback_content,
            use_ollama=use_ollama,
            equipment_id=equipment_id,
            answer_status="adapter_format_error",
            equipment_resolved=True,
            debug=parse_debug,
        )
