"""User-facing Markdown formatter for function Git lifecycle results.

Git lifecycle and related official documents are separate axes (§11–§12).
Analysis / Evidence Link / equipment / symbol logic is unchanged — this module
only reshapes already-computed entries and PPT links into a readable document.
"""

from __future__ import annotations

import html
import re
from typing import Any

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
    connection_strength,
    connection_strength_label,
    merge_official_doc_collections,
)

_USE_DETAILS = True

_TO_BE_SPLIT_RE = re.compile(r"(?<=[.。;；])\s+|\n+")
_PIPE_RE = re.compile(r"\|")
_CREATION_TYPES = frozenset({"function_creation", "function_creation_estimated"})

# Display-only caps (Evidence Link / PptLink keep full lists).
_RELATED_SOURCES_DISPLAY_LIMIT = 6
_RELATED_SYMBOLS_DISPLAY_LIMIT = 8


def _prioritize_for_display(
    items: list[str],
    *,
    preferred: str | None,
    limit: int,
    match_fn=None,
) -> tuple[list[str], int]:
    """Pin preferred item first for display; return (shown, omitted_count)."""
    if not items:
        return [], 0

    def _key(x: str) -> str:
        return (x or "").strip().lower()

    preferred_norm = (preferred or "").strip()
    ordered: list[str] = []
    seen: set[str] = set()

    if preferred_norm:
        for item in items:
            hit = (
                bool(match_fn(preferred_norm, item))
                if match_fn is not None
                else _key(item) == _key(preferred_norm)
                or preferred_norm.lower() in _key(item)
            )
            if hit and _key(item) not in seen:
                ordered.append(item)
                seen.add(_key(item))
                break
    for item in items:
        k = _key(item)
        if k in seen:
            continue
        ordered.append(item)
        seen.add(k)

    shown = ordered[: max(0, limit)]
    omitted = max(0, len(ordered) - len(shown))
    return shown, omitted


def _symbols_match_display(preferred: str, item: str) -> bool:
    from app.services.symbol_utils import symbols_equivalent

    return symbols_equivalent(preferred, item) or preferred.lower() == (item or "").lower()


def _path_match_display(preferred: str, item: str) -> bool:
    a = preferred.replace("\\", "/").lower().lstrip("./")
    b = (item or "").replace("\\", "/").lower().lstrip("./")
    if not a or not b:
        return False
    return (
        a == b
        or a.endswith("/" + b)
        or b.endswith("/" + a)
        or a.split("/")[-1] == b.split("/")[-1]
    )


def md_escape_cell(value: str | None) -> str:
    """Escape table-cell content (pipes / newlines)."""
    if not value:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = " ".join(text.split())
    return _PIPE_RE.sub("\\|", text)


def md_escape_html(value: str | None) -> str:
    if not value:
        return ""
    return html.escape(str(value), quote=True)


def format_date_display(value: str | None) -> str:
    if not value:
        return "확인되지 않음"
    text = str(value).strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return text


def short_hash(commit: str | None) -> str:
    """Display short hash — always 8 hex chars when possible (PROJECT_SPEC v2.6)."""
    if not commit:
        return "(hash 없음)"
    text = str(commit).strip()
    if len(text) >= 8:
        return text[:8]
    return text


def split_to_be_bullets(text: str | None, *, limit: int = 12) -> list[str]:
    """Split To-Be on punctuation / newlines without inventing content."""
    if not text:
        return []
    raw = str(text).strip()
    if not raw:
        return []
    parts = [p.strip(" .-•·\t") for p in _TO_BE_SPLIT_RE.split(raw) if p and p.strip()]
    parts = [p for p in parts if len(p) >= 2]
    if len(parts) <= 1:
        alt = re.split(r"\s*[·•]\s+|\s*\d+[.)]\s+", raw)
        alt = [p.strip(" .-•·\t") for p in alt if p and p.strip() and len(p.strip()) >= 2]
        if len(alt) > 1:
            parts = alt
    if not parts:
        return [raw]
    return parts[:limit]


def _details_block(summary: str, body_lines: list[str]) -> list[str]:
    if not _USE_DETAILS:
        return [f"#### {summary}", ""] + body_lines + [""]
    lines = [
        "<details>",
        f"<summary>{summary}</summary>",
        "",
    ]
    lines.extend(body_lines)
    if not body_lines or body_lines[-1] != "":
        lines.append("")
    lines.append("</details>")
    lines.append("")
    return lines


