"""Function Git lifecycle for the Extension's official answer (STEP 9 adapter).

Each lifecycle item uses the **exact** git_change row for (commit_id, file_path).
Evidence Link scoring is untouched — this module only formats answers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.db.database import get_connection
from app.schemas.trace import GitCandidate
from app.services.evidence_service import EvidenceLink, EvidenceResult
from app.services.lifecycle_ppt import (
    LINK_COMMIT_DIRECT,
    LINK_DEV_REFERENCE,
    LINK_FEATURE_RELEASE,
    LINK_MAINTENANCE,
    LINK_RELATED,
    PptLink,
    STRENGTH_COMMIT_DIRECT,
    STRENGTH_RELATED,
    STRENGTH_STAGE,
    build_ppt_link_for_entry,
    collect_feature_documents,
    collect_stage_official_docs,
    connection_strength,
    merge_official_doc_collections,
    ppt_link_type_user_label,
    unique_official_docs,
)
from app.services.trace_service import get_git_change_record, resolve_git_change_record

# User-facing labels (no internal search jargon).
_CHANGE_TYPE_LABELS: dict[str, str] = {
    "function_creation": "함수 최초 추가",
    "function_creation_estimated": "최초 추가 추정",
    "function_deletion": "함수 삭제",
    "signature_change": "함수 시그니처 변경",
    "body_change": "함수 본문 로직 변경",
    "card_type_setting": "카드 유형 설정 변경",
    "date_logic_change": "날짜 비교 로직 변경",
    "transfer_reboarding_change": "환승·재승차 판정 변경",
    "institution_condition_change": "기관별 적용 조건 변경",
    "time_limit_condition_change": "시간 제한 조건 변경",
    "fare_penalty_condition_change": "요금·할인·패널티 조건 변경",
    "climate_condition_change": "기후동행 관련 조건 변경",
    "branch_change": "조건문/분기 변경",
    "return_handling_change": "반환값/오류 처리 변경",
    "call_site_change": "함수 호출부 변경",
    "comment_or_log": "로그/주석 변경",
    "related_candidate": "관련 변경 후보",
    "diff_unavailable": "Diff 확인 불가",
}

_TOPIC_CHANGE_TYPES = frozenset(
    {
        "transfer_reboarding_change",
        "institution_condition_change",
        "time_limit_condition_change",
        "fare_penalty_condition_change",
        "climate_condition_change",
    }
)

_CORE_TYPES = frozenset(
    {
        "function_creation",
        "function_creation_estimated",
        "function_deletion",
        "signature_change",
        "body_change",
        "card_type_setting",
        "date_logic_change",
        "branch_change",
        "return_handling_change",
    }
    | _TOPIC_CHANGE_TYPES
)

_CHANGE_TYPE_PRIORITY: dict[str, int] = {
    "function_creation": 100,
    "function_creation_estimated": 95,
    "function_deletion": 94,
    "signature_change": 88,
    "body_change": 82,
    "transfer_reboarding_change": 84,
    "climate_condition_change": 83,
    "fare_penalty_condition_change": 83,
    "institution_condition_change": 82,
    "time_limit_condition_change": 82,
    "card_type_setting": 81,
    "date_logic_change": 80,
    "branch_change": 79,
    "return_handling_change": 78,
    "call_site_change": 45,
    "comment_or_log": 35,
    "related_candidate": 12,
    "diff_unavailable": 5,
}

_FUNC_HISTORY_FETCH_LIMIT = 50
_PARENT_WALK_MAX_DEPTH = 8

_CARD_TYPE_RE = re.compile(
    r"usertype|user_type|카드\s*유형|청소년|어린이|성인|cardtype|card_type",
    re.IGNORECASE,
)
# Narrow to birthday/registration-number specific tokens. Generic "날짜"/"date"/
# "비교"/"적용일" words appear in many unrelated business rules (reboarding time
# windows, climate-card penalty windows, etc.) and must not alone imply a
# birthday/date-of-birth comparison change (PROJECT_SPEC v2.4 §9).
_DATE_LOGIC_RE = re.compile(
    r"생년월일|birthday|생일|주민(?:등록)?번호",
    re.IGNORECASE,
)
_LOG_RE = re.compile(r"log|로그|printf|trace|debug", re.IGNORECASE)
_BRANCH_RE = re.compile(r"\bif\b|\belse\b|switch|case\b", re.IGNORECASE)
_MERGE_MSG_RE = re.compile(r"^\s*merge\b", re.IGNORECASE)
_DEV_LOG_MSG_RE = re.compile(
    r"(테스트\s*)?로그\s*(삭제|제거|정리)|log\s*(delete|remove|clean)|printf|디버그\s*로그",
    re.IGNORECASE,
)
_DATE_HARDCODE_MSG_RE = re.compile(
    r"하드코딩|날짜\s*(비교|조건)?\s*(삭제|제거)|적용일\s*(삭제|제거)|date\s*compar",
    re.IGNORECASE,
)

# Domain-topic keywords — checked against function-scoped Diff changed lines
# first; Commit message is a fallback when Diff is absent or inconclusive.
# When both disagree, Diff wins (PROJECT_SPEC v2.4 §10.3).
_REBOARD_TOPIC_RE = re.compile(r"재승차|재개표|환승", re.IGNORECASE)
_CLIMATE_TOPIC_RE = re.compile(r"기후동행|climate", re.IGNORECASE)
_PENALTY_TOPIC_RE = re.compile(
    r"패널티|강제할인|할인\s*적용|요금\s*(적용|부과|계산)|penalty|discount", re.IGNORECASE
)
_INSTITUTION_TOPIC_RE = re.compile(r"기관\s*(추가|확대|적용|별)", re.IGNORECASE)
_TIME_LIMIT_TOPIC_RE = re.compile(
    r"\d+\s*분\s*(재승차|재개표|이내|내)|시간\s*(초과|변경|제한)", re.IGNORECASE
)

# Priority order matters: reboarding/climate/penalty are the most specific
# business topics and must win over the more generic institution/time-limit
# matches when a message mentions several at once (e.g. "15분 재승차 시간
# 변경 및 기관추가" is primarily a reboarding change, not an institution one).
_TOPIC_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (_REBOARD_TOPIC_RE, "transfer_reboarding_change", "환승·재승차 판정 조건을 변경했습니다."),
    (_CLIMATE_TOPIC_RE, "climate_condition_change", "기후동행카드 관련 환승·패널티 조건을 변경했습니다."),
    (_PENALTY_TOPIC_RE, "fare_penalty_condition_change", "요금·할인·패널티 처리 조건을 변경했습니다."),
    (_INSTITUTION_TOPIC_RE, "institution_condition_change", "기관별 적용 조건을 변경했습니다."),
    (_TIME_LIMIT_TOPIC_RE, "time_limit_condition_change", "시간 제한 조건을 변경했습니다."),
]


def _detect_topic_blob(text: str | None) -> tuple[str, str] | None:
    """Return (change_type, description) from topic keywords in arbitrary text."""
    if not text:
        return None
    for pattern, change_type, desc in _TOPIC_RULES:
        if pattern.search(text):
            return change_type, desc
    return None


def _function_changed_blob(stats: dict, diff: str | None) -> str:
    """Changed lines scoped to the target function hunk when available."""
    in_function_lines = stats.get("in_function_changed_lines")
    if in_function_lines:
        return " ".join(in_function_lines)[:4000]
    if not diff:
        return ""
    changed_lines: list[str] = []
    for raw in diff.splitlines()[:200]:
        if raw.startswith("+") or raw.startswith("-"):
            if raw.startswith("+++") or raw.startswith("---"):
                continue
            changed_lines.append(raw[1:])
    return " ".join(changed_lines)[:2000]


def _resolve_topic_change_type(diff_blob: str, message: str | None) -> str | None:
    """Pick a domain topic; when Diff and message disagree, Diff wins."""
    diff_topic = _detect_topic_blob(diff_blob)
    msg_topic = _detect_topic_blob(message)
    if diff_topic and msg_topic and diff_topic[0] != msg_topic[0]:
        return diff_topic[0]
    if diff_topic:
        return diff_topic[0]
    if msg_topic:
        return msg_topic[0]
    return None

# Internal reason → user-facing limitation (analysis section only).
_USER_LIMITATION_NOTES: dict[str, str] = {
    "symbol_not_in_diff": "확보된 Diff에서 대상 함수를 직접 확인하지 못했습니다.",
    "symbol_in_diff_scope_unknown": (
        "함수명은 Diff에 있으나 본문 변경 여부를 자동 확정하지 못했습니다."
    ),
    "message_only": "Commit 메시지에만 함수명이 포함되어 있습니다.",
    "diff_unavailable": "해당 커밋의 정확한 Diff를 확보하지 못했습니다.",
    "keyword_in_diff_hunk_header_only": "Diff 헤더에만 함수명이 검색되었습니다.",
    "merge_no_function_change": "Merge 커밋이나 본문 변경이 확인되지 않아 제외했습니다.",
    "weak_overlap": "기능 일부만 일치하는 참고자료로 연결했습니다.",
}

_SECTION_CORE = "core"
_SECTION_OTHER = "other"
_SECTION_MAINT = "maintenance"
_SECTION_UNCONFIRMED = "unconfirmed"


@dataclass
class FunctionGitHistoryEntry:
    commit_id: int
    commit_hash: str
    commit_date: str | None
    message: str | None
    file_path: str
    change_type: str
    change_type_label: str
    change_description: str
    impact: str | None
    confidence: str
    confidence_label: str
    is_core: bool
    ppt_title: str | None = None
    ppt_file: str | None = None
    ppt_slide: int | None = None
    ppt_link_level: str = "none"  # direct | indirect | none (compat)
    ppt_link_reason: str | None = None
    ppt_link: PptLink | None = None
    ppt_links: list[PptLink] = field(default_factory=list)
    priority: int = 0
    section: str = "core"  # core | other | maintenance | unconfirmed
    diff_state: str | None = None
    confirmation_note: str | None = None
    debug_item: dict = field(default_factory=dict)


@dataclass
class FunctionGitLifecycleResult:
    entries: list[FunctionGitHistoryEntry] = field(default_factory=list)
    creation: FunctionGitHistoryEntry | None = None
    excluded: list[dict] = field(default_factory=list)
    debug: dict = field(default_factory=dict)
    document_text: str = ""
    citation_lines: list[str] = field(default_factory=list)
    overall_confidence: str = "low"
    overall_confidence_label: str = "낮음"
    # Backward-compat for trace_extension_service callers
    lines: list[str] = field(default_factory=list)
    summary_lines: list[str] = field(default_factory=list)


def _symbol_in_diff(diff: str | None, symbol: str) -> bool:
    if not diff:
        return False
    if symbol in diff:
        return True
    return symbol.lower() in diff.lower()


def _user_limitation_note(reason: str | None, diff_state: str | None = None) -> str:
    if diff_state and diff_state in _USER_LIMITATION_NOTES:
        return _USER_LIMITATION_NOTES[diff_state]
    if reason and reason in _USER_LIMITATION_NOTES:
        return _USER_LIMITATION_NOTES[reason]
    return "변경 내용을 자동으로 확정하지 못했습니다."


def _assign_section(change_type: str, is_core: bool) -> str:
    # PROJECT_SPEC v2.5 §1.6 / §8 — without confirmed target-function body Diff,
    # do not promote into 주요 Git 변경 (core) or 유지보수.
    if not is_core:
        if change_type == "comment_or_log":
            return _SECTION_OTHER
        return _SECTION_UNCONFIRMED
    if change_type == "date_logic_change":
        return _SECTION_MAINT
    if change_type in {"related_candidate", "diff_unavailable"}:
        return _SECTION_UNCONFIRMED
    if change_type in {"comment_or_log", "call_site_change"}:
        return _SECTION_OTHER
    return _SECTION_CORE


def _is_merge_commit(message: str | None) -> bool:
    return bool(message and _MERGE_MSG_RE.match(message.strip()))


def _merge_has_function_change(
    stats: dict, change_type: str, is_core: bool
) -> bool:
    if is_core:
        return True
    touched = stats.get("added_line_count", 0) + stats.get("deleted_line_count", 0)
    if change_type in {"comment_or_log", "call_site_change"} and touched > 0:
        return True
    return touched > 0 and stats.get("function_range_confirmed")


# Final lifecycle inclusion — message/topic-only must not survive when there is
# no target-function Diff evidence (body/context/call-site/symbol-in-diff).
_MESSAGE_ONLY_LIFECYCLE_REASONS = frozenset(
    {
        "message_topic",
        "message_log_cleanup",
        "message_date_hardcode",
        "message_card_type",
        "message_only",
    }
)


def _has_target_function_evidence(stats: dict, reason: str, change_type: str) -> bool:
    """True when Diff (or call-site) shows the queried function is involved."""
    if change_type == "call_site_change" or reason == "call_site_only":
        return True
    if reason in {
        "symbol_only",
        "symbol_in_diff_scope_unknown",
        "keyword_in_diff_hunk_header_only",
    }:
        return True
    evidence = stats.get("evidence_tier")
    if evidence in {EVIDENCE_DIRECT_BODY, EVIDENCE_FUNCTION_CONTEXT}:
        return True
    if stats.get("function_range_confirmed"):
        return True
    if stats.get("symbol_definition_found"):
        return True
    if int(stats.get("plus_sym", 0) or 0) + int(stats.get("minus_sym", 0) or 0) > 0:
        return True
    return False


def _lifecycle_exclusion_reason(
    *,
    change_type: str,
    reason: str,
    stats: dict,
) -> str | None:
    """Return exclusion key when Commit must not appear in function lifecycle."""
    # Keep when target-function evidence exists (incl. symbol-in-diff, body
    # unconfirmed). Message-topic wording must not drop those commits.
    if _has_target_function_evidence(stats, reason, change_type):
        return None
    if reason in _MESSAGE_ONLY_LIFECYCLE_REASONS:
        return reason
    if reason in {"symbol_not_in_diff", "diff_unavailable"}:
        return reason
    if change_type == "related_candidate":
        return reason or "related_no_function_evidence"
    return None


def _ppt_link_user_label(level: str) -> str:
    return {"direct": "직접", "indirect": "간접", "none": "없음"}.get(level, "없음")


def _ppt_level_from_link(link: PptLink | None) -> str:
    if link is None:
        return "none"
    # Only Diff+doc commit-direct counts as "direct" for user wording.
    if link.link_type == LINK_COMMIT_DIRECT:
        return "direct"
    if link.link_type in {
        LINK_FEATURE_RELEASE,
        LINK_DEV_REFERENCE,
        LINK_MAINTENANCE,
        LINK_RELATED,
    }:
        return "indirect"
    return "none"


def _basename(path: str | None) -> str | None:
    if not path:
        return None
    name = PurePosixPath(str(path).replace("\\", "/")).name
    return name or None


def _short_hash(commit: str | None) -> str:
    if not commit:
        return "(hash 없음)"
    text = str(commit).strip()
    return text[:8] if len(text) >= 8 else text


def _confidence_label(level: str) -> str:
    return {"high": "높음", "medium": "보통", "low": "낮음"}.get(level, level)


def _strip_diff_prefix(line: str) -> tuple[str, str]:
    if line.startswith(("+++", "---", "@@")):
        return "", line
    if line[:1] in "+- ":
        return line[0], line[1:]
    return " ", line


def _is_comment_line(text: str) -> bool:
    t = text.strip()
    return (
        t.startswith("//")
        or t.startswith("/*")
        or t.startswith("*")
        or t.startswith("#")
    )


def _looks_like_definition(text: str, symbol: str) -> bool:
    """True for function definition / prototype lines (not bare call statements)."""
    if symbol not in text:
        return False
    stripped = text.strip()
    # Bare `FN(...);` / `FN(...)` at start — call statement, or K&R without `;`.
    if re.match(rf"^{re.escape(symbol)}\s*\(", stripped):
        return not stripped.endswith(";")
    # Typed definition/prototype requires at least one type/storage token.
    pattern = re.compile(
        rf"(?:^|[\s:;{{])(?:(?:static|inline|extern|const|unsigned|signed|struct|"
        rf"void|int|char|long|short|float|double|BOOL|bool|UINT|DWORD|BYTE)\s+|\*\s*)+"
        rf"{re.escape(symbol)}\s*\(",
        re.IGNORECASE,
    )
    return bool(pattern.search(text))


def _looks_like_call(text: str, symbol: str) -> bool:
    if not re.search(rf"\b{re.escape(symbol)}\s*\(", text):
        return False
    return not _looks_like_definition(text, symbol)


def _line_has_symbol(text: str, symbol: str) -> bool:
    return symbol in text or symbol.lower() in text.lower()


# PROJECT_SPEC v2.5.1 §1.7 — Diff evidence tiers (not display labels).
EVIDENCE_DIRECT_BODY = "DIRECT_BODY_CHANGE"
EVIDENCE_FUNCTION_CONTEXT = "FUNCTION_CONTEXT_CHANGE"
EVIDENCE_SYMBOL_ONLY = "SYMBOL_ONLY"
EVIDENCE_MESSAGE_ONLY = "MESSAGE_ONLY"

_HUNK_HEADER_RE = re.compile(r"^@@[^@]*@@(.*)$")


def _hunk_header_context(raw: str) -> str:
    """Return the optional function-context text after the second ``@@``."""
    m = _HUNK_HEADER_RE.match(raw.rstrip("\n"))
    if not m:
        return ""
    return (m.group(1) or "").strip()


def _parse_diff_stats(diff: str | None, symbol: str) -> dict:
    stats = {
        "added_line_count": 0,
        "deleted_line_count": 0,
        "plus_def": 0,
        "minus_def": 0,
        "plus_sym": 0,
        "minus_sym": 0,
        "plus_call": 0,
        "minus_call": 0,
        "plus_comment": 0,
        "minus_comment": 0,
        "added_samples": [],
        "deleted_samples": [],
        "symbol_definition_found": False,
        "function_range_confirmed": False,
        # Changed (+/-) lines observed only while inside the target function's
        # hunk context. Used to scope classification so unrelated changes
        # elsewhere in the same diff cannot leak into the change-type decision.
        "in_function_changed_lines": [],
        # v2.5.1 evidence tier — refined at end of parse / by analyze_function_commit.
        "evidence_tier": EVIDENCE_SYMBOL_ONLY,
        "hunk_header_scoped": False,
        "direct_body_lines": 0,
        "context_scoped_lines": 0,
    }
    if not diff:
        stats["evidence_tier"] = EVIDENCE_MESSAGE_ONLY
        return stats

    symbol_seen_in_context = False
    in_function = False
    hunk_header_scoped = False
    confirmed_any = False
    scoped_change_count = 0
    direct_body_count = 0
    saw_definition_line = False

    for raw in diff.splitlines():
        if raw.startswith("@@"):
            # New hunk: reset *cursor* only. Do not clear already-confirmed
            # evidence from earlier hunks (PROJECT_SPEC v2.5.1 §1.7).
            in_function = False
            symbol_seen_in_context = False
            hunk_header_scoped = False
            ctx = _hunk_header_context(raw)
            if ctx and _line_has_symbol(ctx, symbol):
                # Git often names the enclosing function only in the @@ header
                # for mid-function body edits.
                hunk_header_scoped = True
                in_function = True
                stats["hunk_header_scoped"] = True
            continue

        mark, text = _strip_diff_prefix(raw)
        if not mark or mark not in "+-":
            if mark == " " and _line_has_symbol(text, symbol):
                if _looks_like_definition(text, symbol):
                    stats["symbol_definition_found"] = True
                    saw_definition_line = True
                    symbol_seen_in_context = True
                    in_function = True
                elif in_function or symbol_seen_in_context:
                    in_function = True
            continue

        if mark == "+":
            stats["added_line_count"] += 1
        else:
            stats["deleted_line_count"] += 1

        scoped_now = bool(in_function or symbol_seen_in_context or hunk_header_scoped)
        if scoped_now:
            scoped_change_count += 1
            if len(stats["in_function_changed_lines"]) < 400:
                stats["in_function_changed_lines"].append(text)
            confirmed_any = True
            if saw_definition_line or symbol_seen_in_context:
                direct_body_count += 1

        if _line_has_symbol(text, symbol):
            is_comment = _is_comment_line(text)
            is_def = _looks_like_definition(text, symbol)
            is_call = _looks_like_call(text, symbol)
            if is_def:
                stats["symbol_definition_found"] = True
                saw_definition_line = True
                in_function = True
                symbol_seen_in_context = True

            if mark == "+":
                stats["plus_sym"] += 1
                if len(stats["added_samples"]) < 4:
                    stats["added_samples"].append(text.strip()[:160])
                if is_comment:
                    stats["plus_comment"] += 1
                if is_def:
                    stats["plus_def"] += 1
                elif is_call:
                    stats["plus_call"] += 1
            else:
                stats["minus_sym"] += 1
                if len(stats["deleted_samples"]) < 4:
                    stats["deleted_samples"].append(text.strip()[:160])
                if is_comment:
                    stats["minus_comment"] += 1
                if is_def:
                    stats["minus_def"] += 1
                elif is_call:
                    stats["minus_call"] += 1

    if confirmed_any and scoped_change_count > 0:
        stats["function_range_confirmed"] = True
    elif (
        symbol_seen_in_context
        and stats["added_line_count"] + stats["deleted_line_count"] > 0
        and scoped_change_count > 0
    ):
        stats["function_range_confirmed"] = True

    stats["direct_body_lines"] = direct_body_count
    stats["context_scoped_lines"] = scoped_change_count

    if stats["function_range_confirmed"] and scoped_change_count > 0:
        if saw_definition_line or direct_body_count > 0:
            stats["evidence_tier"] = EVIDENCE_DIRECT_BODY
        elif stats["hunk_header_scoped"]:
            stats["evidence_tier"] = EVIDENCE_FUNCTION_CONTEXT
        else:
            stats["evidence_tier"] = EVIDENCE_DIRECT_BODY
    elif _symbol_in_diff(diff, symbol):
        stats["evidence_tier"] = EVIDENCE_SYMBOL_ONLY
    else:
        stats["evidence_tier"] = EVIDENCE_MESSAGE_ONLY

    return stats


def _strict_creation_candidate(stats: dict) -> bool:
    """True only when diff shows a new definition block (not context-only)."""
    if stats["plus_def"] <= 0 or stats["minus_def"] > 0:
        return False
    if stats["minus_sym"] > 0:
        return False
    if stats["added_line_count"] < 3:
        return False
    return stats["plus_sym"] >= 1 or stats["added_line_count"] >= 5


def _symbol_in_unchanged_context(diff: str, symbol: str) -> bool:
    for raw in diff.splitlines():
        mark, text = _strip_diff_prefix(raw)
        if mark != " ":
            continue
        if symbol in text and _looks_like_definition(text, symbol):
            return True
    return False


def _get_parent_commit_id(commit_id: int) -> int | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT gc.parent_hash, gc.repository_id
            FROM git_commit gc
            WHERE gc.id = ?
            """,
            (commit_id,),
        ).fetchone()
        if not row or not row["parent_hash"]:
            return None
        parent = conn.execute(
            """
            SELECT id FROM git_commit
            WHERE repository_id = ? AND commit_hash = ?
            LIMIT 1
            """,
            (row["repository_id"], row["parent_hash"]),
        ).fetchone()
        return int(parent["id"]) if parent else None
    finally:
        conn.close()


