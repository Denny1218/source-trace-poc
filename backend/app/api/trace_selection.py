"""PROJECT_SPEC v2.4 §5 — 선택 코드 변경 근거 조회 엔드포인트 `POST /api/trace/selection`.

함수/Symbol 전체 이력 조회(`/api/trace/report`)와 mode·schema·service가 명확히
분리된 별도 엔드포인트다. 선택 코드 원문은 서버 일반 로그에 출력하지 않는다
(§5 필수 검증).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.logging import get_logger
from app.schemas.trace_selection import SelectionTraceRequest, SelectionTraceResponse
from app.services.selection_git_service import SelectionGitError
from app.services.selection_trace_service import (
    SelectionValidationError,
    analyze_selected_code,
)

router = APIRouter(prefix="/api/trace", tags=["trace-selection"])

logger = get_logger()


def _degraded(message: str, request: SelectionTraceRequest, *, status: str) -> SelectionTraceResponse:
    return SelectionTraceResponse(
        content=message,
        answer_status=status,
        equipment_id=request.equipment_id,
        file_path=request.file_path,
        start_line=request.start_line,
        end_line=request.end_line,
        enclosing_symbol=request.enclosing_symbol,
        debug={"answer_status": status},
    )


@router.post("/selection", response_model=SelectionTraceResponse)
def trace_selection(request: SelectionTraceRequest) -> SelectionTraceResponse:
    # Selected code text itself must never reach general server logs — only
    # non-sensitive shape metadata (§5, §12.3).
    logger.info(
        "Selection trace request equipment_id=%s file_path=%s start_line=%s end_line=%s "
        "has_symbol=%s revision=%s",
        request.equipment_id,
        request.file_path,
        request.start_line,
        request.end_line,
        bool(request.enclosing_symbol),
        request.revision,
    )
    try:
        result = analyze_selected_code(request)
    except SelectionValidationError as exc:
        logger.info("Selection trace validation failed reason=%s", exc.message)
        return _degraded(exc.message, request, status="validation_error")
    except SelectionGitError as exc:
        logger.info("Selection trace git failure reason=%s", exc.message)
        return _degraded(exc.message, request, status="git_error")
    except Exception:
        logger.exception("Selection trace unexpected failure")
        return _degraded(
            "선택 코드 변경 근거 조회 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            request,
            status="unexpected_error",
        )

    logger.info(
        "Selection trace completed equipment_id=%s blame_groups=%s line_history=%s doc_links=%s",
        request.equipment_id,
        len(result.blame_rows),
        len(result.line_history),
        len(result.document_links),
    )
    return result