def _is_creation_entry(entry: Any) -> bool:
    return (getattr(entry, "change_type", None) or "") in _CREATION_TYPES


def _entry_has_confirmed_function_diff(entry: Any) -> bool:
    debug = getattr(entry, "debug_item", None) or {}
    evidence = debug.get("evidence_tier")
    reason = str(debug.get("classification_reason") or "")
    if evidence in {"DIRECT_BODY_CHANGE", "FUNCTION_CONTEXT_CHANGE"}:
        return True
    if reason.startswith("body_change") or reason.startswith("function_context"):
        return True
    if reason in {
        "parent_already_has_function",
        "parent_missing_function_definition",
        "creation_without_parent_proof",
        "definition_removed",
        "definition_replaced",
        "in_function_scope_log",
        "function_context_log",
    }:
        return True
    return False


def _first_desc_line(entry: Any) -> str:
    desc = (getattr(entry, "change_description", None) or "").strip()
    for part in desc.split("\n"):
        part = part.strip().lstrip("-").strip()
        if not part:
            continue
        # Drop internal limitation lines from the short table cell.
        if "세부 Diff" in part or "확보하지 못" in part or "확인하지 못" in part:
            continue
        if part.startswith("Commit 메시지상"):
            part = part.replace("Commit 메시지상 ", "").replace("(으)로 확인됩니다.", "").strip()
        return part
    return ""


def _clean_commit_message_line(message: str | None) -> str:
    if not message:
        return ""
    line = message.strip().splitlines()[0].strip()
    line = line.lstrip("#").strip()
    return line


def _user_history_summary(entry: Any, *, symbol: str | None = None) -> str:
    """User-facing change cell — Diff-first, message for concrete facts (v2.6)."""
    _ = symbol
    if _is_creation_entry(entry):
        return "함수 최초 확인"

    debug = getattr(entry, "debug_item", None) or {}
    first = _first_desc_line(entry)
    label = (getattr(entry, "change_type_label", None) or "").strip()
    message = _clean_commit_message_line(getattr(entry, "message", None))

    if _entry_has_confirmed_function_diff(entry):
        # Prefer explicit Commit-message facts over generic Diff subtype templates.
        if message and len(message) >= 4:
            text = message
        else:
            text = first or label or "함수 내부 변경 확인"
            # Drop verbose template endings for table cells.
            text = re.sub(r"을\(를\) 변경했습니다\.?$", " 변경", text)
            text = re.sub(r"을 변경했습니다\.?$", " 변경", text)
            text = re.sub(r"^함수 변경 구간에서\s*", "", text)
        if len(text) > 72:
            text = text[:70] + "…"
        return md_escape_cell(text)

    # SYMBOL_ONLY / MESSAGE_ONLY — never claim function-body change.
    topic = message or first or label or "관련 Commit"
    topic = re.sub(r"\(으\)로 확인됩니다\.?$", "", topic).strip()
    topic = re.sub(r"^Commit 메시지상\s*", "", topic).strip()
    if "대상 함수 Diff 미확인" not in topic:
        topic = f"{topic} (대상 함수 Diff 미확인)"
    if len(topic) > 72:
        topic = topic[:70] + "…"
    return md_escape_cell(topic)


def _entry_flow_category(entry: Any) -> str:
    """Internal section label — not shown in v2.6 user tables."""
    ct = getattr(entry, "change_type", "") or ""
    section = getattr(entry, "section", "") or ""
    if ct in _CREATION_TYPES:
        return "최초 추가"
    if ct == "comment_or_log" or section == "other":
        return "보조 변경"
    if section == "maintenance" or ct in {"date_logic_change", "function_deletion"}:
        return "유지보수"
    if section == "unconfirmed":
        return "연관 이력"
    return "기능 변경"