def ancestor_file_has_function_definition(
    commit_id: int, file_path: str, symbol: str
) -> bool | None:
    """Walk parents until the file patch is found; True if symbol already defined."""
    current_id = commit_id
    for _ in range(_PARENT_WALK_MAX_DEPTH):
        parent_id = _get_parent_commit_id(current_id)
        if parent_id is None:
            return None
        record = get_git_change_record(parent_id, file_path)
        if record and record.get("diff"):
            diff = record["diff"]
            if _symbol_in_unchanged_context(diff, symbol):
                return True
            parent_stats = _parse_diff_stats(diff, symbol)
            if _strict_creation_candidate(parent_stats):
                return True
            if parent_stats["symbol_definition_found"] and not _strict_creation_candidate(
                parent_stats
            ):
                return True
            if symbol in diff and parent_stats["plus_sym"] + parent_stats["minus_sym"] > 0:
                return True
            return False
        current_id = parent_id
    return None


def _refine_body_subtype(stats: dict, message: str | None, diff: str | None) -> str:
    # PROJECT_SPEC v2.4 §10.3 — when Diff and Commit message conflict on
    # change nature, the function-scoped Diff wins. Message is a fallback when
    # Diff is absent or inconclusive. Generic regex heuristics (card/date/if)
    # are applied to changed lines only so untouched context tokens cannot
    # override a clearer message topic.
    diff_blob = _function_changed_blob(stats, diff)

    topic_type = _resolve_topic_change_type(diff_blob, message)
    if topic_type:
        return topic_type

    if diff_blob:
        if _CARD_TYPE_RE.search(diff_blob):
            return "card_type_setting"
        if _DATE_LOGIC_RE.search(diff_blob):
            return "date_logic_change"
        if _BRANCH_RE.search(diff_blob):
            return "branch_change"
        if re.search(r"return|error|err_|retval", diff_blob, re.IGNORECASE):
            return "return_handling_change"
        return "body_change"

    if message:
        if _CARD_TYPE_RE.search(message):
            return "card_type_setting"
        if _DATE_LOGIC_RE.search(message):
            return "date_logic_change"
        if _BRANCH_RE.search(message):
            return "branch_change"
        if re.search(r"return|error|err_|retval", message, re.IGNORECASE):
            return "return_handling_change"
    return "body_change"


