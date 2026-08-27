"""STEP 8: Ollama-based Evidence Grounded Answer generation.

Order of operations (must not change — see PROJECT_SPEC_v2 STEP 8):

    query -> (STEP 4-7) Evidence Link Top N  ->  상위 Evidence만 선정  ->  Ollama

Response policy (qwen3.5:9b ops stability):

- Primary: Markdown / plain-text Korean answer from Ollama (not JSON-only).
- Optional compat: if the model still returns JSON with summary/reason, use it.
- If the body is non-empty meaningful text that is not valid JSON, use it as
  the answer (``answered_with_plain_text``) — do not discard a usable reply
  just because JSON parse failed.
- Empty / unusable body -> Evidence-grounded fallback.
- ``confidence`` / citations / evidence_refs are always server Evidence-based.
- No evidence -> skip Ollama entirely (``no_evidence``).
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import httpx

from app.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_MAX_EVIDENCE,
    OLLAMA_MODEL,
    OLLAMA_TEST_TIMEOUT_SECONDS,
    OLLAMA_TIMEOUT_SECONDS,
    TRACE_ANSWER_EVIDENCE_LIMIT,
    TRACE_ANSWER_MAX_DIFF_CHARS,
    TRACE_ANSWER_MAX_FIELD_CHARS,
    TRACE_ANSWER_MAX_PROMPT_CHARS,
)
from app.core.link_score_config import PRIMARY_EVIDENCE_TYPES
from app.core.logging import get_logger
from app.schemas.trace import GitCandidate
from app.services.change_item_candidate_service import ChangeItemCandidate
from app.services.evidence_service import EvidenceLink, EvidenceResult
from app.services.link_score_service import MatchReason

logger = get_logger()

NO_EVIDENCE_SUMMARY = "관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다."
AI_DISABLED_MESSAGE = "AI 분석 기능이 비활성화되어 있습니다."
AI_TIMEOUT_MESSAGE = "Ollama 응답 실패 — 서버 근거 기반 요약을 표시합니다."
AI_UNAVAILABLE_MESSAGE = "Ollama 응답 실패 — 서버 근거 기반 요약을 표시합니다."
AI_PLAIN_TEXT_MESSAGE = "AI 응답 형식은 표준과 달랐지만, 응답 본문을 표시합니다."
AI_FALLBACK_PARSE_MESSAGE = (
    "AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다."
)

AI_USER_DISABLED_MESSAGE = (
    "AI 보조 설명을 사용하지 않고 서버 근거 기반 요약만 표시합니다."
)
AI_SUCCESS_MESSAGE = "AI 보조 설명이 생성되었습니다."

STATUS_OK = "ok"
STATUS_NO_EVIDENCE = "no_evidence"
STATUS_PARSE_ERROR = "ollama_parse_error"
STATUS_PLAIN_TEXT = "answered_with_plain_text"
STATUS_TIMEOUT = "ollama_timeout"
STATUS_UNAVAILABLE = "ollama_unavailable"
STATUS_DISABLED = "ollama_disabled"
STATUS_USER_DISABLED = "ollama_skipped_by_user"
STATUS_PARTIAL = "partial"
STATUS_EMPTY = "ollama_empty_response"

_AI_SUCCESS_STATUSES = frozenset({STATUS_OK, STATUS_PARTIAL, STATUS_PLAIN_TEXT})

# qwen3.5:9b — ask for Korean Markdown prose, not JSON (JSON was unstable in ops).
SYSTEM_PROMPT = """당신은 장비 소스 변경 이력 분석 보조자다.

원칙:
- 제공된 근거만 사용한다.
- 근거에 없는 변경 이유를 사실처럼 생성하지 않는다.
- Git 변경 사실과 문서에 명시된 사유를 구분한다.
- 추론이 필요하면 "(추정)"이라고 표시한다.
- 변경 사유를 확인할 수 없으면 "확인 불가"라고 답한다.
- Commit Hash / 문서명 / Slide는 근거에 있는 값만 언급한다.