def _entry_git_basis(entry: Any) -> str:
    """Internal Git evidence label — not shown in v2.6 user tables."""
    reason = (getattr(entry, "debug_item", None) or {}).get("classification_reason") or ""
    evidence = (getattr(entry, "debug_item", None) or {}).get("evidence_tier")
    diff_state = getattr(entry, "diff_state", None)
    section = getattr(entry, "section", "") or ""
    if _is_creation_entry(entry):
        return "Git 최초 확인"
    if evidence == "DIRECT_BODY_CHANGE" or str(reason).startswith("body_change"):
        return "함수 Diff"
    if evidence == "FUNCTION_CONTEXT_CHANGE" or str(reason).startswith("function_context"):
        return "함수 변경 구간 확인"
    if reason in {
        "diff_unavailable",
        "message_only",
        "message_topic",
        "message_card_type",
        "message_date_hardcode",
    } or diff_state == "diff_unavailable":
        return "Commit 메시지"
    if reason in {
        "symbol_in_diff_scope_unknown",
        "symbol_not_in_diff",
        "symbol_only",
        "keyword_in_diff_hunk_header_only",
        "diff_topic",
    }:
        return "Symbol만 확인"
    if section == "unconfirmed":
        if str(reason).startswith("body_change"):
            return "함수 Diff"
        if str(reason).startswith("function_context"):
            return "함수 변경 구간 확인"
        return "검색 후보"
    if section in {"core", "other", "maintenance"}:
        return "함수 Diff"
    return "—"


def _entry_doc_link_basis(entry: Any) -> str:
    link = getattr(entry, "ppt_link", None)
    if link is None:
        return "—"
    strength = connection_strength(link.link_type)
    if strength in {STRENGTH_COMMIT_DIRECT, STRENGTH_STAGE}:
        return connection_strength_label(link.link_type)
    return "—"


def _entry_flow_basis(entry: Any) -> str:
    return _entry_git_basis(entry)


def _entry_flow_summary(entry: Any) -> str:
    return _user_history_summary(entry)


def _render_commit_doc_fields(entry: Any) -> list[str]:
    """Commit detail: only clear Commit-direct document links (v2.6).

    Stage/reference docs stay in the bottom ``## 관련 문서`` section only.
    """
    link = getattr(entry, "ppt_link", None)
    if link is None:
        return []
    strength = connection_strength(link.link_type)
    if strength != STRENGTH_COMMIT_DIRECT:
        return []
    doc = link.document_name or link.change_title or "(문서명 없음)"
    slide = f", Slide {link.slide_number}" if link.slide_number is not None else ""
    return [f"- 관련 문서: `{doc}`{slide}"]


_SPECULATIVE_RE = re.compile(
    r"(했을 수 있습니다|일 수 있습니다|로 보입니다|가능성이 있습니다|"
    r"^아마\b|추정됩니다)"
)


def _normalize_code_fact_line(text: str) -> str:
    """Strip bullet markers / Diff prefixes from a description line."""
    part = text.strip()
    if part.startswith("-"):
        part = part.lstrip("-").strip()
    part = re.sub(r"^Diff에서\s*", "", part)
    part = re.sub(r"을\(를\) 변경했습니다\.?$", " 변경", part)
    part = re.sub(r"을 변경했습니다\.?$", " 변경", part)
    part = re.sub(r"를 변경했습니다\.?$", " 변경", part)
    return part.strip()


def _is_commit_message_echo(line: str, message: str | None) -> bool:
    """True when a description line is just a copy of the Commit message."""
    msg = _clean_commit_message_line(message)
    if not msg or not line:
        return False
    a = re.sub(r"\s+", " ", line).strip().lower()
    b = re.sub(r"\s+", " ", msg).strip().lower()
    if not a or not b:
        return False
    return a == b or a in b or b in a


def _code_confirmed_lines(entry: Any) -> list[str]:
    """Diff-verified fact lines for ``코드에서 확인`` (no Commit-message echo)."""
    message = getattr(entry, "message", None)
    out: list[str] = []
    for raw in (getattr(entry, "change_description", None) or "").split("\n"):
        part = _normalize_code_fact_line(raw)
        if not part:
            continue
        if "세부 Diff" in part or "확인하지 못" in part or "확보하지 못" in part:
            continue
        if part.startswith("Commit 메시지"):
            continue
        if _is_commit_message_echo(part, message):
            continue
        if _SPECULATIVE_RE.search(part):
            continue
        out.append(part)
    return out