def analyze_function_commit(
    *,
    diff: str | None,
    symbol: str,
    message: str | None,
    parent_has_function: bool | None,
    diff_available: bool,
) -> tuple[str, str, str, str, bool]:
    """Return (change_type, description, confidence, classification_reason, is_core)."""
    if not diff_available:
        promoted = _promote_from_message_only(message, symbol)
        if promoted:
            return promoted
        return (
            "diff_unavailable",
            "- 정확한 함수 변경 내용은 자동으로 요약하지 못했습니다.\n"
            "- Diff를 확보하지 못해 변경 범위를 확정하지 못했습니다.",
            "low",
            "diff_unavailable",
            False,
        )

    if not diff or not _symbol_in_diff(diff, symbol):
        # Diff exists without target-function/alias evidence — do not promote from
        # Commit message topic alone (false-positive into function lifecycle).
        if message and symbol.lower() in message.lower():
            return (
                "related_candidate",
                "- 검색 단계에서 관련 커밋으로 수집되었습니다.\n"
                "- Commit 메시지에만 함수명이 포함되어 있습니다.",
                "low",
                "message_only",
                False,
            )
        return (
            "related_candidate",
            "- 검색 단계에서 관련 커밋으로 수집되었지만 확보된 Diff에서는 "
            "대상 함수의 직접 변경을 확인하지 못했습니다.",
            "low",
            "symbol_not_in_diff",
            False,
        )

    stats = _parse_diff_stats(diff, symbol)
    sym_touched = stats["plus_sym"] + stats["minus_sym"]
    evidence = stats.get("evidence_tier") or EVIDENCE_SYMBOL_ONLY
    in_function_scope = bool(
        stats["function_range_confirmed"]
        and (
            stats["added_line_count"] + stats["deleted_line_count"] > 0
            or len(stats.get("in_function_changed_lines") or []) > 0
        )
    )

    # v2.5.1 §1.7 — function-scoped Diff evidence promotes to core lifecycle.
    if evidence in {EVIDENCE_DIRECT_BODY, EVIDENCE_FUNCTION_CONTEXT} and in_function_scope:
        scoped_lines = stats.get("in_function_changed_lines") or []
        blob = " ".join(scoped_lines) + " " + (message or "")
        msg = message or ""
        log_in_scope = bool(_LOG_RE.search(" ".join(scoped_lines)))
        log_in_message = bool(
            _DEV_LOG_MSG_RE.search(msg) or _LOG_RE.search(msg)
        )
        if (
            scoped_lines
            and log_in_scope
            and (
                stats["plus_comment"] + stats["minus_comment"] > 0
                or log_in_message
            )
            and not _CARD_TYPE_RE.search(blob)
            and stats["plus_def"] + stats["minus_def"] == 0
        ):
            return (
                "comment_or_log",
                _build_log_description(stats, message),
                "medium",
                (
                    "in_function_scope_log"
                    if evidence == EVIDENCE_DIRECT_BODY
                    else "function_context_log"
                ),
                False,
            )

        if _strict_creation_candidate(stats):
            if parent_has_function is True:
                subtype = _refine_body_subtype(stats, message, diff)
                return (
                    subtype,
                    _build_body_description(subtype, stats, message, symbol),
                    "medium",
                    "parent_already_has_function",
                    True,
                )
            if parent_has_function is False:
                return (
                    "function_creation",
                    _build_creation_description(stats, parent_verified_absent=True),
                    "high",
                    "parent_missing_function_definition",
                    True,
                )
            return (
                "function_creation_estimated",
                _build_creation_description(stats, parent_verified_absent=False),
                "low",
                "creation_without_parent_proof",
                True,
            )

        if stats["minus_def"] > 0 and stats["plus_def"] == 0:
            return (
                "function_deletion",
                _build_deletion_description(stats, message),
                "high",
                "definition_removed",
                True,
            )

        if stats["plus_def"] > 0 and stats["minus_def"] > 0:
            return (
                "signature_change",
                "함수 시그니처(원형)가 변경되었습니다.",
                "medium",
                "definition_replaced",
                True,
            )

        subtype = _refine_body_subtype(stats, message, diff)
        reason = (
            f"body_change:{subtype}"
            if evidence == EVIDENCE_DIRECT_BODY
            else f"function_context:{subtype}"
        )
        conf = "high" if evidence == EVIDENCE_DIRECT_BODY else "medium"
        return (
            subtype,
            _build_body_description(subtype, stats, message, symbol),
            conf,
            reason,
            True,
        )

    # SYMBOL_ONLY / unclear scope — never claim "Diff상 {기능} 판정 변경".
    if sym_touched == 0 or evidence == EVIDENCE_SYMBOL_ONLY:
        if (stats["plus_call"] or stats["minus_call"]) and not (
            stats["plus_def"] or stats["minus_def"]
        ):
            return (
                "call_site_change",
                "함수 호출부만 변경되었습니다 (함수 본문 정의 변경은 확인되지 않음).",
                "medium",
                "call_site_only",
                False,
            )
        promoted = _promote_symbol_only(message, diff, symbol, stats)
        if promoted:
            return promoted
        return (
            "related_candidate",
            "- 대상 함수명이 Diff에 포함되지만 함수 본문 변경 여부는 "
            "자동으로 확정하지 못했습니다.",
            "low",
            "symbol_in_diff_scope_unknown",
            False,
        )

    if _strict_creation_candidate(stats):
        if parent_has_function is True:
            subtype = _refine_body_subtype(stats, message, diff)
            return (
                subtype,
                _build_body_description(subtype, stats, message, symbol),
                "medium",
                "parent_already_has_function",
                True,
            )
        if parent_has_function is False:
            return (
                "function_creation",
                _build_creation_description(stats, parent_verified_absent=True),
                "high",
                "parent_missing_function_definition",
                True,
            )
        return (
            "function_creation_estimated",
            _build_creation_description(stats, parent_verified_absent=False),
            "low",
            "creation_without_parent_proof",
            True,
        )

    if stats["minus_def"] > 0 and stats["plus_def"] == 0:
        return (
            "function_deletion",
            _build_deletion_description(stats, message),
            "high" if stats["function_range_confirmed"] else "medium",
            "definition_removed",
            True,
        )

    if stats["plus_def"] > 0 and stats["minus_def"] > 0:
        return (
            "signature_change",
            "함수 시그니처(원형)가 변경되었습니다.",
            "medium",
            "definition_replaced",
            True,
        )

    sym_lines = stats["plus_sym"] + stats["minus_sym"]
    if sym_lines > 0 and (stats["plus_comment"] + stats["minus_comment"]) == sym_lines:
        return (
            "comment_or_log",
            _build_log_description(stats, message),
            "medium" if stats["function_range_confirmed"] else "low",
            "comment_or_log_only",
            False,
        )

    if (stats["plus_call"] or stats["minus_call"]) and not (
        stats["plus_def"] or stats["minus_def"]
    ):
        return (
            "call_site_change",
            "함수 호출부만 변경되었습니다 (함수 본문 정의 변경은 확인되지 않음).",
            "medium",
            "call_site_only",
            False,
        )

    subtype = _refine_body_subtype(stats, message, diff)
    conf = "high" if stats["function_range_confirmed"] else "medium"
    return (
        subtype,
        _build_body_description(subtype, stats, message, symbol),
        conf,
        f"body_change:{subtype}",
        True,
    )



