"""PROJECT_SPEC v2.4 §5~§8 — 선택 코드 변경 근거 조회 오케스트레이션.

함수 전체 이력 조회(``trace_extension_service`` / ``function_git_lifecycle_service``)
와 완전히 분리된 서비스다. 선택 코드 조회의 1차 근거는 항상 git blame과 실제
Diff이며, 키워드 후보 검색은 오직 (이미 확정된) blame Commit에 대한 공식 문서
후보를 찾는 보조 용도로만 사용한다 (§6.4) — 대표 Commit이나 대표 문서를
score로 결정하지 않는다.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.schemas.trace_selection import (
    MAX_SELECTION_LINE_SPAN,
    SelectionBlameRow,
    SelectionDocumentLink,
    SelectionLineHistoryRow,
    SelectionTraceRequest,
    SelectionTraceResponse,
)
from app.services.lifecycle_ppt import (
    LINK_COMMIT_DIRECT,
    FeatureDocument,
    build_ppt_link_for_entry,
    collect_feature_documents,
)
from app.services.selection_git_service import (
    SelectionGitError,
    classify_blame_commit_change,
    classify_change_kind_from_hunks,
    extract_overlapping_hunks,
    git_blame_lines,
    git_log_line_history,
    git_show_commit_diff,
    group_blame_lines,
    resolve_selection_repository,
    validate_revision,
    verify_selection_against_revision,
)

logger = get_logger()

_CHANGE_KIND_LABEL = {
    "added": "추가",
    "modified": "수정",
    "deleted": "삭제",
    "moved": "이동",
    "comment_only": "주석만 변경",
    "context_only": "변경 Commit 확인",
    "unknown": "변경 Commit 확인",
}

# Kinds proven by Diff structure — safe to show 추가/수정/삭제 in the table.
_CHANGE_KIND_CONFIRMED = frozenset({"added", "modified", "deleted", "moved", "comment_only"})

# Map selection-scope change classification onto the function-lifecycle
# change_type vocabulary so we can reuse `build_ppt_link_for_entry`'s strict
# commit-direct gating without duplicating its logic.
_CHANGE_KIND_TO_LIFECYCLE_TYPE = {
    "added": "body_change",
    "modified": "body_change",
    "moved": "body_change",
    "comment_only": "comment_or_log",
    "context_only": "related_candidate",
    "unknown": "related_candidate",
}


class SelectionValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def validate_selection_request(request: SelectionTraceRequest) -> None:
    if request.equipment_id is None:
        raise SelectionValidationError("equipment_id가 설정되지 않았습니다.")
    has_rel = bool((request.repo_relative_path or "").strip())
    has_fallback = bool((request.file_path or "").strip())
    if not has_rel and not has_fallback:
        raise SelectionValidationError(
            "repo_relative_path(또는 구버전 file_path)가 필요합니다."
        )
    if request.start_line is None or request.end_line is None:
        raise SelectionValidationError("선택 범위(시작·종료 행)가 설정되지 않았습니다.")
    if request.start_line < 1 or request.end_line < 1:
        raise SelectionValidationError("행 번호는 1 이상이어야 합니다.")
    if request.start_line > request.end_line:
        raise SelectionValidationError("시작 행이 종료 행보다 클 수 없습니다.")
    if (request.end_line - request.start_line + 1) > MAX_SELECTION_LINE_SPAN:
        raise SelectionValidationError(
            f"선택 범위가 너무 넓습니다 (최대 {MAX_SELECTION_LINE_SPAN}행)."
        )
    if not request.selected_code or not request.selected_code.strip():
        raise SelectionValidationError("공백만 선택되었습니다. 코드를 선택해 주세요.")


def _short(h: str) -> str:
    text = (h or "").strip()
    return text[:8] if len(text) >= 8 else text


def _build_document_links(
    *,
    equipment_id: int,
    file_path: str,
    enclosing_symbol: str | None,
    blame_rows: list[SelectionBlameRow],
) -> list[SelectionDocumentLink]:
    """Conservative direct-document lookup (§7).

    Only a strict Commit-direct link (`LINK_COMMIT_DIRECT` — symbol listed in
    the document's own related-function list AND the blamed commit's Diff
    confirms the change AND time/action compatibility) is shown. Any weaker
    connection (stage/feature-release, maintenance, related-reference) is
    intentionally suppressed here — those belong to the separate function
    lifecycle query, never to a single-line/block selection result.
    """
    if not enclosing_symbol:
        return []

    try:
        from app.services.evidence_service import EvidenceLinkError, build_evidence

        evidence_result = build_evidence(
            equipment_id=equipment_id,
            query=enclosing_symbol,
            file_path=file_path,
        )
    except Exception as exc:  # Document discovery must never break the blame result.
        logger.info("Selection ppt discovery skipped reason=%s", type(exc).__name__)
        return []

    docs: list[FeatureDocument] = collect_feature_documents(
        evidence_result, enclosing_symbol, file_path=file_path
    )
    if not docs:
        return []

    out: list[SelectionDocumentLink] = []
    seen: set[str] = set()
    for row in blame_rows:
        if row.is_uncommitted or row.change_kind == "unknown":
            continue
        lifecycle_type = _CHANGE_KIND_TO_LIFECYCLE_TYPE.get(row.change_kind, "related_candidate")
        link = build_ppt_link_for_entry(
            commit_hash=row.commit_hash,
            commit_date=row.author_date,
            message=row.commit_message,
            change_type=lifecycle_type,
            file_path=file_path,
            symbol=enclosing_symbol,
            feature_docs=docs,
            function_range_confirmed=row.change_kind in {"added", "modified", "moved"},
            diff_available=True,
        )
        if link is None or link.link_type != LINK_COMMIT_DIRECT:
            continue
        key = f"{link.document_name}|{link.slide_number}|{link.change_title}"
        if key in seen:
            continue
        seen.add(key)
        out.append(
            SelectionDocumentLink(
                document_name=link.document_name,
                slide_number=link.slide_number,
                change_title=link.change_title,
                csr_no=link.csr_no,
                versions=link.versions,
                link_reason=link.link_reason_user,
            )
        )
    return out


def analyze_selected_code(request: SelectionTraceRequest) -> SelectionTraceResponse:
    validate_selection_request(request)

    assert request.equipment_id is not None
    repo, resolve_method = resolve_selection_repository(
        equipment_id=request.equipment_id,
        repo_id=request.repo_id,
        repo_id_hint=request.repo_id_hint,
        repo_relative_path=request.repo_relative_path,
        file_path=request.file_path,
        revision=request.revision,
    )

    if not validate_revision(repo.repo_path, request.revision):
        raise SelectionValidationError(f"revision '{request.revision}'을(를) 확인할 수 없습니다.")

    # Guard: IDE line range + selected_code must match server revision blob
    # before blame / log -L. Prevents past-commit evidence for uncommitted
    # local-only selections that share the same line numbers.
    matched, _server_block = verify_selection_against_revision(
        repo.repo_path,
        repo.rel_path,
        start_line=request.start_line,
        end_line=request.end_line,
        selected_code=request.selected_code,
        revision=request.revision,
    )
    if not matched:
        content = render_selection_source_mismatch_markdown(
            request=request,
            repo_rel_path=repo.rel_path,
        )
        return SelectionTraceResponse(
            description=f"{repo.rel_path} {request.start_line}행 선택 코드 변경 근거",
            content=content,
            equipment_id=request.equipment_id,
            file_path=repo.rel_path,
            start_line=request.start_line,
            end_line=request.end_line,
            enclosing_symbol=request.enclosing_symbol,
            blame_rows=[],
            line_history=[],
            line_history_available=False,
            document_links=[],
            debug={
                "repository_id": repo.repository_id,
                "repository_name": repo.repository_name,
                "resolve_method": resolve_method,
                "repo_relative_path": repo.rel_path,
                "source_match": False,
                "blame_skipped": True,
                "blame_group_count": 0,
                "line_history_count": 0,
                "document_link_count": 0,
            },
        )

    blame_lines = git_blame_lines(
        repo.repo_path,
        repo.rel_path,
        request.start_line,
        request.end_line,
        revision=request.revision,
    )
    groups = group_blame_lines(blame_lines)

    blame_rows: list[SelectionBlameRow] = []
    diff_cache: dict[str, str | None] = {}
    for g in groups:
        commit_message: str | None = None
        author_date = g.author_time
        if not g.is_uncommitted:
            try:
                meta = git_show_commit_diff(repo.repo_path, g.commit_hash, repo.rel_path)
            except Exception:
                meta = None
            diff_cache[g.commit_hash] = meta
            try:
                from app.services.git_service import get_commit_metadata

                full_meta = get_commit_metadata(repo.repo_path, g.commit_hash)
                commit_message = (full_meta.get("message") or "").strip() or None
                author_date = full_meta.get("commit_date") or author_date
            except Exception:
                commit_message = g.summary

        diff_text = diff_cache.get(g.commit_hash)
        hunks = (
            []
            if g.is_uncommitted
            else extract_overlapping_hunks(
                diff_text, start_line=g.start_line, end_line=g.end_line
            )
        )
        if g.is_uncommitted:
            change_kind = "unknown"
        elif hunks:
            change_kind = classify_change_kind_from_hunks(hunks, g.sample_lines)
        else:
            change_kind = classify_blame_commit_change(diff_text, g.sample_lines)

        before_code = None
        after_code = None
        diff_hunk = None
        if hunks:
            before_parts = [ln for h in hunks for ln in h.before_lines()]
            after_parts = [ln for h in hunks for ln in h.after_lines()]
            before_code = "\n".join(before_parts).rstrip("\n") or None
            after_code = "\n".join(after_parts).rstrip("\n") or None
            diff_hunk = "".join(h.unified_text() for h in hunks).rstrip("\n") or None

        blame_rows.append(
            SelectionBlameRow(
                commit_hash=g.commit_hash,
                short_hash=_short(g.commit_hash),
                start_line=g.start_line,
                end_line=g.end_line,
                author=g.author,
                author_date=author_date,
                commit_message=commit_message or g.summary,
                is_uncommitted=g.is_uncommitted,
                is_boundary=g.boundary,
                change_kind=change_kind,
                before_code=before_code,
                after_code=after_code,
                diff_hunk=diff_hunk,
            )
        )

    history_entries = git_log_line_history(
        repo.repo_path,
        repo.rel_path,
        request.start_line,
        request.end_line,
        revision=request.revision,
    )
    line_history_available = history_entries is not None
    line_history = [
        SelectionLineHistoryRow(
            commit_hash=e.commit_hash,
            short_hash=_short(e.commit_hash),
            date=e.date,
            subject=e.subject,
        )
        for e in (history_entries or [])
    ]

    document_links = _build_document_links(
        equipment_id=request.equipment_id,
        file_path=repo.rel_path,
        enclosing_symbol=request.enclosing_symbol,
        blame_rows=blame_rows,
    )

    content = render_selection_markdown(
        request=request,
        repo_rel_path=repo.rel_path,
        blame_rows=blame_rows,
        line_history=line_history,
        line_history_available=line_history_available,
        document_links=document_links,
    )

    return SelectionTraceResponse(
        description=f"{repo.rel_path} {request.start_line}행 선택 코드 변경 근거",
        content=content,
        equipment_id=request.equipment_id,
        file_path=repo.rel_path,
        start_line=request.start_line,
        end_line=request.end_line,
        enclosing_symbol=request.enclosing_symbol,
        blame_rows=blame_rows,
        line_history=line_history,
        line_history_available=line_history_available,
        document_links=document_links,
        debug={
            "repository_id": repo.repository_id,
            "repository_name": repo.repository_name,
            "resolve_method": resolve_method,
            "repo_relative_path": repo.rel_path,
            "source_match": True,
            "blame_group_count": len(blame_rows),
            "line_history_count": len(line_history),
            "document_link_count": len(document_links),
        },
    )


def _range_label(start: int, end: int) -> str:
    return f"{start}행" if start == end else f"{start}-{end}행"


def _kind_label(kind: str) -> str:
    if kind in _CHANGE_KIND_CONFIRMED:
        return _CHANGE_KIND_LABEL.get(kind, "변경 Commit 확인")
    return "변경 Commit 확인"


_SOURCE_MISMATCH_NOTICE = (
    "선택한 코드와 서버 Git 소스가 일치하지 않습니다.\n"
    "로컬 변경사항이 아직 Commit/반영되지 않았거나 소스 버전이 다를 수 있습니다."
)


def render_selection_source_mismatch_markdown(
    *,
    request: SelectionTraceRequest,
    repo_rel_path: str,
) -> str:
    """Markdown when IDE selection does not match server revision lines."""
    lines: list[str] = []
    lines.append("# 선택 코드 변경 근거")
    lines.append("")
    lines.append("## 선택 코드")
    lines.append("")
    lines.append("```c")
    lines.append((request.selected_code or "").strip())
    lines.append("```")
    lines.append("")
    lines.append(f"- 파일: `{repo_rel_path}`")
    lines.append(f"- 범위: {_range_label(request.start_line or 0, request.end_line or 0)}")
    if request.enclosing_symbol:
        lines.append(f"- 포함 함수: `{request.enclosing_symbol}()`")
    lines.append("")
    lines.append("## 현재 라인의 Git 근거")
    lines.append("")
    lines.append(_SOURCE_MISMATCH_NOTICE)
    lines.append("")
    lines.append(
        "서버 revision 코드와 선택이 일치할 때만 git blame / line history를 제공합니다."
    )
    lines.append("")
    lines.append("## 실제 변경 내용")
    lines.append("")
    lines.append("- 소스 불일치로 실제 변경 내용을 조회하지 않았습니다.")
    lines.append("")
    lines.append("## line history")
    lines.append("")
    lines.append("- 소스 불일치로 line history를 조회하지 않았습니다.")
    lines.append("")
    lines.append("## 관련 문서")
    lines.append("")
    lines.append("관련 문서를 찾지 못했습니다.")
    lines.append("")
    lines.append("## 함수 전체 이력")
    lines.append("")
    if request.enclosing_symbol:
        lines.append(
            f"이 코드가 포함된 `{request.enclosing_symbol}()` 함수 전체 변경 이력은 "
            "`Source Trace: 함수 변경 이력 조회`에서 별도로 확인합니다."
        )
    else:
        lines.append(
            "포함 함수가 확인되지 않았습니다. 함수 전체 이력이 필요하면 "
            "`Source Trace: 함수 변경 이력 조회`를 함수명으로 별도 실행해 주세요."
        )
    lines.append("")
    return "\n".join(lines)


def render_selection_markdown(
    *,
    request: SelectionTraceRequest,
    repo_rel_path: str,
    blame_rows: list[SelectionBlameRow],
    line_history: list[SelectionLineHistoryRow],
    line_history_available: bool,
    document_links: list[SelectionDocumentLink],
) -> str:
    lines: list[str] = []
    lines.append("# 선택 코드 변경 근거")
    lines.append("")
    lines.append("## 선택 코드")
    lines.append("")
    lines.append("```c")
    lines.append((request.selected_code or "").strip())
    lines.append("```")
    lines.append("")
    lines.append(f"- 파일: `{repo_rel_path}`")
    lines.append(f"- 범위: {_range_label(request.start_line, request.end_line)}")
    if request.enclosing_symbol:
        lines.append(f"- 포함 함수: `{request.enclosing_symbol}()`")
    lines.append("")

    lines.append("## 현재 라인의 Git 근거")
    lines.append("")
    if not blame_rows:
        lines.append("git blame 결과를 확인하지 못했습니다.")
    else:
        lines.append("| 행 범위 | Commit | 변경일 | 작성자 | 변경 유형 | Commit 메시지 |")
        lines.append("|---|---|---|---|---|---|")
        for row in blame_rows:
            commit_disp = "미커밋(uncommitted)" if row.is_uncommitted else f"`{row.short_hash}`"
            kind_label = _kind_label(row.change_kind)
            msg = (row.commit_message or "").splitlines()[0][:80] if row.commit_message else ""
            lines.append(
                f"| {_range_label(row.start_line, row.end_line)} | {commit_disp} | "
                f"{row.author_date or ''} | {row.author or ''} | {kind_label} | {msg} |"
            )
            if row.is_boundary:
                lines.append(
                    f"> `{row.short_hash}`은(는) boundary Commit입니다 "
                    "(이전 이력을 추가로 추적하지 못했습니다)."
                )
    lines.append("")

    lines.append("## 실제 변경 내용")
    lines.append("")
    if not blame_rows:
        lines.append("- 확인 제한: git blame 결과가 없어 실제 변경 내용을 확인하지 못했습니다.")
    else:
        for row in blame_rows:
            if row.is_uncommitted:
                lines.append(
                    f"- {_range_label(row.start_line, row.end_line)}: 아직 Commit되지 않은 "
                    "로컬 변경입니다."
                )
                continue

            has_split = bool(row.before_code or row.after_code)
            has_hunk = bool(row.diff_hunk)
            if has_split and row.before_code and row.after_code:
                lines.append("### 변경 전")
                lines.append("```c")
                lines.append(row.before_code)
                lines.append("```")
                lines.append("")
                lines.append("### 변경 후")
                lines.append("```c")
                lines.append(row.after_code)
                lines.append("```")
                lines.append("")
                lines.append(f"- Commit: `{row.short_hash}`")
                if row.commit_message:
                    msg = row.commit_message.splitlines()[0].strip()
                    lines.append(f"- Commit 메시지: `{msg}`")
                kind_label = _kind_label(row.change_kind)
                if row.change_kind in _CHANGE_KIND_CONFIRMED:
                    lines.append(f"- 변경 유형: {kind_label}")
                lines.append("")
            elif has_hunk:
                lines.append("```diff")
                lines.append(row.diff_hunk.rstrip("\n"))
                lines.append("```")
                lines.append("")
                lines.append(f"- Commit: `{row.short_hash}`")
                if row.commit_message:
                    msg = row.commit_message.splitlines()[0].strip()
                    lines.append(f"- Commit 메시지: `{msg}`")
                lines.append("")
            elif row.change_kind in _CHANGE_KIND_CONFIRMED:
                kind_label = _kind_label(row.change_kind)
                lines.append(
                    f"- {_range_label(row.start_line, row.end_line)} (`{row.short_hash}`): "
                    f"{kind_label} — Diff에서 선택 코드와 관련된 변경을 확인했습니다."
                )
            else:
                lines.append(
                    f"- {_range_label(row.start_line, row.end_line)} (`{row.short_hash}`): "
                    "변경 Commit은 확인했지만 선택 라인과 겹치는 Diff hunk를 "
                    "추출하지 못했습니다."
                )
    lines.append("")

    lines.append("## line history")
    lines.append("")
    if not line_history_available:
        lines.append(
            "현재 라인의 blame Commit은 확인했지만 이전 line history는 코드 이동 "
            "또는 Git 추적 제한으로 완전하게 확인하지 못했습니다."
        )
    elif not line_history:
        lines.append("추가로 확인된 과거 변경 이력이 없습니다.")
    else:
        lines.append("| 날짜 | Commit | 변경 내용 |")
        lines.append("|---|---|---|")
        for h in line_history:
            subj = (h.subject or "")[:80]
            lines.append(f"| {h.date or ''} | `{h.short_hash}` | {subj} |")
    lines.append("")

    lines.append("## 관련 문서")
    lines.append("")
    if not document_links:
        lines.append("관련 문서를 찾지 못했습니다.")
    else:
        for doc in document_links:
            slide = f"Slide {doc.slide_number}" if doc.slide_number else ""
            ver = ", ".join(doc.versions) if doc.versions else ""
            lines.append(
                f"- `{doc.document_name}` {slide} — {doc.change_title or ''} "
                f"{('(' + ver + ')') if ver else ''}"
            )
            if doc.csr_no:
                lines.append(f"  - CSR: {doc.csr_no}")
            if doc.link_reason:
                lines.append(f"  - 연결 근거: {doc.link_reason}")
    lines.append("")

    lines.append("## 함수 전체 이력")
    lines.append("")
    if request.enclosing_symbol:
        lines.append(
            f"이 코드가 포함된 `{request.enclosing_symbol}()` 함수 전체 변경 이력은 "
            "`Source Trace: 함수 변경 이력 조회`에서 별도로 확인합니다."
        )
    else:
        lines.append(
            "포함 함수가 확인되지 않았습니다. 함수 전체 이력이 필요하면 "
            "`Source Trace: 함수 변경 이력 조회`를 함수명으로 별도 실행해 주세요."
        )
    lines.append("")

    return "\n".join(lines)