def _render_entry_details(
    entry: Any,
    *,
    heading_fn,
    detailed: bool,
    symbol: str | None = None,
) -> list[str]:
    heading = _user_history_summary(entry, symbol=symbol)
    # Prefer plain text heading without markdown escapes for <summary>
    heading_plain = heading.replace("\\|", "|")
    date = format_date_display(entry.commit_date)
    summary = (
        f"{md_escape_html(date)} · "
        f"<code>{md_escape_html(short_hash(entry.commit_hash))}</code> · "
        f"{md_escape_html(heading_plain)}"
    )
    body: list[str] = []
    if entry.message:
        body.append(f"- Commit 메시지: `{entry.message[:240]}`")

    if _entry_has_confirmed_function_diff(entry) or _is_creation_entry(entry):
        facts = _code_confirmed_lines(entry)
        if facts:
            body.append("- 코드에서 확인:")
            for part in facts:
                body.append(f"  - {part}")
    else:
        body.append(
            "- 확인 상태: 대상 함수의 세부 Diff는 확인하지 못했습니다."
        )

    if detailed and entry.impact:
        body.append(f"- 영향: {entry.impact}")
    body.extend(_render_commit_doc_fields(entry))
    return _details_block(summary, body)


def _entry_commit_summary(entry: Any) -> str:
    """One-line summary for brief context / commit lists."""
    desc = (getattr(entry, "change_description", None) or "").strip()
    for part in desc.split("\n"):
        part = part.strip().lstrip("-").strip()
        if part:
            return part[:120]
    return getattr(entry, "change_type_label", None) or _entry_flow_category(entry)


def _entry_link_fields(entry: Any) -> tuple[str, str]:
    """Return (connection type label, reason) for a commit's document link."""
    link = getattr(entry, "ppt_link", None)
    if link is None:
        return "—", ""
    return connection_strength_label(link.link_type), (link.link_reason_user or "").strip()


def _render_doc_linked_commits(doc: PptLink, entries: list[Any]) -> list[str]:
    """List linked commits without connection-strength grade labels (v2.6)."""
    linked = _linked_commits_for_doc(doc, entries)
    lines: list[str] = []
    if not linked:
        lines.append("- 확정된 단일 Commit은 없습니다.")
        return lines
    for e in linked[:12]:
        h = short_hash(e.commit_hash)
        lines.append(f"- `{h}` · {format_date_display(e.commit_date)}")
    return lines


def _linked_commits_for_doc(doc: PptLink, entries: list[Any]) -> list[Any]:
    """Commits that already carry this document identity — no date-based attach."""
    return [
        e
        for e in entries
        if e.ppt_link and e.ppt_link.identity_key() == doc.identity_key()
    ]


def _doc_display_link_type(doc: PptLink, entries: list[Any]) -> str:
    """Strongest connection type across entry links for this document."""
    types = [doc.link_type]
    for e in entries:
        link = getattr(e, "ppt_link", None)
        if link is not None and link.identity_key() == doc.identity_key():
            types.append(link.link_type)
    best = LINK_RELATED
    best_rank = -1
    rank = {
        LINK_COMMIT_DIRECT: 3,
        LINK_FEATURE_RELEASE: 2,
        LINK_MAINTENANCE: 1,
        LINK_DEV_REFERENCE: 1,
        LINK_RELATED: 1,
    }
    for lt in types:
        r = rank.get(lt, 0)
        if r > best_rank:
            best = lt
            best_rank = r
    return best


def _count_docs_by_strength(docs: list[PptLink], entries: list[Any]) -> dict[str, int]:
    counts = {
        STRENGTH_COMMIT_DIRECT: 0,
        STRENGTH_STAGE: 0,
        STRENGTH_RELATED: 0,
    }
    for doc in docs:
        strength = connection_strength(_doc_display_link_type(doc, entries))
        counts[strength] = counts.get(strength, 0) + 1
    return counts