응답 형식:
- 한국어 Markdown 또는 평문만 출력한다.
- JSON, code fence(```), 시스템 설명, 인사말은 출력하지 않는다.
- 다음 구성으로 짧게 작성한다:
  1) 한두 문장 요약
  2) 연결 근거 불릿(가능하면)
  3) Git/변경내역서 근거 요약(가능하면)
"""

_USER_PROMPT_SUFFIX = """
위 근거만 사용해 한국어로 답변하세요.
JSON을 출력하지 마세요. Markdown 또는 평문만 출력하세요.
"""

_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_RAW_RESPONSE_PREVIEW_LIMIT = 500
_MIN_PLAIN_TEXT_LEN = 20
_TINY_PROMPT = "안녕. 한 문장으로 답해줘."
_TINY_RESPONSE_PREVIEW = 200

_LINK_REASON_LINES = {
    "same_file_path": "Git 변경 파일과 변경내역서의 소스 파일이 일치합니다.",
    "same_file_basename": "Git 변경 파일명과 변경내역서의 소스 파일명이 일치합니다.",
    "same_function_exact": "변경내역서의 소스/함수 항목에 요청 함수가 포함되어 있습니다.",
    "csr_exact": "CSR 번호가 Git과 변경내역서에서 일치합니다.",
    "commit_message_change_title": "Commit 메시지와 변경내역서 제목이 연결됩니다.",
}


@dataclass
class EvidenceRef:
    type: str  # git | document
    commit: str | None = None
    file: str | None = None
    slide: int | None = None


@dataclass
class OllamaAnalysisResult:
    ai_available: bool
    summary: str | None
    reason: str | None
    confidence: str  # high | medium | low
    inference: bool
    answer: str
    answer_status: str = STATUS_OK
    evidence_refs: list[EvidenceRef] = field(default_factory=list)
    error: str | None = None
    parse_error: bool = False
    ai_evidence_missing: bool = False
    raw_response: str | None = None
    # Server Evidence-only summary/answer — ALWAYS populated, independent of
    # Ollama outcome. UI must show this first and never let AI text replace it.
    evidence_summary: str = ""
    evidence_answer: str = ""
    evidence_reason: str | None = None
    # Ollama's own generated text — only set when an AI answer was actually
    # produced this request (None when skipped/disabled/failed/no evidence).
    ai_answer: str | None = None
    # Whether Ollama was actually invoked for this request (use_ollama=true,
    # OLLAMA_ENABLED, and Evidence present).
    ai_used: bool = False


class OllamaCallError(Exception):
    """Raised only by the raw transport call — always caught internally."""

    def __init__(self, message: str, *, kind: str = "unavailable"):
        self.message = message
        self.kind = kind  # timeout | unavailable
        super().__init__(message)


def _git_evidence_ref(git: GitCandidate) -> EvidenceRef:
    return EvidenceRef(type="git", commit=git.commit_hash)


def _document_evidence_ref(item: ChangeItemCandidate) -> EvidenceRef:
    return EvidenceRef(
        type="document",
        file=item.file_name or item.file_path,
        slide=item.slide_no,
    )


def _select_evidence_for_context(
    evidence_result: EvidenceResult,
) -> tuple[list[EvidenceLink], list[GitCandidate]]:
    """Top Evidence Link pairs, or (if none linked) Top query-relevant Git only."""
    links = evidence_result.evidence_links[:OLLAMA_MAX_EVIDENCE]
    if links:
        return links, []

    relevant_git = [
        g
        for g in evidence_result.git_candidates
        if g.query_relevance_level in {"높음", "보통"}
    ]
    return [], relevant_git[:OLLAMA_MAX_EVIDENCE]


def compute_evidence_confidence(
    links: list[EvidenceLink], git_only: list[GitCandidate]
) -> str:
    """Rule-based confidence from Evidence — independent of Ollama output shape."""
    if not links and not git_only:
        return "low"

    if links:
        top = links[0]
        primary_count = sum(
            1 for r in top.match_reasons if r.type in PRIMARY_EVIDENCE_TYPES
        )
        level = top.query_relevance_level or "없음"
        if level == "높음" and primary_count >= 1:
            return "high"
        if level in {"높음", "보통"} and primary_count >= 1:
            return "medium"
        if level in {"높음", "보통"}:
            return "medium"
        if primary_count >= 1:
            return "medium"
        return "low"

    top_git = git_only[0]
    if top_git.query_relevance_level == "높음":
        return "medium"
    if top_git.query_relevance_level == "보통":
        return "low"
    return "low"


def _short_hash(commit: str | None) -> str:
    if not commit:
        return "(hash 없음)"
    return commit[:7] if len(commit) > 7 else commit


def _basename(path: str | None) -> str | None:
    if not path:
        return None
    name = PurePosixPath(path.replace("\\", "/")).name
    return name or None


def _truncate(text: str | None, limit: int | None = None) -> str | None:
    if text is None:
        return None
    max_chars = TRACE_ANSWER_MAX_FIELD_CHARS if limit is None else limit
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1] + "…"


def _estimate_tokens(prompt_chars: int) -> int:
    """Rough mixed KR/EN heuristic (~4 chars/token). Not a tokenizer."""
    return max(1, prompt_chars // 4) if prompt_chars else 0


def _cap_prompt(prompt: str) -> tuple[str, bool]:
    """Hard-cap prompt length; never log the body."""
    if len(prompt) <= TRACE_ANSWER_MAX_PROMPT_CHARS:
        return prompt, False
    return prompt[: TRACE_ANSWER_MAX_PROMPT_CHARS - 1] + "…", True


def build_ollama_request_meta(
    *,
    links: list[EvidenceLink],
    git_only: list[GitCandidate],
    prompt_chars: int,
    prompt_truncated: bool = False,
) -> dict:
    """Safe diagnostic metadata — no prompt/diff/raw_text body."""
    git_count = len(links) if links else len(git_only)
    doc_count = len(links)
    return {
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL.rstrip("/"),
        "timeout_seconds": OLLAMA_TIMEOUT_SECONDS,
        "evidence_limit": TRACE_ANSWER_EVIDENCE_LIMIT,
        "evidence_count": git_count,
        "git_evidence_count": git_count,
        "document_evidence_count": doc_count,
        "prompt_chars": prompt_chars,
        "prompt_estimated_tokens": _estimate_tokens(prompt_chars),
        "prompt_truncated": prompt_truncated,
        "max_diff_chars": TRACE_ANSWER_MAX_DIFF_CHARS,
        "max_field_chars": TRACE_ANSWER_MAX_FIELD_CHARS,
        "max_prompt_chars": TRACE_ANSWER_MAX_PROMPT_CHARS,
    }


def _log_ollama_diag(phase: str, meta: dict, **extra: object) -> None:
    """INFO diagnostic line. Never includes Full Prompt / Diff / PPT text."""
    forbidden = {"prompt", "full_prompt", "diff", "raw_text", "system", "body"}
    safe_extra = {k: v for k, v in extra.items() if k.lower() not in forbidden}
    parts = [f"{k}={meta[k]}" for k in (
        "model",
        "base_url",
        "timeout_seconds",
        "evidence_count",
        "git_evidence_count",
        "document_evidence_count",
        "prompt_chars",
        "prompt_estimated_tokens",
        "max_diff_chars",
        "max_field_chars",
        "max_prompt_chars",
    ) if k in meta]
    parts.extend(f"{k}={v}" for k, v in safe_extra.items())
    logger.info("Ollama %s %s", phase, " ".join(parts))


def _result_type_for_status(answer_status: str, *, parse_error: bool = False) -> str:
    mapping = {
        STATUS_OK: "success",
        STATUS_PARTIAL: "success",
        STATUS_PLAIN_TEXT: "success",
        STATUS_TIMEOUT: "timeout",
        STATUS_UNAVAILABLE: "connection_error",
        STATUS_PARSE_ERROR: "parse_error",
        STATUS_EMPTY: "empty_response",
        STATUS_DISABLED: "fallback",
        STATUS_NO_EVIDENCE: "fallback",
    }
    if answer_status in mapping:
        return mapping[answer_status]
    if parse_error:
        return "parse_error"
    return "fallback"


def _reason_line_for_match(reason: MatchReason) -> str | None:
    base = _LINK_REASON_LINES.get(reason.type)
    if not base:
        return None
    tip = reason.git_value or reason.change_item_value
    if reason.type in {"same_file_path", "same_file_basename"} and tip:
        name = _basename(tip) or tip
        return (
            f"Git 변경 파일과 변경내역서의 소스 파일이 {name}로 일치합니다."
            if reason.type == "same_file_path"
            else f"Git 변경 파일명과 변경내역서의 소스 파일명이 {name}로 일치합니다."
        )
    if reason.type == "same_function_exact" and tip:
        return f"변경내역서의 소스/함수 항목에 {tip}()이 포함되어 있습니다."
    if reason.type == "csr_exact" and tip:
        return f"CSR 번호 {tip}가 Git과 변경내역서에서 일치합니다."
    if reason.type == "commit_message_change_title" and tip:
        return f"Commit 메시지와 변경내역서 제목이 '{tip}' 키워드로 연결됩니다."
    return base


def _query_match_connection_lines(link: EvidenceLink) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for r in link.query_match_reasons or []:
        if getattr(r, "strength", "core") == "weak":
            continue
        field = getattr(r, "field", "")
        keyword = getattr(r, "keyword", "")
        if field == "commit_message" and keyword:
            text = f"Commit 메시지에도 {keyword}이 포함되어 있습니다."
            if text not in seen:
                seen.add(text)
                lines.append(text)
        elif field == "source_function" and keyword:
            text = f"변경내역서의 소스/함수 항목에 {keyword}이 포함되어 있습니다."
            if text not in seen:
                seen.add(text)
                lines.append(text)
    return lines


def build_fallback_answer(
    links: list[EvidenceLink],
    git_only: list[GitCandidate],
    evidence_refs: list[EvidenceRef],
) -> tuple[str, str | None, str]:
    """Evidence-grounded natural-language fallback (summary, reason, full answer)."""
    if not links and not git_only:
        answer = _compose_answer(NO_EVIDENCE_SUMMARY, None, False, [])
        return NO_EVIDENCE_SUMMARY, None, answer

    if links:
        top = links[0]
        title = (top.change_item.change_title or "").strip() or "(제목 없음)"
        summary = f"가장 관련 높은 변경 항목은 `{title}`입니다."

        connection: list[str] = []
        seen: set[str] = set()
        for mr in top.match_reasons:
            line = _reason_line_for_match(mr)
            if line and line not in seen:
                seen.add(line)
                connection.append(line)
        for line in _query_match_connection_lines(top):
            if line not in seen:
                seen.add(line)
                connection.append(line)

        reason_parts = connection[:4]
        reason = "\n".join(f"- {p}" for p in reason_parts) if reason_parts else None

        lines = [summary, ""]
        if reason_parts:
            lines.append("연결 근거:")
            lines.extend(f"- {p}" for p in reason_parts)
            lines.append("")
        lines.append("근거:")
        for r in evidence_refs:
            if r.type == "git" and r.commit:
                lines.append(f"- Commit {_short_hash(r.commit)}")
            elif r.type == "document":
                slide = f", Slide {r.slide}" if r.slide is not None else ""
                lines.append(f"- {r.file or '(문서명 없음)'}{slide}")
        answer = "\n".join(lines)
        return summary, reason, answer

    top_git = git_only[0]
    summary = (
        f"관련 Git Commit `{_short_hash(top_git.commit_hash)}`은 확인했지만 "
        "관련 변경내역서를 찾지 못해 변경 사유는 확인할 수 없습니다."
    )
    reason = None
    answer = _compose_answer(summary, reason, False, evidence_refs)
    return summary, reason, answer


def _format_git_section(idx: int, git: GitCandidate, diff_excerpt: str | None) -> str:
    msg_limit = min(300, TRACE_ANSWER_MAX_FIELD_CHARS)
    lines = [
        f"[Git 근거 {idx}]",
        "",
        "Commit:",
        git.commit_hash,
        "",
        "Date:",
        git.commit_date,
        "",
        "File:",
        git.file_path,
        "",
        "Message:",
        _truncate(git.message, msg_limit) or "",
    ]
    clipped = _truncate(diff_excerpt, TRACE_ANSWER_MAX_DIFF_CHARS)
    if clipped:
        lines += ["", "Diff (excerpt):", clipped]
    return "\n".join(lines)


def _format_document_section(idx: int, item: ChangeItemCandidate) -> str:
    title_limit = min(200, TRACE_ANSWER_MAX_FIELD_CHARS)
    content_parts = [
        p
        for p in (
            _truncate(item.change_title, title_limit),
            _truncate(item.business_background),
            _truncate(item.current_status),
            _truncate(item.as_is),
            _truncate(item.to_be),
        )
        if p
    ]
    # Never send full raw_text — structured fields only (truncated).
    return "\n".join(
        [
            f"[변경내역서 근거 {idx}]",
            "",
            "File:",
            item.file_name or item.file_path or "(문서명 없음)",
            "",
            "Slide:",
            str(item.slide_no),
            "",
            "Content:",
            "\n".join(content_parts) if content_parts else "(내용 없음)",
        ]
    )


def build_ollama_context(
    query: str,
    links: list[EvidenceLink],
    git_only: list[GitCandidate],
) -> str:
    """Evidence-only prompt body — never the full Git repo or full PPT text."""
    sections = [f"[사용자 질문]\n\n{query}"]

    if links:
        for idx, link in enumerate(links, start=1):
            sections.append(
                _format_git_section(idx, link.git_candidate, link.diff_excerpt)
            )
            sections.append(_format_document_section(idx, link.change_item))
    else:
        for idx, git in enumerate(git_only, start=1):
            sections.append(_format_git_section(idx, git, None))
        sections.append(
            "[변경내역서 근거]\n\n관련 변경내역서 근거를 찾지 못했습니다."
        )

    return "\n\n\n".join(sections)


def _call_ollama_raw(
    prompt: str,
    *,
    system: str | None = None,
    timeout_seconds: float | None = None,
    append_user_suffix: bool = True,
) -> str:
    """The only network call in this module — mock/monkeypatch this in tests.

    Does NOT set Ollama ``format=json`` — qwen3.5:9b ops showed unstable
    JSON-only compliance; we ask for Markdown/plain text instead.
    """
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    timeout = OLLAMA_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    body_prompt = prompt + (_USER_PROMPT_SUFFIX if append_user_suffix else "")
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url,
                json={
                    "model": OLLAMA_MODEL,
                    "system": system if system is not None else SYSTEM_PROMPT,
                    "prompt": body_prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise OllamaCallError(
            "Ollama 응답이 시간 내에 도착하지 않았습니다.", kind="timeout"
        ) from exc
    except httpx.HTTPError as exc:
        raise OllamaCallError("Ollama 서버에 연결할 수 없습니다.", kind="unavailable") from exc
    except ValueError as exc:
        raise OllamaCallError("Ollama 응답을 해석할 수 없습니다.", kind="unavailable") from exc
    return data.get("response", "") if isinstance(data, dict) else ""


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    fence = _CODE_FENCE_RE.search(text)
    if fence:
        return fence.group(1).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text


def _parse_ollama_json(raw: str) -> dict | None:
    """Optional compat path — JSON is no longer required."""
    if not raw or not raw.strip():
        return None
    candidates = [raw.strip(), _strip_code_fences(raw)]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and (
                "summary" in parsed or "reason" in parsed or "answer" in parsed
            ):
                return parsed
        except (ValueError, TypeError):
            pass
        match = _JSON_OBJECT_RE.search(candidate)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict) and (
                    "summary" in parsed or "reason" in parsed or "answer" in parsed
                ):
                    return parsed
            except (ValueError, TypeError):
                pass
    return None


def _looks_like_json_blob(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") and stripped.endswith("}")


def _is_meaningful_plain_text(raw: str) -> bool:
    text = (raw or "").strip()
    if len(text) < _MIN_PLAIN_TEXT_LEN:
        return False
    # Broken / incomplete JSON-shaped payloads are not usable prose.
    if text.startswith("{") and _parse_ollama_json(text) is None:
        return False
    if _looks_like_json_blob(text) and _parse_ollama_json(text) is None:
        return False
    return True


def _summary_from_plain_text(text: str) -> str:
    first = text.strip().splitlines()[0].strip()
    first = first.lstrip("#").strip()
    if len(first) > 160:
        return first[:159] + "…"
    return first or text[:160]


def _compose_answer(
    summary: str | None,
    reason: str | None,
    inference: bool,
    evidence_refs: list[EvidenceRef],
) -> str:
    lines: list[str] = [summary or NO_EVIDENCE_SUMMARY]
    if reason and reason != summary:
        lines.append("")
        if reason.lstrip().startswith("-"):
            lines.append(reason if not inference else f"(추정)\n{reason}")
        else:
            lines.append(("(추정) " if inference else "") + reason)

    git_refs = [r for r in evidence_refs if r.type == "git"]
    doc_refs = [r for r in evidence_refs if r.type == "document"]

    if git_refs:
        lines.append("")
        lines.append("Git 근거")
        lines.extend(f"- {r.commit}" for r in git_refs)

    if doc_refs:
        lines.append("")
        lines.append("변경내역서 근거")
        for r in doc_refs:
            lines.append(f"- {r.file}")
            if r.slide is not None:
                lines.append(f"  Slide {r.slide}")

    return "\n".join(lines)


def _append_server_citations(answer_body: str, evidence_refs: list[EvidenceRef]) -> str:
    """Ensure server Evidence citations appear even when AI prose omitted them."""
    body = (answer_body or "").strip()
    git_refs = [r for r in evidence_refs if r.type == "git" and r.commit]
    doc_refs = [r for r in evidence_refs if r.type == "document"]
    if not git_refs and not doc_refs:
        return body

    already_has_git = any(r.commit and r.commit[:7] in body for r in git_refs)
    already_has_doc = any((r.file or "") and (r.file or "") in body for r in doc_refs)
    if already_has_git and (already_has_doc or not doc_refs):
        return body

    lines = [body, ""] if body else []
    if git_refs and not already_has_git:
        lines.append("Git 근거")
        lines.extend(f"- {r.commit}" for r in git_refs)
        lines.append("")
    if doc_refs and not already_has_doc:
        lines.append("변경내역서 근거")
        for r in doc_refs:
            lines.append(f"- {r.file}")
            if r.slide is not None:
                lines.append(f"  Slide {r.slide}")
    return "\n".join(lines).strip()


def _deterministic_refs(
    links: list[EvidenceLink], git_only: list[GitCandidate]
) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    if links:
        for link in links:
            refs.append(_git_evidence_ref(link.git_candidate))
            refs.append(_document_evidence_ref(link.change_item))
    else:
        refs.extend(_git_evidence_ref(g) for g in git_only)
    return refs


def _interpret_ollama_response(
    raw: str,
    *,
    confidence: str,
    evidence_refs: list[EvidenceRef],
    fb_summary: str,
    fb_reason: str | None,
    fb_answer: str,
) -> OllamaAnalysisResult:
    """Markdown-first interpretation with JSON compat + plain-text salvage."""
    text = (raw or "").strip()
    if not text:
        logger.info("Ollama empty response — using evidence fallback")
        return OllamaAnalysisResult(
            ai_available=True,
            summary=fb_summary,
            reason=fb_reason,
            confidence=confidence,
            inference=False,
            error=AI_FALLBACK_PARSE_MESSAGE,
            answer=fb_answer,
            answer_status=STATUS_EMPTY,
            evidence_refs=evidence_refs,
            parse_error=True,
            raw_response=None,
        )

    parsed = _parse_ollama_json(text)
    if parsed is not None:
        summary = parsed.get("summary") or parsed.get("answer")
        reason = parsed.get("reason")
        inference = bool(parsed.get("inference", False))
        ai_evidence = parsed.get("evidence")
        ai_evidence_missing = not ai_evidence
        summary_text = summary if isinstance(summary, str) and summary.strip() else None
        reason_text = reason if isinstance(reason, str) and reason.strip() else None
        if summary_text:
            answer = _append_server_citations(
                _compose_answer(summary_text, reason_text, inference, evidence_refs),
                evidence_refs,
            )
            return OllamaAnalysisResult(
                ai_available=True,
                summary=summary_text,
                reason=reason_text,
                confidence=confidence,
                inference=inference,
                answer=answer,
                answer_status=STATUS_PARTIAL if ai_evidence_missing else STATUS_OK,
                evidence_refs=evidence_refs,
                ai_evidence_missing=ai_evidence_missing,
            )
        # JSON without usable summary — fall through to plain / fallback.

    if _is_meaningful_plain_text(text):
        body = _strip_code_fences(text)
        # If after fence strip it became empty JSON leftovers, fall back.
        if not _is_meaningful_plain_text(body):
            body = text
        was_json_attempt = _looks_like_json_blob(text.strip()) or (
            "```json" in text.lower()
        )
        summary = _summary_from_plain_text(body)
        answer = _append_server_citations(body, evidence_refs)
        inference = "(추정)" in body
        return OllamaAnalysisResult(
            ai_available=True,
            summary=summary,
            reason=None,
            confidence=confidence,
            inference=inference,
            answer=answer,
            answer_status=STATUS_PLAIN_TEXT if was_json_attempt else STATUS_OK,
            evidence_refs=evidence_refs,
            parse_error=was_json_attempt,
            error=AI_PLAIN_TEXT_MESSAGE if was_json_attempt else None,
            ai_evidence_missing=True,
            raw_response=text[:_RAW_RESPONSE_PREVIEW_LIMIT],
        )

    logger.info("Ollama response unusable — using evidence fallback")
    return OllamaAnalysisResult(
        ai_available=True,
        summary=fb_summary,
        reason=fb_reason,
        confidence=confidence,
        inference=False,
        error=AI_FALLBACK_PARSE_MESSAGE,
        answer=fb_answer,
        answer_status=STATUS_PARSE_ERROR,
        evidence_refs=evidence_refs,
        parse_error=True,
        raw_response=text[:_RAW_RESPONSE_PREVIEW_LIMIT],
    )