def _promote_from_message_only(
    message: str | None, symbol: str
) -> tuple[str, str, str, str, bool] | None:
    if not message:
        return None
    topic = _detect_topic_blob(message)
    if topic:
        change_type, desc = topic
        return (
            change_type,
            f"- Commit 메시지상 {_CHANGE_TYPE_LABELS.get(change_type, change_type)}(으)로 확인됩니다.\n"
            "- 대상 함수의 세부 Diff는 확보하지 못했습니다.",
            "medium",
            "message_topic",
            False,  # v2.5: message-only never promotes to 주요 lifecycle
        )
    if _DEV_LOG_MSG_RE.search(message) or (
        _LOG_RE.search(message) and re.search(r"삭제|제거|정리|remove|clean", message, re.I)
    ):
        return (
            "comment_or_log",
            "- Commit 메시지상 테스트/개발 로그 정리입니다.\n"
            "- 카드 판정 로직 자체의 변경은 Commit 메시지 기준으로는 확인되지 않았습니다.",
            "medium",
            "message_log_cleanup",
            False,
        )
    if _DATE_HARDCODE_MSG_RE.search(message):
        return (
            "date_logic_change",
            "- Commit 메시지상 날짜 하드코딩 또는 날짜 비교 조건 제거입니다.\n"
            "- 대상 함수의 세부 Diff는 확보하지 못했습니다.",
            "medium",
            "message_date_hardcode",
            False,
        )
    if _CARD_TYPE_RE.search(message) and (
        symbol.lower() in message.lower() or "청소년" in message or "어린이" in message
    ):
        return (
            "card_type_setting",
            "- Commit 메시지상 카드 유형 판정 변경으로 확인됩니다.\n"
            "- 대상 함수의 세부 Diff는 확보하지 못했습니다.",
            "medium",
            "message_card_type",
            False,
        )
    return None


def _promote_symbol_only(
    message: str | None, diff: str | None, symbol: str, stats: dict
) -> tuple[str, str, str, str, bool] | None:
    """SYMBOL_ONLY / unclear-scope promote — never claim Diff상 기능 확정.

    PROJECT_SPEC v2.5.1 §1.7 — when body/hunk scope is not confirmed, topic
    keywords found elsewhere in the file Diff must not be worded as
    ``Diff상 {기능} 판정 변경``.
    """
    _ = (diff, stats)
    # Prefer Commit message topic when available.
    msg_promoted = _promote_from_message_only(message, symbol)
    if msg_promoted:
        return msg_promoted
    return (
        "related_candidate",
        "- 대상 함수명이 Diff에 포함되지만 함수 본문 변경 여부는 "
        "자동으로 확정하지 못했습니다.",
        "low",
        "symbol_only",
        False,
    )


def _promote_from_message_and_diff(
    message: str | None, diff: str | None, symbol: str, stats: dict
) -> tuple[str, str, str, str, bool] | None:
    """Deprecated alias — callers should use evidence-tier aware paths."""
    return _promote_symbol_only(message, diff, symbol, stats)


def _pick_code_sample(samples: list[str], symbol: str) -> str | None:
    """Prefer real body lines; skip bare function declarations used as context."""
    for sample in samples or []:
        text = (sample or "").strip()
        if not text:
            continue
        if _looks_like_definition(text, symbol):
            continue
        if text.endswith(";") and symbol in text and "(" in text and "{" not in text:
            # forward declaration / prototype context
            continue
        return text[:100]
    return None