def _render_related_official_doc(
    doc: PptLink,
    entries: list[Any],
    *,
    query_symbol: str | None = None,
    query_file_path: str | None = None,
) -> list[str]:
    title = doc.change_title or doc.document_name or "관련 문서"
    lines: list[str] = [f"**{title}**", ""]
    lines += ["| 항목 | 내용 |", "|---|---|"]
    if doc.document_name:
        lines.append(f"| 문서 | `{md_escape_cell(doc.document_name)}` |")
    if doc.slide_number is not None:
        lines.append(f"| Slide | {doc.slide_number} |")
    if doc.document_date:
        lines.append(f"| 작성일 | {md_escape_cell(doc.document_date)} |")
    if doc.versions:
        lines.append(f"| 적용 버전 | {md_escape_cell(' / '.join(doc.versions))} |")
    if doc.csr_no:
        lines.append(f"| CSR | {md_escape_cell(doc.csr_no)} |")
    lines.append("")

    if doc.business_background:
        lines.append(f"- 업무 배경: {doc.business_background[:240]}")
        lines.append("")

    bullets = split_to_be_bullets(doc.to_be)
    if bullets:
        lines.append("**주요 변경 내용**")
        lines.append("")
        for b in bullets:
            lines.append(f"- {b}")
        lines.append("")
    as_is = (doc.as_is or "").strip()
    if as_is and as_is.upper() != "N/A":
        lines.append(f"- As-Is: {as_is[:200]}")
        lines.append("")

    related_body: list[str] = []
    if doc.related_source_paths:
        shown, omitted = _prioritize_for_display(
            list(doc.related_source_paths),
            preferred=query_file_path,
            limit=_RELATED_SOURCES_DISPLAY_LIMIT,
            match_fn=_path_match_display,
        )
        related_body.append("### 관련 소스")
        for p in shown:
            related_body.append(f"- {p}")
        if omitted:
            related_body.append(f"- 외 {omitted}개")
        related_body.append("")
    if doc.related_symbols:
        shown, omitted = _prioritize_for_display(
            list(doc.related_symbols),
            preferred=query_symbol,
            limit=_RELATED_SYMBOLS_DISPLAY_LIMIT,
            match_fn=_symbols_match_display,
        )
        related_body.append("### 관련 함수")
        for s in shown:
            related_body.append(f"- {s}()")
        if omitted:
            related_body.append(f"- 외 {omitted}개")
        related_body.append("")
    # Linked commits stay in Evidence Link / entry.ppt_link for internal use —
    # do not expose "### 연결 Commit" on the user Markdown (v2.6).
    if related_body:
        lines.extend(_details_block("관련 소스·함수 보기", related_body))
    return lines


def _collect_caution_lines(
    entries: list[Any],
    *,
    official_docs: list[PptLink],
    user_limitation_note,
) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        reason = (getattr(entry, "debug_item", None) or {}).get("classification_reason")
        note = getattr(entry, "confirmation_note", None) or user_limitation_note(
            reason, getattr(entry, "diff_state", None)
        )
        needs = False
        if entry.section == "unconfirmed":
            needs = True
        if reason in {
            "diff_unavailable",
            "symbol_not_in_diff",
            "symbol_in_diff_scope_unknown",
            "message_only",
        }:
            needs = True
        if entry.diff_state == "diff_unavailable":
            needs = True
        desc = entry.change_description or ""
        if "세부 Diff는 확보하지 못했" in desc:
            needs = True
            if not note or "Diff" not in note:
                note = (
                    "Commit 메시지는 대상 기능과 관련되지만 "
                    "대상 함수의 세부 Diff를 확보하지 못했습니다."
                )
        if not needs or not note:
            continue
        h = short_hash(entry.commit_hash)
        key = f"{h}|{note}"
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- `{h}`: {note}")

    has_direct = any(
        e.ppt_link and e.ppt_link.link_type == LINK_COMMIT_DIRECT for e in entries
    )
    if official_docs and not has_direct:
        lines.append(
            "- 관련 공식 문서는 확인되었으나 개별 Commit 직접 근거로 확인된 문서는 없습니다."
        )
    return lines