def analyze_evidence(
    evidence_result: EvidenceResult, *, use_ollama: bool = True
) -> OllamaAnalysisResult:
    """STEP 8 entry point — build Evidence Grounded Answer from STEP 7 Evidence.

    ``use_ollama=False`` skips the Ollama call entirely (user opt-out) while
    still returning the full server Evidence-based summary/confidence/citations.
    """
    query = evidence_result.query
    links, git_only = _select_evidence_for_context(evidence_result)
    evidence_refs = _deterministic_refs(links, git_only)
    confidence = compute_evidence_confidence(links, git_only)
    fb_summary, fb_reason, fb_answer = build_fallback_answer(
        links, git_only, evidence_refs
    )

    if not links and not git_only:
        logger.info("Ollama analysis skipped: no grounded evidence for query")
        return OllamaAnalysisResult(
            ai_available=True,
            summary=NO_EVIDENCE_SUMMARY,
            reason=None,
            confidence=confidence,
            inference=False,
            answer=fb_answer,
            answer_status=STATUS_NO_EVIDENCE,
            evidence_refs=[],
            evidence_summary=fb_summary,
            evidence_answer=fb_answer,
            evidence_reason=fb_reason,
            ai_answer=None,
            ai_used=False,
        )

    if not use_ollama:
        logger.info("Ollama analysis skipped by user (use_ollama=false)")
        return OllamaAnalysisResult(
            ai_available=False,
            summary=fb_summary,
            reason=fb_reason,
            confidence=confidence,
            inference=False,
            error=AI_USER_DISABLED_MESSAGE,
            answer=fb_answer,
            answer_status=STATUS_USER_DISABLED,
            evidence_refs=evidence_refs,
            evidence_summary=fb_summary,
            evidence_answer=fb_answer,
            evidence_reason=fb_reason,
            ai_answer=None,
            ai_used=False,
        )

    if not OLLAMA_ENABLED:
        logger.info("Ollama analysis disabled (OLLAMA_ENABLED=false)")
        return OllamaAnalysisResult(
            ai_available=False,
            summary=fb_summary,
            reason=fb_reason,
            confidence=confidence,
            inference=False,
            error=AI_DISABLED_MESSAGE,
            answer=fb_answer,
            answer_status=STATUS_DISABLED,
            evidence_refs=evidence_refs,
            evidence_summary=fb_summary,
            evidence_answer=fb_answer,
            evidence_reason=fb_reason,
            ai_answer=None,
            ai_used=False,
        )

    prompt_raw = build_ollama_context(query, links, git_only)
    prompt, prompt_truncated = _cap_prompt(prompt_raw)
    meta = build_ollama_request_meta(
        links=links,
        git_only=git_only,
        prompt_chars=len(prompt),
        prompt_truncated=prompt_truncated,
    )
    request_start = time.strftime("%Y-%m-%dT%H:%M:%S")
    _log_ollama_diag(
        "request_start",
        meta,
        request_start_time=request_start,
        evidence_limit=OLLAMA_MAX_EVIDENCE,
    )

    started = time.perf_counter()
    try:
        raw = _call_ollama_raw(prompt)
    except OllamaCallError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        is_timeout = exc.kind == "timeout"
        result_type = "timeout" if is_timeout else "connection_error"
        _log_ollama_diag(
            "request_end",
            meta,
            request_start_time=request_start,
            elapsed_ms=elapsed_ms,
            result_type=result_type,
        )
        logger.error("Ollama error: %s", exc.message)
        return OllamaAnalysisResult(
            ai_available=False,
            summary=fb_summary,
            reason=fb_reason,
            confidence=confidence,
            inference=False,
            error=AI_TIMEOUT_MESSAGE if is_timeout else AI_UNAVAILABLE_MESSAGE,
            answer=fb_answer,
            answer_status=STATUS_TIMEOUT if is_timeout else STATUS_UNAVAILABLE,
            evidence_refs=evidence_refs,
            evidence_summary=fb_summary,
            evidence_answer=fb_answer,
            evidence_reason=fb_reason,
            ai_answer=None,
            ai_used=True,
        )

    result = _interpret_ollama_response(
        raw,
        confidence=confidence,
        evidence_refs=evidence_refs,
        fb_summary=fb_summary,
        fb_reason=fb_reason,
        fb_answer=fb_answer,
    )
    result.evidence_summary = fb_summary
    result.evidence_answer = fb_answer
    result.evidence_reason = fb_reason
    result.ai_used = True
    result.ai_answer = result.answer if result.answer_status in _AI_SUCCESS_STATUSES else None
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result_type = _result_type_for_status(
        result.answer_status, parse_error=result.parse_error
    )
    # Empty / parse failure after a transport success still counts as degraded.
    if result.answer_status in {STATUS_PARSE_ERROR, STATUS_EMPTY}:
        result_type = (
            "empty_response"
            if result.answer_status == STATUS_EMPTY
            else "parse_error"
        )
        if result.answer == fb_answer:
            # Explicit fallback after unusable model output.
            if result_type == "parse_error":
                pass  # keep parse_error; also note fallback in log
    _log_ollama_diag(
        "request_end",
        meta,
        request_start_time=request_start,
        elapsed_ms=elapsed_ms,
        result_type=result_type,
        answer_status=result.answer_status,
        used_fallback=result.answer == fb_answer and result_type != "success",
    )
    return result