def _build_creation_description(
    stats: dict, *, parent_verified_absent: bool = False
) -> str:
    """Diff/parent-verified facts only — no speculative call-site claims."""
    _ = stats
    if parent_verified_absent:
        parts = ["함수 원형과 구현이 새로 추가되었습니다."]
    else:
        parts = ["이 Commit에서 함수 원형과 구현이 최초로 확인되었습니다."]
    return "\n".join(f"- {p}" for p in parts)


def _build_deletion_description(stats: dict, message: str | None) -> str:
    _ = stats, message
    parts = ["함수 정의가 삭제되었습니다."]
    return "\n".join(f"- {p}" for p in parts)


def _build_log_description(stats: dict, message: str | None) -> str:
    parts = []
    if stats.get("deleted_samples") or (message and re.search(r"삭제|제거|정리", message)):
        parts.append("테스트용 로그 또는 주석 출력을 정리·삭제했습니다.")
    else:
        parts.append("로그 또는 주석 관련 라인이 변경되었습니다.")
    parts.append("카드 판정 로직 자체의 변경은 확인되지 않았습니다.")
    return "\n".join(f"- {p}" for p in parts)


def _build_body_description(
    subtype: str,
    stats: dict,
    message: str | None = None,
    symbol: str | None = None,
) -> str:
    """Diff-derived description only — never copy Commit message into this text.

    Commit message is rendered separately as ``- Commit 메시지:`` in Markdown.
    """
    _ = message
    templates = {
        "card_type_setting": "카드 사용자 유형(청소년·어린이·성인 등) 판정 또는 설정 조건 변경",
        "date_logic_change": "생년월일 비교 또는 적용일 조건 처리 로직 변경",
        "transfer_reboarding_change": "환승·재승차 판정 조건 변경",
        "institution_condition_change": "기관별 적용 조건 변경",
        "time_limit_condition_change": "시간 제한 조건 변경",
        "fare_penalty_condition_change": "요금·할인·패널티 처리 조건 변경",
        "climate_condition_change": "기후동행카드 관련 환승·패널티 조건 변경",
        "branch_change": "조건문/분기 처리 로직 변경",
        "return_handling_change": "반환값 또는 오류 처리 로직 변경",
        "body_change": "함수 내부 구현 변경",
    }
    parts: list[str] = [templates.get(subtype, templates["body_change"])]
    sym = symbol or ""
    added = _pick_code_sample(stats.get("added_samples") or [], sym)
    deleted = _pick_code_sample(stats.get("deleted_samples") or [], sym)
    if added:
        parts.append(f"추가된 코드 예: `{added}`")
    if deleted:
        parts.append(f"삭제된 코드 예: `{deleted}`")
    return "\n".join(f"- {p}" for p in parts)


def classify_symbol_diff(diff: str | None, symbol: str) -> tuple[str, str, int]:
    """Backward-compatible wrapper used in unit tests."""
    change_type, desc, conf, _reason, is_core = analyze_function_commit(
        diff=diff,
        symbol=symbol,
        message=None,
        parent_has_function=None,
        diff_available=diff is not None,
    )
    priority = _CHANGE_TYPE_PRIORITY.get(change_type, 10)
    return change_type, desc.replace("\n", " / ")[:320], priority