def render_lifecycle_markdown(
    symbol: str,
    entries: list[Any],
    overall_label: str,
    counts: dict,
    *,
    entry_heading,
    user_limitation_note,
    build_narrative,
) -> str:
    """Build the user-facing lifecycle Markdown document (PROJECT_SPEC v2.6 §12)."""
    _ = (overall_label, entry_heading, build_narrative)  # retained for call-site compat
    creation = next((e for e in entries if _is_creation_entry(e)), None)

    all_links = [e.ppt_link for e in entries if e.ppt_link]
    stage_docs: list[PptLink] = list(counts.get("_stage_official_docs") or [])
    request_eid = counts.get("_request_equipment_id")
    request_ename = counts.get("_request_equipment_name")
    query_file_path = counts.get("_query_file_path")
    official_docs = merge_official_doc_collections(
        all_links,
        stage_docs,
        request_equipment_id=request_eid,
        request_equipment_name=request_ename,
    )
    doc_n = len(official_docs)

    flow_entries = [
        e
        for e in entries
        if getattr(e, "section", None) in {"core", "other", "maintenance", "unconfirmed"}
    ]
    flow_entries = sorted(
        flow_entries,
        key=lambda e: (e.commit_date or "9999", e.commit_hash or ""),
    )
    subsequent_n = max(0, len(flow_entries) - (1 if creation else 0))
    # Keep counts in sync for Output / callers.
    counts["subsequent_change_count"] = subsequent_n
    counts["displayed_git_count"] = len(flow_entries)
    counts["related_document_count"] = doc_n

    lines: list[str] = [f"# {symbol} 변경 이력", "", "## 한눈에 보기", ""]
    lines += ["| 항목 | 결과 |", "|---|---|"]

    if creation:
        lines.append(
            f"| 최초 확인 | {format_date_display(creation.commit_date)} · "
            f"`{short_hash(creation.commit_hash)}` |"
        )
    else:
        lines.append("| 최초 확인 | 확인되지 않음 |")

    lines.append(f"| 이후 Git 이력 | {subsequent_n}건 |")
    lines.append(f"| 관련 문서 | {doc_n}건 |" if doc_n else "| 관련 문서 | 0건 |")
    if isinstance(query_file_path, str) and query_file_path.strip():
        lines.append(f"| 조회 파일 | `{md_escape_cell(query_file_path)}` |")
    lines.append("")

    # --- 변경 이력 (3-column) ---
    lines += ["## 변경 이력", ""]
    if not flow_entries:
        lines.append("- 표시할 변경 이력이 없습니다.")
    else:
        lines += [
            "| 날짜 | Commit | 변경 내용 |",
            "|---|---|---|",
        ]
        for entry in flow_entries:
            lines.append(
                "| "
                f"{format_date_display(entry.commit_date)} | "
                f"`{short_hash(entry.commit_hash)}` | "
                f"{_user_history_summary(entry, symbol=symbol)} |"
            )

    # --- 변경 상세 (single chronological section) ---
    lines += ["", "## 변경 상세", ""]
    if not flow_entries:
        lines.append("- 표시할 변경 상세가 없습니다.")
        lines.append("")
    else:
        for entry in flow_entries:
            lines.extend(
                _render_entry_details(
                    entry,
                    heading_fn=entry_heading,
                    detailed=True,
                    symbol=symbol,
                )
            )

    # --- 관련 문서 ---
    lines += ["", "## 관련 문서", ""]
    if not official_docs:
        lines.append("관련 문서를 찾지 못했습니다.")
        lines.append("")
    else:
        for doc in official_docs:
            lines.extend(
                _render_related_official_doc(
                    doc,
                    entries,
                    query_symbol=symbol,
                    query_file_path=query_file_path
                    if isinstance(query_file_path, str)
                    else None,
                )
            )

    # Diff-limitation notes stay inside commit details; keep optional caution only
    # when useful, without confidence grades.
    cautions = _collect_caution_lines(
        entries,
        official_docs=official_docs,
        user_limitation_note=user_limitation_note,
    )
    # Soften / skip global caution section when notes already appear in details.
    _ = cautions

    cite_body: list[str] = ["### Git Commit", ""]
    seen_c: set[str] = set()
    for entry in flow_entries:
        h = short_hash(entry.commit_hash)
        if h in seen_c:
            continue
        seen_c.add(h)
        cite_body.append(f"- `{h}`")
    cite_body.append("")
    cite_body.append("### 변경내역서")
    cite_body.append("")
    if official_docs:
        for doc in official_docs:
            name = doc.document_name or doc.change_title or "(문서명 없음)"
            slide = f", Slide {doc.slide_number}" if doc.slide_number is not None else ""
            cite_body.append(f"- `{md_escape_cell(name)}`{slide}")
    else:
        cite_body.append("- 없음")
    cite_body.append("")
    lines += ["", "## 전체 참조 근거", ""]
    lines.extend(_details_block("Git Commit 및 변경내역서 전체 보기", cite_body))

    from datetime import datetime

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines += ["", "---", f"조회: {now}"]
    return "\n".join(lines).rstrip() + "\n"