@dataclass
class OllamaTinyTestResult:
    ok: bool
    model: str
    elapsed_ms: int
    response_preview: str | None = None
    error_type: str | None = None
    base_url: str | None = None
    timeout_seconds: float | None = None


def run_ollama_tiny_test() -> OllamaTinyTestResult:
    """Ollama-only smoke test (no Git/PPT/Evidence). For ops diagnosis."""
    timeout = OLLAMA_TEST_TIMEOUT_SECONDS
    meta = {
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL.rstrip("/"),
        "timeout_seconds": timeout,
        "evidence_count": 0,
        "git_evidence_count": 0,
        "document_evidence_count": 0,
        "prompt_chars": len(_TINY_PROMPT),
        "prompt_estimated_tokens": _estimate_tokens(len(_TINY_PROMPT)),
        "max_diff_chars": TRACE_ANSWER_MAX_DIFF_CHARS,
        "max_field_chars": TRACE_ANSWER_MAX_FIELD_CHARS,
        "max_prompt_chars": TRACE_ANSWER_MAX_PROMPT_CHARS,
    }
    request_start = time.strftime("%Y-%m-%dT%H:%M:%S")
    _log_ollama_diag(
        "tiny_test_start",
        meta,
        request_start_time=request_start,
    )
    started = time.perf_counter()
    try:
        raw = _call_ollama_raw(
            _TINY_PROMPT,
            system="한 문장으로만 짧게 답하세요.",
            timeout_seconds=timeout,
            append_user_suffix=False,
        )
    except OllamaCallError as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        err = "timeout" if exc.kind == "timeout" else "connection_error"
        _log_ollama_diag(
            "tiny_test_end",
            meta,
            request_start_time=request_start,
            elapsed_ms=elapsed_ms,
            result_type=err,
        )
        return OllamaTinyTestResult(
            ok=False,
            model=OLLAMA_MODEL,
            elapsed_ms=elapsed_ms,
            error_type=err,
            base_url=OLLAMA_BASE_URL.rstrip("/"),
            timeout_seconds=timeout,
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    preview = (raw or "").strip()
    if not preview:
        _log_ollama_diag(
            "tiny_test_end",
            meta,
            request_start_time=request_start,
            elapsed_ms=elapsed_ms,
            result_type="empty_response",
        )
        return OllamaTinyTestResult(
            ok=False,
            model=OLLAMA_MODEL,
            elapsed_ms=elapsed_ms,
            error_type="empty_response",
            base_url=OLLAMA_BASE_URL.rstrip("/"),
            timeout_seconds=timeout,
        )

    _log_ollama_diag(
        "tiny_test_end",
        meta,
        request_start_time=request_start,
        elapsed_ms=elapsed_ms,
        result_type="success",
        response_preview_chars=min(len(preview), _TINY_RESPONSE_PREVIEW),
    )
    return OllamaTinyTestResult(
        ok=True,
        model=OLLAMA_MODEL,
        elapsed_ms=elapsed_ms,
        response_preview=preview[:_TINY_RESPONSE_PREVIEW],
        base_url=OLLAMA_BASE_URL.rstrip("/"),
        timeout_seconds=timeout,
    )