def fetch_symbol_git_rows(
    equipment_id: int,
    symbol: str,
    *,
    file_path: str | None = None,
    limit: int = _FUNC_HISTORY_FETCH_LIMIT,
) -> list[dict]:
    if not symbol or equipment_id is None:
        return []
    like = f"%{symbol}%"
    basename = _basename(file_path)
    conn = get_connection()
    try:
        if basename:
            rows = conn.execute(
                """
                SELECT
                    gr.id AS repository_id,
                    gr.name AS repository_name,
                    gc.id AS commit_id,
                    gc.commit_hash,
                    gc.commit_date,
                    gc.message,
                    gch.id AS git_change_id,
                    gch.file_path,
                    gch.diff
                FROM git_commit gc
                JOIN git_repository gr ON gr.id = gc.repository_id
                JOIN git_change gch ON gch.commit_id = gc.id
                WHERE gr.equipment_id = ?
                  AND gch.diff LIKE ?
                  AND (gch.file_path = ? OR gch.file_path LIKE ?)
                ORDER BY gc.commit_date ASC
                LIMIT ?
                """,
                (equipment_id, like, basename, f"%/{basename}", limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    gr.id AS repository_id,
                    gr.name AS repository_name,
                    gc.id AS commit_id,
                    gc.commit_hash,
                    gc.commit_date,
                    gc.message,
                    gch.id AS git_change_id,
                    gch.file_path,
                    gch.diff
                FROM git_commit gc
                JOIN git_repository gr ON gr.id = gc.repository_id
                JOIN git_change gch ON gch.commit_id = gc.id
                WHERE gr.equipment_id = ?
                  AND gch.diff LIKE ?
                ORDER BY gc.commit_date ASC
                LIMIT ?
                """,
                (equipment_id, like, limit),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _row_to_candidate(row: dict) -> GitCandidate:
    return GitCandidate.model_construct(
        repository_id=row["repository_id"],
        repository_name=row.get("repository_name") or "",
        commit_id=row["commit_id"],
        commit_hash=row["commit_hash"],
        commit_date=row.get("commit_date") or "",
        message=row.get("message") or "",
        file_path=row["file_path"],
        score=1,
        match_reasons=["diff_symbol"],
        query_match_reasons=[],
        query_relevance_score=0,
        query_relevance_level="없음",
    )


def _ppt_links_exact(links: list[EvidenceLink]) -> dict[str, EvidenceLink]:
    """Exact full commit_hash only — never alias by short prefix."""
    out: dict[str, EvidenceLink] = {}
    for link in links or []:
        h = getattr(link.git_candidate, "commit_hash", None)
        if h:
            out[h] = link
    return out


def _token_overlap(a: str, b: str) -> float:
    ta = {t for t in re.split(r"[^\w가-힣]+", a.lower()) if len(t) >= 2}
    tb = {t for t in re.split(r"[^\w가-힣]+", b.lower()) if len(t) >= 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _apply_ppt_link_to_entry(entry: FunctionGitHistoryEntry, link: PptLink | None) -> None:
    entry.ppt_link = link
    entry.ppt_links = [link] if link else []
    if link is None:
        entry.ppt_title = None
        entry.ppt_file = None
        entry.ppt_slide = None
        entry.ppt_link_level = "none"
        entry.ppt_link_reason = None
        return
    entry.ppt_title = link.change_title
    entry.ppt_file = link.document_name
    entry.ppt_slide = link.slide_number
    entry.ppt_link_level = _ppt_level_from_link(link)
    entry.ppt_link_reason = link.link_reason_user


def _collect_candidate_pool(
    evidence_result: EvidenceResult,
    symbol: str,
    *,
    file_path: str | None,
) -> list[GitCandidate]:
    pool: dict[tuple[int, str], GitCandidate] = {}

    def _add(git: GitCandidate) -> None:
        key = (int(git.commit_id), str(git.file_path))
        pool.setdefault(key, git)

    for git in evidence_result.git_candidates or []:
        _add(git)
    for link in evidence_result.evidence_links or []:
        _add(link.git_candidate)
    try:
        for row in fetch_symbol_git_rows(
            evidence_result.equipment_id, symbol, file_path=file_path
        ):
            _add(_row_to_candidate(row))
    except Exception:
        pass
    return list(pool.values())


def _apply_commit_analysis_to_entry(
    entry: FunctionGitHistoryEntry,
    *,
    diff: str | None,
    symbol: str,
    message: str | None,
    parent_has_function: bool | None,
    diff_source: str,
    feature_docs: list,
    record: dict | None,
    creation_date: str | None = None,
    debug_extra: dict | None = None,
) -> None:
    """Populate or refresh all user-facing fields from commit diff analysis."""
    diff_available = diff_source in {"exact_git_change", "path_alias_git_change", "live_git_show"} and bool(
        diff
    )
    change_type, description, confidence, reason, is_core = analyze_function_commit(
        diff=diff,
        symbol=symbol,
        message=message,
        parent_has_function=parent_has_function,
        diff_available=diff_available,
    )
    stats = _parse_diff_stats(diff, symbol) if diff else {}
    diff_state = reason if change_type in {"related_candidate", "diff_unavailable"} else None

    ppt = build_ppt_link_for_entry(
        commit_hash=entry.commit_hash,
        commit_date=entry.commit_date,
        message=message,
        change_type=change_type,
        file_path=entry.file_path,
        symbol=symbol,
        feature_docs=feature_docs,
        creation_date=creation_date,
        function_range_confirmed=bool(stats.get("function_range_confirmed")),
        diff_available=diff_available,
    )

    entry.change_type = change_type
    entry.change_type_label = _CHANGE_TYPE_LABELS.get(change_type, change_type)
    entry.change_description = description
    entry.confidence = confidence
    entry.confidence_label = _confidence_label(confidence)
    entry.is_core = is_core
    entry.section = _assign_section(change_type, is_core)
    entry.diff_state = diff_state
    entry.confirmation_note = (
        _user_limitation_note(reason, diff_state) if entry.section == "unconfirmed" else None
    )
    _apply_ppt_link_to_entry(entry, ppt)
    entry.priority = _CHANGE_TYPE_PRIORITY.get(change_type, 10)

    git_change_ids = [record["id"]] if record and record.get("id") else []
    item_debug = {
        "lifecycle_commit_hash": entry.commit_hash,
        "lifecycle_file_path": entry.file_path,
        "git_change_ids": git_change_ids,
        "diff_source": diff_source,
        "diff_text": diff,
        "added_line_count": stats.get("added_line_count", 0),
        "deleted_line_count": stats.get("deleted_line_count", 0),
        "symbol_definition_found": stats.get("symbol_definition_found", False),
        "function_range_confirmed": stats.get("function_range_confirmed", False),
        "evidence_tier": stats.get("evidence_tier"),
        "hunk_header_scoped": stats.get("hunk_header_scoped", False),
        "classification": change_type,
        "classification_reason": reason,
        "diff_state": diff_state,
        "parent_has_function": parent_has_function,
        "ppt_link_type": ppt.link_type if ppt else None,
        "ppt_change_action": ppt.change_action if ppt else None,
        "ppt_phase": ppt.phase if ppt else None,
    }
    if debug_extra:
        item_debug.update(debug_extra)
    entry.debug_item = item_debug


def _enforce_single_creation(
    entries: list[FunctionGitHistoryEntry],
    symbol: str,
    feature_docs: list,
) -> None:
    creations = [
        e
        for e in entries
        if e.change_type in {"function_creation", "function_creation_estimated"}
    ]
    if len(creations) <= 1:
        return
    verified = [e for e in creations if e.change_type == "function_creation"]
    pick = min(
        verified or creations,
        key=lambda e: (e.commit_date or "", e.commit_hash),
    )
    for entry in entries:
        if entry is pick:
            continue
        if entry.change_type not in {"function_creation", "function_creation_estimated"}:
            continue
        prior_type = entry.change_type
        diff = entry.debug_item.get("diff_text")
        _apply_commit_analysis_to_entry(
            entry,
            diff=diff,
            symbol=symbol,
            message=entry.message,
            parent_has_function=True,
            diff_source=entry.debug_item.get("diff_source", "unavailable"),
            feature_docs=feature_docs,
            record=None,
            debug_extra={
                "reclassified_from": prior_type,
                "reclassification_reason": "earlier_creation_exists",
            },
        )


def _overall_confidence(
    core_entries: list[FunctionGitHistoryEntry],
    other_entries: list[FunctionGitHistoryEntry],
    unconfirmed: list[FunctionGitHistoryEntry],
    maintenance: list[FunctionGitHistoryEntry] | None = None,
) -> tuple[str, str]:
    confirmed = core_entries + other_entries + (maintenance or [])
    if not confirmed and unconfirmed:
        return "low", "낮음"
    if not confirmed:
        return "low", "낮음"
    levels = [e.confidence for e in confirmed]
    high_n = sum(1 for l in levels if l == "high")
    low_n = sum(1 for l in levels if l == "low")
    if unconfirmed and len(unconfirmed) > len(confirmed):
        return "low", "낮음"
    if low_n > len(confirmed) // 2:
        return "low", "낮음"
    if high_n >= max(1, len(confirmed) // 2) and low_n == 0 and not unconfirmed:
        return "high", "높음"
    return "medium", "보통"


def _lifecycle_counts(
    entries: list[FunctionGitHistoryEntry],
    *,
    total_candidates: int,
    excluded: list[dict],
) -> dict:
    core = [e for e in entries if e.section == "core"]
    other = [e for e in entries if e.section == "other"]
    maintenance = [e for e in entries if e.section == "maintenance"]
    unconfirmed = [e for e in entries if e.section == "unconfirmed"]
    creation = next(
        (
            e
            for e in core
            if e.change_type in {"function_creation", "function_creation_estimated"}
        ),
        None,
    )
    creation_count = 1 if creation else 0
    core_followup = len(core) - creation_count
    all_links = [e.ppt_link for e in entries if e.ppt_link]
    official = unique_official_docs(all_links)
    return {
        "total_candidates": total_candidates,
        "direct_confirmed_count": len(core) + len(other) + len(maintenance),
        "creation_count": creation_count,
        "core_followup_count": max(0, core_followup),
        "other_count": len(other),
        "maintenance_count": len(maintenance),
        "unconfirmed_count": len(unconfirmed),
        "excluded_count": len(excluded),
        "ppt_direct_count": sum(
            1 for e in entries if e.ppt_link and e.ppt_link.link_type == LINK_COMMIT_DIRECT
        ),
        # Per-commit link counts (debug only; glance uses unique doc counts).
        "ppt_feature_release_link_count": sum(
            1 for e in entries if e.ppt_link and e.ppt_link.link_type == LINK_FEATURE_RELEASE
        ),
        "ppt_feature_release_count": sum(
            1 for d in official if d.link_type == LINK_FEATURE_RELEASE
        ),
        "ppt_dev_reference_count": sum(
            1 for e in entries if e.ppt_link and e.ppt_link.link_type == LINK_DEV_REFERENCE
        ),
        "ppt_maintenance_count": sum(
            1 for d in official if d.link_type == LINK_MAINTENANCE
        ),
        "ppt_indirect_count": sum(1 for e in entries if e.ppt_link_level == "indirect"),
        "ppt_official_doc_count": len(official),
        "git_only_count": sum(1 for e in entries if e.ppt_link_level == "none"),
    }


def _entry_heading(entry: FunctionGitHistoryEntry) -> str:
    """User-facing heading — never default to '확인 필요' for explainable commits."""
    if entry.change_type == "comment_or_log":
        return "테스트 로그 정리"
    if entry.change_type == "card_type_setting":
        return "카드 유형 판정 조건 변경"
    if entry.change_type == "date_logic_change":
        return "날짜 비교/하드코딩 제거"
    if entry.change_type in {"function_creation", "function_creation_estimated"}:
        return "함수 최초 추가"
    if entry.section == "unconfirmed":
        if entry.message and _DEV_LOG_MSG_RE.search(entry.message):
            return "테스트 로그 정리"
        if entry.message and _CARD_TYPE_RE.search(entry.message):
            return "카드 유형 관련 변경 후보"
        return "관련 코드 변경 후보"
    return entry.change_type_label


def _render_ppt_fields(
    entry: FunctionGitHistoryEntry,
    *,
    stage_docs: list[PptLink] | None = None,
) -> list[str]:
    lines: list[str] = []
    link = entry.ppt_link
    if link is not None and link.link_type == LINK_COMMIT_DIRECT:
        slide = f", Slide {link.slide_number}" if link.slide_number is not None else ""
        doc = link.document_name or link.change_title or "(문서명 없음)"
        lines.append(f"- 변경내역서: {doc}{slide}")
        lines.append(f"- 연결 유형: {link.link_type_label}")
        if link.link_reason_user:
            lines.append(f"- 연결 근거: {link.link_reason_user}")
        return lines

    # Non-commit-direct: never imply Diff-backed commit document proof.
    stage_match = None
    if link is not None and link.link_type in {
        LINK_FEATURE_RELEASE,
        LINK_MAINTENANCE,
    }:
        stage_match = link
    elif stage_docs and entry.section in {"core", "other", "unconfirmed", "maintenance"}:
        for doc in stage_docs:
            if doc.phase == "development" and doc.change_action != "delete":
                stage_match = doc
                break
        if stage_match is None and stage_docs:
            stage_match = stage_docs[0]

    if stage_match is not None:
        slide = (
            f", Slide {stage_match.slide_number}"
            if stage_match.slide_number is not None
            else ""
        )
        doc = stage_match.change_title or stage_match.document_name or "(문서명 없음)"
        lines.append("- Commit 직접 연결 문서: 찾지 못함")
        lines.append(
            f"- 해당 기능 단계 공식 문서: {doc}{slide} ({stage_match.link_type_label})"
        )
        if link is not None and link.link_type == LINK_DEV_REFERENCE and link.link_reason_user:
            lines.append(f"- 참고: {link.link_reason_user}")
        return lines

    if link is not None:
        # Weak related / development_reference without stage official.
        slide = f", Slide {link.slide_number}" if link.slide_number is not None else ""
        doc = link.document_name or link.change_title or "(문서명 없음)"
        lines.append("- Commit 직접 연결 문서: 찾지 못함")
        lines.append(f"- 참고 변경내역서: {doc}{slide} ({link.link_type_label})")
        if link.link_type == LINK_DEV_REFERENCE:
            lines.append("- 참고: 기능 동작 변경의 직접 사유 문서로 사용하지 않습니다.")
        return lines

    lines.append("- 현재 검색 기준에서 관련 변경내역서를 찾지 못했습니다.")
    return lines


def _render_document(
    symbol: str,
    entries: list[FunctionGitHistoryEntry],
    overall_label: str,
    counts: dict,
) -> str:
    from app.services.lifecycle_markdown import render_lifecycle_markdown

    return render_lifecycle_markdown(
        symbol,
        entries,
        overall_label,
        counts,
        entry_heading=_entry_heading,
        user_limitation_note=_user_limitation_note,
        build_narrative=_build_narrative,
    )


def _build_narrative(
    symbol: str,
    creation: FunctionGitHistoryEntry | None,
    core: list[FunctionGitHistoryEntry],
    other: list[FunctionGitHistoryEntry],
    maintenance: list[FunctionGitHistoryEntry],
    primary_docs: list[PptLink],
    maint_docs: list[PptLink],
    counts: dict,
) -> str:
    parts: list[str] = []
    if creation:
        parts.append(
            f"이 함수는 `{_short_hash(creation.commit_hash)}`"
            f"({creation.commit_date or '날짜 미확인'})에서 최초 추가되었습니다."
        )
    follow = counts.get("core_followup_count", 0)
    if follow:
        parts.append(f"이후 핵심 기능 변경 {follow}건이 확인되었습니다.")
    if other:
        parts.append(
            f"개발 과정에서 테스트 로그 정리 등 보조 변경 {len(other)}건이 있었습니다."
        )
    if maintenance:
        parts.append(f"후속 Git 유지보수 변경 {len(maintenance)}건이 확인되었습니다.")
    # primary_docs holds the unique related-official collection (maint_docs unused).
    related_docs = list(primary_docs) + [
        d for d in maint_docs if d not in primary_docs
    ]
    if related_docs:
        parts.append(f"관련 공식 문서 {len(related_docs)}건이 확인되었습니다.")
    if not parts:
        parts.append(
            f"함수 `{symbol}`와 관련된 Git 변경 "
            f"{counts.get('direct_confirmed_count', 0)}건이 확인되었습니다."
        )
    return " ".join(parts)


def _render_official_doc_block(
    idx: int,
    doc: PptLink,
    entries: list[FunctionGitHistoryEntry],
    *,
    heading_prefix: str = "공식 변경내역서",
) -> list[str]:
    title = doc.change_title or heading_prefix
    lines = [f"#### {idx}. {heading_prefix} — {title}", ""]
    if doc.document_name:
        lines.append(f"- 문서: {doc.document_name}")
    if doc.document_date:
        lines.append(f"- 작성일: {doc.document_date}")
    if doc.versions:
        lines.append(f"- 적용 버전: {' / '.join(doc.versions)}")
    if doc.slide_number is not None:
        lines.append(f"- Slide: {doc.slide_number}")
    if doc.csr_no:
        lines.append(f"- 관련 CSR: {doc.csr_no}")
    if doc.business_background:
        lines.append(f"- 업무 배경: {doc.business_background[:240]}")
    if doc.to_be:
        lines.append(f"- 주요 To-Be: {doc.to_be[:280]}")
    if doc.as_is:
        lines.append(f"- As-Is: {doc.as_is[:200]}")
    if doc.related_source_paths:
        lines.append("- 관련 소스:")
        paths = list(doc.related_source_paths)
        for p in paths[:6]:
            lines.append(f"  - {p}")
        omitted = max(0, len(paths) - 6)
        if omitted:
            lines.append(f"  - 외 {omitted}개")
    if doc.related_symbols:
        lines.append("- 관련 함수:")
        symbols = list(doc.related_symbols)
        for s in symbols[:8]:
            lines.append(f"  - {s}()")
        omitted = max(0, len(symbols) - 8)
        if omitted:
            lines.append(f"  - 외 {omitted}개")
    linked = [
        e
        for e in entries
        if e.ppt_link and e.ppt_link.identity_key() == doc.identity_key()
    ]
    # Also attach same-stage core commits that lack a stronger opposing PPT link.
    if doc.link_type == LINK_FEATURE_RELEASE:
        for e in entries:
            if e.section != "core":
                continue
            if any(x.commit_hash == e.commit_hash for x in linked):
                continue
            if e.ppt_link is None or e.ppt_link.link_type == LINK_DEV_REFERENCE:
                linked.append(e)
            elif e.ppt_link.identity_key() == doc.identity_key():
                linked.append(e)
    if linked:
        # Prefer feature/release first, then log refs last in display.
        core_first = [e for e in linked if e.section == "core"]
        other_linked = [e for e in linked if e.section != "core"]
        ordered = core_first + other_linked
        hashes = ", ".join(f"`{_short_hash(e.commit_hash)}`" for e in ordered[:8])
        lines.append(f"- 관련 Git 변경: {hashes}")
        log_only = [e for e in ordered if e.change_type == "comment_or_log"]
        if log_only and core_first:
            lines.append(
                "- 참고: 로그 정리 commit은 개발 과정 참고이며 기능 배포의 직접 근거가 아닙니다."
            )
    else:
        lines.append("- 관련 Git 변경: 확정된 단일 commit은 없습니다.")
    lines.append(f"- 연결 유형: {doc.link_type_label}")
    lines.append("")
    return lines


def _render_entry_block(
    idx: int,
    entry: FunctionGitHistoryEntry,
    *,
    detailed: bool,
    stage_docs: list[PptLink] | None = None,
) -> list[str]:
    lines = [f"### {idx}. {_entry_heading(entry)}", ""]
    lines.append(f"- 날짜: {entry.commit_date or '확인되지 않음'}")
    lines.append(f"- Commit: `{_short_hash(entry.commit_hash)}`")
    if entry.message:
        lines.append(f"- Commit 메시지: {entry.message[:240]}")
    lines.append(f"- 변경 성격: {entry.change_type_label}")
    lines.append("- 변경 내용:")
    for part in entry.change_description.split("\n"):
        part = part.strip()
        if not part:
            continue
        lines.append(f"  {part}" if part.startswith("-") else f"  - {part}")
    if detailed and entry.impact:
        lines.append(f"- 영향: {entry.impact}")
    lines.extend(_render_ppt_fields(entry, stage_docs=stage_docs))
    lines.append(f"- 신뢰도: {entry.confidence_label}")
    lines.append("")
    return lines


def _render_related_block(idx: int, entry: FunctionGitHistoryEntry) -> list[str]:
    note = entry.confirmation_note or _user_limitation_note(
        entry.debug_item.get("classification_reason"),
        entry.diff_state,
    )
    lines = [f"### {idx}. {_entry_heading(entry)}", ""]
    lines.append(f"- 날짜: {entry.commit_date or '확인되지 않음'}")
    lines.append(f"- Commit: `{_short_hash(entry.commit_hash)}`")
    if entry.message:
        lines.append(f"- Commit 메시지: {entry.message[:240]}")
    lines.append("- 변경 내용:")
    for part in entry.change_description.split("\n"):
        part = part.strip()
        if not part or "확인 상태" in part:
            continue
        lines.append(f"  {part}" if part.startswith("-") else f"  - {part}")
    lines.extend(_render_ppt_fields(entry))
    lines.append(f"- 직접 함수 범위 확인: 일부 제한 — {note}")
    lines.append(f"- 신뢰도: {entry.confidence_label}")
    lines.append("")
    return lines


def _render_unconfirmed_block(idx: int, entry: FunctionGitHistoryEntry) -> list[str]:
    """Backward-compatible alias used by older tests."""
    return _render_related_block(idx, entry)


def resolve_function_git_lifecycle(
    evidence_result: EvidenceResult,
    primary_symbol: str,
    *,
    file_path: str | None = None,
) -> FunctionGitLifecycleResult:
    result = FunctionGitLifecycleResult()
    debug: dict = {
        "function_git_candidates": 0,
        "function_direct_diff_matches": 0,
        "function_creation_commits": 0,
        "function_body_change_commits": 0,
        "ppt_linked_commits": 0,
        "git_only_commits": 0,
        "final_history_count": 0,
        "excluded_commits": [],
        "lifecycle_items_debug": [],
    }
    result.debug = debug

    if not primary_symbol:
        return result

    scope_path = file_path
    if not scope_path and evidence_result.request_files:
        scope_path = evidence_result.request_files[0]
    if not scope_path and evidence_result.path_scopes:
        scope_path = evidence_result.path_scopes[0]

    candidates = _collect_candidate_pool(evidence_result, primary_symbol, file_path=scope_path)
    debug["function_git_candidates"] = len(candidates)
    feature_docs = collect_feature_documents(
        evidence_result, primary_symbol, file_path=scope_path
    )
    debug["feature_document_count"] = len(feature_docs)

    entries: list[FunctionGitHistoryEntry] = []
    excluded: list[dict] = []

    for git in candidates:
        record, diff_source = resolve_git_change_record(
            git.commit_id,
            git.file_path,
            scope_path=scope_path,
        )
        diff = record.get("diff") if record else None

        parent_has_fn = ancestor_file_has_function_definition(
            git.commit_id, git.file_path, primary_symbol
        )

        # Pre-analyze for merge exclusion before building entry.
        diff_available = diff_source in {
            "exact_git_change",
            "path_alias_git_change",
            "live_git_show",
        } and bool(diff)
        pre_type, _, _, pre_reason, pre_core = analyze_function_commit(
            diff=diff,
            symbol=primary_symbol,
            message=git.message,
            parent_has_function=parent_has_fn,
            diff_available=diff_available,
        )
        pre_stats = _parse_diff_stats(diff, primary_symbol) if diff else {}

        if _is_merge_commit(git.message) and not _merge_has_function_change(
            pre_stats, pre_type, pre_core
        ):
            excluded.append(
                {
                    "commit_hash": git.commit_hash,
                    "reason": "merge_no_function_change",
                }
            )
            continue

        entry = FunctionGitHistoryEntry(
            commit_id=git.commit_id,
            commit_hash=git.commit_hash,
            commit_date=git.commit_date or None,
            message=git.message or None,
            file_path=git.file_path,
            change_type="related_candidate",
            change_type_label="",
            change_description="",
            impact=None,
            confidence="low",
            confidence_label="낮음",
            is_core=False,
        )
        _apply_commit_analysis_to_entry(
            entry,
            diff=diff,
            symbol=primary_symbol,
            message=git.message,
            parent_has_function=parent_has_fn,
            diff_source=diff_source,
            feature_docs=feature_docs,
            record=record,
        )

        exclude_key = _lifecycle_exclusion_reason(
            change_type=entry.change_type,
            reason=(entry.debug_item or {}).get("classification_reason") or pre_reason,
            stats=pre_stats,
        )
        if exclude_key:
            excluded.append({"commit_hash": git.commit_hash, "reason": exclude_key})
            continue

        if _is_merge_commit(git.message) and entry.section == "unconfirmed":
            entry.change_type_label = "Merge 관련 변경"
            entry.confirmation_note = (
                "Merge 커밋으로 수집되었으나 대상 함수의 직접 변경을 자동 확정하지 못했습니다."
            )

        debug["lifecycle_items_debug"].append(entry.debug_item)
        if diff and _symbol_in_diff(diff, primary_symbol):
            debug["function_direct_diff_matches"] += 1

        entries.append(entry)

        if entry.change_type in {"function_creation", "function_creation_estimated"}:
            debug["function_creation_commits"] += 1
        if entry.section == "core" and entry.change_type not in {
            "function_creation",
            "function_creation_estimated",
        }:
            debug["function_body_change_commits"] += 1
        if entry.ppt_link_level == "direct":
            debug["ppt_linked_commits"] += 1
        else:
            debug["git_only_commits"] += 1

    entries.sort(key=lambda e: (e.commit_date or "", e.commit_hash))
    _enforce_single_creation(entries, primary_symbol, feature_docs)

    creation = next(
        (
            e
            for e in entries
            if e.change_type in {"function_creation", "function_creation_estimated"}
        ),
        None,
    )
    creation_date = creation.commit_date if creation else (
        entries[0].commit_date if entries else None
    )

    # Re-link PPT with creation_date so maintenance docs cannot monopolize intro commits.
    for entry in entries:
        stats = entry.debug_item or {}
        ppt = build_ppt_link_for_entry(
            commit_hash=entry.commit_hash,
            commit_date=entry.commit_date,
            message=entry.message,
            change_type=entry.change_type,
            file_path=entry.file_path,
            symbol=primary_symbol,
            feature_docs=feature_docs,
            creation_date=creation_date,
            function_range_confirmed=bool(stats.get("function_range_confirmed")),
            diff_available=stats.get("diff_source")
            in {"exact_git_change", "path_alias_git_change", "live_git_show"}
            and bool(stats.get("diff_text")),
        )
        _apply_ppt_link_to_entry(entry, ppt)
        entry.debug_item["ppt_link_type"] = ppt.link_type if ppt else None
        entry.debug_item["ppt_change_action"] = ppt.change_action if ppt else None
        entry.debug_item["ppt_phase"] = ppt.phase if ppt else None

    # Refresh ppt counters after re-link.
    debug["ppt_linked_commits"] = sum(
        1 for e in entries if e.ppt_link_level == "direct"
    )
    debug["git_only_commits"] = sum(1 for e in entries if e.ppt_link_level == "none")

    result.entries = entries
    result.creation = creation
    result.excluded = excluded
    debug["excluded_commits"] = excluded
    debug["final_history_count"] = len(entries)

    core_entries = [e for e in entries if e.section == "core"]
    other_entries = [e for e in entries if e.section == "other"]
    maintenance_entries = [e for e in entries if e.section == "maintenance"]
    unconfirmed_entries = [e for e in entries if e.section == "unconfirmed"]

    overall, overall_label = _overall_confidence(
        core_entries, other_entries, unconfirmed_entries, maintenance_entries
    )
    result.overall_confidence = overall
    result.overall_confidence_label = overall_label

    counts = _lifecycle_counts(
        entries,
        total_candidates=len(candidates),
        excluded=excluded,
    )
    creation_date = None
    for e in entries:
        if e.change_type in {"function_creation", "function_creation_estimated"}:
            creation_date = e.commit_date
            break
    stage_docs = collect_stage_official_docs(
        feature_docs,
        symbol=primary_symbol,
        creation_date=creation_date,
        request_equipment_id=getattr(evidence_result, "equipment_id", None),
        request_equipment_name=getattr(evidence_result, "equipment_name", None),
        file_path=entries[0].file_path if entries else None,
    )
    all_links = [e.ppt_link for e in entries if e.ppt_link]
    official = merge_official_doc_collections(
        all_links,
        stage_docs,
        request_equipment_id=getattr(evidence_result, "equipment_id", None),
        request_equipment_name=getattr(evidence_result, "equipment_name", None),
    )
    counts["ppt_official_doc_count"] = len(official)
    # Unique-document connection-strength counts (Output / glance alignment).
    strength_n = {
        STRENGTH_COMMIT_DIRECT: 0,
        STRENGTH_STAGE: 0,
        STRENGTH_RELATED: 0,
    }
    for doc in official:
        # Prefer strongest type among entry links sharing this identity.
        types = [doc.link_type]
        for e in entries:
            if e.ppt_link and e.ppt_link.identity_key() == doc.identity_key():
                types.append(e.ppt_link.link_type)
        best = doc.link_type
        best_rank = -1
        rank = {
            LINK_COMMIT_DIRECT: 3,
            LINK_FEATURE_RELEASE: 2,
            LINK_MAINTENANCE: 1,
            LINK_RELATED: 1,
            LINK_DEV_REFERENCE: 1,
        }
        for lt in types:
            r = rank.get(lt, 0)
            if r > best_rank:
                best = lt
                best_rank = r
        strength_n[connection_strength(best)] = (
            strength_n.get(connection_strength(best), 0) + 1
        )
    counts["ppt_commit_direct_doc_count"] = strength_n[STRENGTH_COMMIT_DIRECT]
    counts["ppt_stage_link_doc_count"] = strength_n[STRENGTH_STAGE]
    counts["ppt_related_ref_doc_count"] = strength_n[STRENGTH_RELATED]
    # Legacy keys kept for older clients; map to strength buckets.
    counts["ppt_feature_release_doc_count"] = strength_n[STRENGTH_STAGE]
    counts["ppt_maintenance_doc_count"] = strength_n[STRENGTH_RELATED]
    counts["ppt_feature_release_count"] = counts["ppt_feature_release_doc_count"]
    counts["ppt_maintenance_count"] = counts["ppt_maintenance_doc_count"]
    counts["_stage_official_docs"] = stage_docs
    counts["_request_equipment_id"] = getattr(evidence_result, "equipment_id", None)
    counts["_request_equipment_name"] = getattr(evidence_result, "equipment_name", None)
    counts["_query_file_path"] = scope_path
    counts["overall_confidence"] = overall_label
    result.document_text = _render_document(
        primary_symbol, entries, overall_label, counts
    )
    # User-facing aggregates (set inside render_lifecycle_markdown).
    debug["lifecycle_summary"] = {
        k: v for k, v in counts.items() if not str(k).startswith("_")
    }
    debug["lifecycle_summary"]["ppt_official_doc_count"] = len(official)
    debug["lifecycle_summary"]["related_document_count"] = counts.get(
        "related_document_count", len(official)
    )
    debug["lifecycle_summary"]["displayed_git_count"] = counts.get(
        "displayed_git_count",
        counts.get("direct_confirmed_count", 0) + counts.get("unconfirmed_count", 0),
    )
    debug["lifecycle_summary"]["subsequent_change_count"] = counts.get(
        "subsequent_change_count"
    )
    # Keep internal strength counts for debug / Evidence Link diagnostics only.
    debug["lifecycle_summary"]["ppt_commit_direct_doc_count"] = strength_n[
        STRENGTH_COMMIT_DIRECT
    ]
    debug["lifecycle_summary"]["ppt_stage_link_doc_count"] = strength_n[STRENGTH_STAGE]
    debug["lifecycle_summary"]["ppt_related_ref_doc_count"] = strength_n[
        STRENGTH_RELATED
    ]

    result.lines = result.document_text.splitlines()
    result.summary_lines = [
        ln for ln in result.lines if ln.startswith("- ") and "한눈에" not in ln
    ][:6]

    citations: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        h = _short_hash(entry.commit_hash)
        if h not in seen:
            seen.add(h)
            citations.append(f"- Commit: {h} ({entry.change_type_label})")
    for doc in official:
        name = doc.document_name or doc.change_title
        if not name:
            continue
        pk = doc.identity_key()
        if pk in seen:
            continue
        seen.add(pk)
        slide = f", Slide {doc.slide_number}" if doc.slide_number is not None else ""
        citations.append(
            f"- 변경내역서: {name}{slide} ({doc.link_type_label})"
        )
    result.citation_lines = citations
    return result
