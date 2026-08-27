"""POC v2.3: Source Trace VS Code Extension analyze helpers.

Pure, side-effect-free helpers used by ``app.api.trace_extension``. This module
never calls Ollama or touches Evidence/Link Score/Query Relevance — it only:

1. Normalizes an (often absolute, IDE-side) file path to a repository-relative
   path using the equipment's registered Git repository local paths — falling
   back to a path-suffix / basename guess so Evidence search never breaks.
2. Truncates ``selected_code`` to a bounded size before it reaches Evidence
   search / Ollama (never send a full file).
3. Extracts C function names from ``selected_code`` and a file mention from
   free-text query and synthesizes a search-friendly ``query`` string, since
   the Extension's default question is purely instructional
   ("선택한 코드가 왜 변경됐는지 알려줘") and carries no keyword the STEP 4
   Git candidate search can use on its own.
4. Renders the final STEP 8 Evidence Grounded Answer as the Extension's
   official Korean Markdown result.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from pathlib import PurePosixPath

from app.schemas.trace import GitCandidate
from app.services.evidence_service import EvidenceLink, EvidenceResult
from app.services.git_repository_service import list_repositories
from app.services.ollama_service import EvidenceRef, OllamaAnalysisResult
from app.services.query_relevance_service import EVIDENCE_QUERY_STOPWORDS

MAX_SELECTED_CODE_CHARS = 4000

# Instructional/boilerplate phrasing that must never become a search core
# keyword (distinct from app.services.query_relevance_service's own
# EVIDENCE_QUERY_STOPWORDS, which governs STEP 7 Query Relevance itself — not
# touched here).
INSTRUCTION_STOPWORDS = frozenset(
    {
        "선택한",
        "분석",
        "결과",
        "그대로",
        "요약",
        "요약해줘",
        "새로운",
        "추측",
        "하지",
        "말고",
        "근거",
        "없는",
        "말하지",
        "컨텍스트",
        "보여줘",
        "알려줘",
        "찾아줘",
        "언제",
        "추가",
        "추가되었어",
        "변경되었어",
    }
)

# Generic conversational/demonstrative filler that refers to "the code" itself
# rather than naming anything searchable ("코드가", "이 함수", "왜 바뀐 거야?").
# Small and deliberately narrow — real business nouns (e.g. "영수증") never
# match this set, only literally reference words about code/change itself.
_GENERIC_CODE_REFERENCE_STOPWORDS = frozenset(
    {
        "이",
        "그",
        "저",
        "이거",
        "그거",
        "저거",
        "코드",
        "소스",
        "거야",
        "바뀐",
        "건가요",
        "건지",
        "그런지",
        "입니다",
        "파일은",
        "파일",
    }
)

MISSING_CONTEXT_MESSAGE = (
    "선택 코드 또는 현재 파일 정보가 전달되지 않아 변경 이력을 조회할 수 없습니다. "
    "함수명 또는 파일명을 질문에 포함해 주세요.\n\n"
    "예: card_sc_check_valid 함수 변경 이력 알려줘. 파일은 card_sc_tm.c 입니다."
)

_ALL_ADAPTER_STOPWORD_SETS = (
    INSTRUCTION_STOPWORDS,
    EVIDENCE_QUERY_STOPWORDS,
    _GENERIC_CODE_REFERENCE_STOPWORDS,
)

_ABS_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/)")


def _safe_list_repositories(equipment_id: int) -> list:
    try:
        return list_repositories(equipment_id)
    except Exception:  # Adapter must never fail on a DB/lookup hiccup.
        return []


def normalize_file_path(
    file_path: str | None, equipment_id: int | None
) -> tuple[str | None, str]:
    """Best-effort repository-relative normalize.

    Returns ``(normalized_path, method)`` where ``method`` is one of:
    ``repository_resolved`` | ``repository_relative`` | ``suffix_fallback`` |
    ``basename_fallback`` | ``unchanged`` | ``none``. Never raises and never
    blocks Evidence search — an un-normalizable path is passed through unchanged.

    Prefers the shared ``resolve_equipment_repository`` path so function-history
    and selection-code results show the same repo-relative path (v2.6).
    """
    if not file_path or not file_path.strip():
        return None, "none"

    raw = file_path.strip()
    posix = raw.replace("\\", "/")

    if equipment_id is not None:
        from app.services.repository_resolver import (
            RepositoryResolveError,
            resolve_equipment_repository,
            strip_local_path_prefix,
        )

        stripped, method = strip_local_path_prefix(posix, equipment_id)
        candidates: list[str] = []
        if method == "repository_relative" and stripped:
            candidates.append(stripped)
        # Relative client path (already repo-relative from Extension).
        if not _ABS_PATH_RE.match(posix):
            candidates.append(posix.lstrip("/"))
        # Absolute Remote-SSH: try progressively shorter suffixes.
        if _ABS_PATH_RE.match(posix):
            parts = [p for p in posix.split("/") if p]
            for i in range(len(parts)):
                cand = "/".join(parts[i:])
                if cand and cand not in candidates:
                    candidates.append(cand)

        for cand in candidates:
            try:
                resolved = resolve_equipment_repository(
                    equipment_id=equipment_id,
                    repo_relative_path=cand,
                )
                return resolved.rel_path, "repository_resolved"
            except RepositoryResolveError:
                continue
            except Exception:
                break

        if method == "repository_relative" and stripped is not None:
            return stripped, method

    if _ABS_PATH_RE.match(posix):
        parts = [p for p in posix.split("/") if p]
        if len(parts) >= 3:
            return "/".join(parts[-3:]), "suffix_fallback"
        if parts:
            return parts[-1], "basename_fallback"
        return posix, "unchanged"

    return posix, "unchanged"


def truncate_selected_code(code: str | None) -> tuple[str | None, bool]:
    """Bound selected_code before it reaches Evidence search / Ollama."""
    if not code:
        return code, False
    if len(code) <= MAX_SELECTED_CODE_CHARS:
        return code, False
    return code[:MAX_SELECTED_CODE_CHARS], True


# --- selected_code symbol extraction + search-query synthesis -------------

_C_KEYWORDS_BLOCKLIST = frozenset(
    {
        "return",
        "if",
        "while",
        "for",
        "switch",
        "sizeof",
        "typedef",
        "case",
        "goto",
        "else",
        "do",
        "defined",
    }
)

# Common libc / logging helpers — too generic to drive Evidence search alone.
_C_CALL_WEAK_BLOCKLIST = frozenset(
    {
        "memset",
        "memcpy",
        "memmove",
        "memcmp",
        "printf",
        "sprintf",
        "snprintf",
        "fprintf",
        "scanf",
        "sscanf",
        "malloc",
        "calloc",
        "realloc",
        "free",
        "strlen",
        "strcpy",
        "strncpy",
        "strcmp",
        "strncmp",
        "strcat",
        "strncat",
        "atoi",
        "atol",
        "atof",
        "exit",
        "abort",
        "assert",
        "log_print",
        "log_printf",
        "printk",
        "puts",
        "putchar",
        "getchar",
        "fopen",
        "fclose",
        "fread",
        "fwrite",
        "fflush",
    }
)

# Bare single C identifier: selected_code="test_Alias" (Extension double-click).
_C_SINGLE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Matches `RET_TYPE name(args) {` / `RET_TYPE name(args);` shapes, e.g.
# `int card_sc_check_valid(...)`, `static int get_pass_level_string(...)`,
# `void file_close_init(...)`. Best-effort regex, not a C parser.
_C_FUNC_SIG_RE = re.compile(
    r"(?:\b(?:static|inline|extern|const|unsigned|signed|volatile)\s+)*"
    r"(?:struct\s+\w+\s+)?"
    r"\b([A-Za-z_]\w*)\b[ \t]*\*{0,2}[ \t]*"
    r"\b([A-Za-z_]\w*)\b[ \t]*"
    r"\(([^;{}()]*)\)[ \t\r\n]*(\{|;)",
    re.MULTILINE,
)

# Bare call sites: `name(` — used only when no definition/declaration matched.
_C_FUNC_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def extract_function_symbols(code: str | None) -> list[str]:
    """Best-effort C function name extraction from selected code.

    Priority: bare single identifier (Extension selection_symbol) →
    declaration/definition names → call-site names.
    Never raises — unmatched or non-C input simply yields an empty list.
    """
    if not code:
        return []

    stripped = code.strip()
    if _C_SINGLE_IDENT_RE.fullmatch(stripped):
        if stripped.lower() not in _C_KEYWORDS_BLOCKLIST:
            return [stripped]

    definitions: list[str] = []
    seen_defs: set[str] = set()
    for match in _C_FUNC_SIG_RE.finditer(code):
        type_token, name, _args, _brace = match.groups()
        if type_token.lower() in _C_KEYWORDS_BLOCKLIST:
            continue
        if name.lower() in _C_KEYWORDS_BLOCKLIST:
            continue
        if name in seen_defs:
            continue
        seen_defs.add(name)
        definitions.append(name)

    if definitions:
        return definitions

    calls: list[str] = []
    seen_calls: set[str] = set()
    for match in _C_FUNC_CALL_RE.finditer(code):
        name = match.group(1)
        lower = name.lower()
        if lower in _C_KEYWORDS_BLOCKLIST or lower in _C_CALL_WEAK_BLOCKLIST:
            continue
        if name in seen_calls:
            continue
        seen_calls.add(name)
        calls.append(name)
    return calls


def preview_text(text: str | None, max_chars: int) -> str:
    """Truncated preview for debug/logs — never the full body."""
    raw = text or ""
    if len(raw) <= max_chars:
        return raw
    return raw[:max_chars] + "…"


# Recognizes a bare filename/path token with a common source extension
# anywhere in free text, e.g. "파일은 card_sc_tm.c 입니다.", "File: card_sc_tm.c".
# Also matches when a Korean suffix is glued: "card_sc_tm.c파일".
_SOURCE_FILE_MENTION_RE = re.compile(
    r"([A-Za-z0-9_][A-Za-z0-9_./\\-]*\.(?:c|h|cpp|cc|hpp|hxx))(?=\b|[가-힣]|$)",
    re.IGNORECASE,
)

# C identifier glued to a Korean suffix: test_Alias함수 → test_Alias + 함수
_ID_KO_GLUE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?=[가-힣])")

# Standalone C identifiers in normalized free text (for query synthesis fallback).
_C_IDENTIFIER_IN_TEXT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def normalize_query_text(text: str | None) -> str:
    """Split glued Latin identifiers / filenames from following Korean text.

    Examples:
    - test_Alias함수 → test_Alias 함수
    - card_sc_check_valid함수 → card_sc_check_valid 함수
    - card_sc_tm.c파일 → card_sc_tm.c 파일
    - 파일은 card_sc_tm.c입니다 → 파일은 card_sc_tm.c 입니다
    """
    raw = (text or "").strip()
    if not raw:
        return ""

    def _split_file_glued(match: re.Match[str]) -> str:
        return match.group(1) + " "

    normalized = _SOURCE_FILE_MENTION_RE.sub(_split_file_glued, raw)
    normalized = _ID_KO_GLUE_RE.sub(r"\1 ", normalized)
    # Korean particle glued after filename: card_sc_tm.c입니다
    normalized = re.sub(
        r"(\.(?:c|h|cpp|cc|hpp|hxx))([가-힣])",
        r"\1 \2",
        normalized,
        flags=re.IGNORECASE,
    )
    return " ".join(normalized.split())


def extract_c_identifiers(text: str | None) -> list[str]:
    """Extract C-style identifiers from normalized free text."""
    normalized = normalize_query_text(text)
    if not normalized:
        return []
    symbols: list[str] = []
    seen: set[str] = set()
    for match in _C_IDENTIFIER_IN_TEXT_RE.finditer(normalized):
        name = match.group(0)
        if len(name) < 2:
            continue
        if name.lower() in _C_KEYWORDS_BLOCKLIST:
            continue
        if name in seen:
            continue
        seen.add(name)
        symbols.append(name)
    return symbols


def extract_file_mention(text: str | None) -> str | None:
    """Best-effort filename extraction from free text."""
    if not text:
        return None
    normalized = normalize_query_text(text)
    match = _SOURCE_FILE_MENTION_RE.search(normalized)
    if match:
        return match.group(1)
    # Fallback: original text before normalization (path may already be spaced).
    match = _SOURCE_FILE_MENTION_RE.search(text)
    return match.group(1) if match else None


def file_basename(path: str | None) -> str | None:
    """Basename of a (possibly absolute/backslash) path, for query synthesis."""
    if not path:
        return None
    name = PurePosixPath(path.replace("\\", "/")).name
    return name or path


_TOKEN_STRIP_RE = re.compile(r'^[\s"\'(\[]+|[\s"\')\].,!?~:;]+$')


def _tokenize(text: str) -> list[str]:
    return [tok for tok in (_TOKEN_STRIP_RE.sub("", t) for t in (text or "").split()) if tok]


def _is_weak_or_instruction_token(token: str) -> bool:
    """Instructional boilerplate OR STEP 7's own weak/filler words.

    Reuses ``EVIDENCE_QUERY_STOPWORDS`` (read-only) plus its conjugated-form
    heuristic (token starts with a >=2-char stopword and isn't much longer)
    so "변경됐는지"/"보여줘요" style conjugations are caught the same way STEP 7
    already treats them — without modifying query_relevance_service at all.
    """
    t = token.strip()
    if not t:
        return True
    tl = t.lower()
    for stopword_set in _ALL_ADAPTER_STOPWORD_SETS:
        if t in stopword_set or tl in stopword_set:
            return True
        for sw in stopword_set:
            swl = sw.lower()
            if len(swl) >= 2 and tl.startswith(swl) and len(tl) <= len(swl) + 4:
                return True
    return False


def merge_selected_code_symbols(
    selected_code: str | None,
    symbols: list[str],
    detected_symbol: str | None = None,
) -> list[str]:
    """Merge regex-extracted symbols with Extension-provided detected_symbol."""
    merged: list[str] = []
    seen: set[str] = set()
    for name in [detected_symbol, *(symbols or [])]:
        if not name:
            continue
        token = name.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        merged.append(token)
    if merged:
        return merged
    if selected_code:
        stripped = selected_code.strip()
        if _C_SINGLE_IDENT_RE.fullmatch(stripped):
            return [stripped]
    return []


def detect_query_intent(raw_query: str | None) -> str:
    """Adapter-only intent tag for markdown/history emphasis (not STEP 7 scoring)."""
    text = normalize_query_text(raw_query).lower()
    if not text:
        return "general"
    history_markers = (
        "언제 추가",
        "언제 추가되었",
        "언제 만들어",
        "처음 추가",
        "최초 추가",
        "언제 등록",
    )
    if any(m in text for m in history_markers):
        return "history_added"
    change_markers = ("왜 변경", "왜 바뀌", "변경 이유", "변경됐", "변경되었", "왜 변경됐")
    if any(m in text for m in change_markers):
        return "change_reason"
    return "general"


def _symbol_match_tokens(symbol: str) -> list[str]:
    tokens = [symbol]
    if "_" in symbol:
        tail = symbol.rsplit("_", 1)[-1]
        if len(tail) >= 3 and tail not in tokens:
            tokens.append(tail)
    return tokens


def _text_matches_symbol(text: str | None, symbol: str) -> bool:
    if not text or not symbol:
        return False
    lower = text.lower()
    for token in _symbol_match_tokens(symbol):
        if token.lower() in lower:
            return True
    return False


def _source_function_entries(change_item) -> list[dict]:
    """Normalize source_functions entries to dicts (never crash on odd shapes)."""
    entries: list[dict] = []
    for sf in getattr(change_item, "source_functions", None) or []:
        if isinstance(sf, dict):
            entries.append(sf)
            continue
        if hasattr(sf, "get"):
            try:
                entries.append(
                    {
                        "file_path": sf.get("file_path"),
                        "functions": sf.get("functions") or [],
                    }
                )
                continue
            except Exception:
                pass
        file_path = getattr(sf, "file_path", None)
        functions = getattr(sf, "functions", None) or []
        entries.append({"file_path": file_path, "functions": list(functions)})
    return entries


def change_item_matches_symbol(change_item, symbol: str) -> bool:
    """True when change-item title/source_functions/detail mention the symbol.

    File-path alone never counts. ``raw_text`` is checked last and only for
    clear symbol tokens (not used as the sole answer authority when a stronger
    title/function match exists elsewhere — see ``_symbol_answer_rank``).
    """
    try:
        if _text_matches_symbol(getattr(change_item, "change_title", None), symbol):
            return True
        for field in ("business_background", "current_status", "as_is", "to_be"):
            if _text_matches_symbol(getattr(change_item, field, None), symbol):
                return True
        for sf in _source_function_entries(change_item):
            for fn in sf.get("functions") or []:
                if _text_matches_symbol(str(fn) if fn is not None else None, symbol):
                    return True
        if _text_matches_symbol(getattr(change_item, "raw_text", None), symbol):
            return True
    except Exception:
        return False
    return False


def git_candidate_matches_symbol(git, symbol: str) -> bool:
    """True when Git message / match reasons mention the symbol.

    File-path-only matches are NOT enough (card_sc_tm.c ≠ test_Alias).
    Generic words like '추가' are never treated as symbol evidence here.
    """
    try:
        if _text_matches_symbol(getattr(git, "message", None), symbol):
            return True
        for reason in getattr(git, "match_reasons", None) or []:
            text = reason if isinstance(reason, str) else str(reason)
            if _text_matches_symbol(text, symbol):
                return True
        for reason in getattr(git, "query_match_reasons", None) or []:
            keyword = getattr(reason, "keyword", None)
            value = getattr(reason, "value", None)
            if isinstance(reason, dict):
                keyword = reason.get("keyword")
                value = reason.get("value")
            if _text_matches_symbol(keyword, symbol) or _text_matches_symbol(value, symbol):
                return True
    except Exception:
        return False
    return False


def _link_reasons_match_symbol(link: EvidenceLink, symbol: str) -> bool:
    """True when Evidence Link Match / Query Match reasons mention the symbol."""
    try:
        for mr in getattr(link, "match_reasons", None) or []:
            if isinstance(mr, dict):
                values = [
                    mr.get("type"),
                    mr.get("git_value"),
                    mr.get("change_item_value"),
                ]
            else:
                values = [
                    getattr(mr, "type", None),
                    getattr(mr, "git_value", None),
                    getattr(mr, "change_item_value", None),
                ]
            # File-path-only link reasons never qualify as symbol evidence.
            reason_type = str(values[0] or "")
            if reason_type in {"same_file_path", "same_file_basename"}:
                if not (
                    _text_matches_symbol(values[1], symbol)
                    or _text_matches_symbol(values[2], symbol)
                ):
                    continue
            for value in values[1:]:
                if _text_matches_symbol(value, symbol):
                    return True
            if reason_type == "same_function_exact" and (
                _text_matches_symbol(values[1], symbol)
                or _text_matches_symbol(values[2], symbol)
            ):
                return True
        for qr in getattr(link, "query_match_reasons", None) or []:
            if isinstance(qr, dict):
                keyword, value, field = qr.get("keyword"), qr.get("value"), qr.get("field")
            else:
                keyword = getattr(qr, "keyword", None)
                value = getattr(qr, "value", None)
                field = getattr(qr, "field", None)
            # Path-only query matches are scope, not symbol answer authority.
            if str(field or "") in {"file_path", "path_scope", "request_files"}:
                continue
            if _text_matches_symbol(keyword, symbol) or _text_matches_symbol(value, symbol):
                return True
    except Exception:
        return False
    return False


def evidence_link_matches_symbol(link: EvidenceLink, symbol: str) -> bool:
    """True when change item, Git, or Link/Query Match reasons mention the symbol."""
    try:
        if change_item_matches_symbol(link.change_item, symbol):
            return True
        if git_candidate_matches_symbol(link.git_candidate, symbol):
            return True
        if _link_reasons_match_symbol(link, symbol):
            return True
    except Exception:
        return False
    return False


def _symbol_answer_rank(link: EvidenceLink, symbol: str) -> int:
    """Higher = better answer Top Evidence Link for ``selected_symbol``.

    Prefer title / same_function / request-function query match over raw_text
    or file-scoped noise. File-path-only never scores.
    """
    score = 0
    try:
        item = link.change_item
        if _text_matches_symbol(getattr(item, "change_title", None), symbol):
            score += 100
        for field in ("business_background", "current_status", "as_is", "to_be"):
            if _text_matches_symbol(getattr(item, field, None), symbol):
                score += 40
        for sf in _source_function_entries(item):
            for fn in sf.get("functions") or []:
                text = str(fn) if fn is not None else ""
                if text.lower() == symbol.lower():
                    score += 90
                elif _text_matches_symbol(text, symbol):
                    score += 70
        for mr in getattr(link, "match_reasons", None) or []:
            reason_type = mr.get("type") if isinstance(mr, dict) else getattr(mr, "type", None)
            git_value = (
                mr.get("git_value") if isinstance(mr, dict) else getattr(mr, "git_value", None)
            )
            ci_value = (
                mr.get("change_item_value")
                if isinstance(mr, dict)
                else getattr(mr, "change_item_value", None)
            )
            if reason_type == "same_function_exact" and (
                _text_matches_symbol(git_value, symbol)
                or _text_matches_symbol(ci_value, symbol)
            ):
                score += 95
        for qr in getattr(link, "query_match_reasons", None) or []:
            if isinstance(qr, dict):
                keyword, value, field = qr.get("keyword"), qr.get("value"), qr.get("field")
            else:
                keyword = getattr(qr, "keyword", None)
                value = getattr(qr, "value", None)
                field = getattr(qr, "field", None)
            if str(field or "") in {"file_path", "path_scope", "request_files"}:
                continue
            if _text_matches_symbol(keyword, symbol) or _text_matches_symbol(value, symbol):
                score += 60
        if git_candidate_matches_symbol(link.git_candidate, symbol):
            score += 35
        # raw_text alone is weak — only a small bump if nothing stronger fired.
        if score == 0 and _text_matches_symbol(getattr(item, "raw_text", None), symbol):
            score += 10
    except Exception:
        return score
    return score


def apply_selected_symbol_guard(
    evidence_result: EvidenceResult, primary_symbol: str | None
) -> tuple[EvidenceResult, bool]:
    """Keep only symbol-matched Evidence links for the final answer; never invent.

    When ``selected_symbol`` is set:
    - file_path remains search scope only (already applied upstream)
    - answer ``evidence_links`` are filtered to symbol matches and ranked so
      Top Evidence Link is the same authority for summary / history / reason
    - file-path-only links (e.g. 기후동행카드 on card_sc_tm.c) are dropped
    ``EvidenceResult`` is a dataclass — use ``dataclasses.replace``.
    """
    if not primary_symbol or not evidence_result.evidence_links:
        return evidence_result, False

    links = list(evidence_result.evidence_links)
    matching = [
        link
        for link in links
        if evidence_link_matches_symbol(link, primary_symbol)
        and _symbol_answer_rank(link, primary_symbol) > 0
    ]
    if not matching:
        # No symbol-qualified link — clear answer links so Markdown cannot fall
        # back to a file-path-only Top candidate (기후동행카드 등).
        updated = replace(evidence_result, evidence_links=[])
        return updated, True

    both = [
        link
        for link in matching
        if change_item_matches_symbol(link.change_item, primary_symbol)
        and git_candidate_matches_symbol(link.git_candidate, primary_symbol)
    ]

    both_ids = {id(link) for link in both}

    def _sort_key(link: EvidenceLink) -> tuple[int, int, int]:
        both_bonus = 1_000_000 if id(link) in both_ids else 0
        rank = _symbol_answer_rank(link, primary_symbol)
        # Stable preference for higher link_score among equal symbol ranks.
        link_score = int(getattr(link, "link_score", 0) or 0)
        return (both_bonus + rank, link_score, -links.index(link))

    ordered = sorted(matching, key=_sort_key, reverse=True)
    updated = replace(evidence_result, evidence_links=ordered)
    return updated, True


def build_search_query(
    raw_query: str, symbols: list[str], file_mention: str | None
) -> tuple[str, str]:
    """Synthesize the ``query`` string actually handed to ``build_evidence()``.

    Free-text queries are frequently pure instruction ("이 함수 왜 바뀐 거야?")
    with the real signal living only in the attached ``selected_code`` — STEP 4's
    Git candidate search has no access to ``selected_code`` on its own, so this
    adapter must fold a strong signal (extracted function symbol, or a filename
    explicitly mentioned in the text) into ``query`` before Evidence search
    runs. Never touches STEP 4-7 scoring/ranking itself.

    ``history_added`` intent (언제/추가) only changes answer formatting — it must
    NOT inject ``언제``/``추가`` into the search query (those pull unrelated
    "추가" commits). Prefer ``{symbol} 변경 이력``.

    Returns ``(final_query_used, source)``.
    """
    normalized = normalize_query_text(raw_query)
    tokens = _tokenize(normalized)
    cleaned_tokens = [t for t in tokens if not _is_weak_or_instruction_token(t)]
    cleaned_query = " ".join(cleaned_tokens).strip()
    text_identifiers = extract_c_identifiers(normalized)
    query_intent = detect_query_intent(raw_query)

    if symbols:
        primary = symbols[0]
        leftover = [t for t in cleaned_tokens if t.lower() != primary.lower()]
        # Strip file basename tokens when a selected symbol is present — file_path
        # is passed separately as scope, not as a core search keyword.
        if file_mention:
            file_stem = PurePosixPath(file_mention.replace("\\", "/")).stem.lower()
            leftover = [
                t
                for t in leftover
                if file_mention.lower() not in t.lower() and t.lower() != file_stem
            ]
        # history_added: intent-only — do not append 언제/추가 as search keywords.
        if query_intent == "history_added" or not leftover:
            return f"{primary} 변경 이력", (
                "selected_code_symbol+history"
                if query_intent == "history_added"
                else "selected_code_symbol"
            )
        return f"{primary} {' '.join(leftover)}".strip(), "selected_code_symbol+query"

    # Query text identifiers beat file basename (Extension sends symbol in query).
    if text_identifiers:
        primary = text_identifiers[0]
        leftover = [t for t in cleaned_tokens if t.lower() != primary.lower()]
        if file_mention:
            file_stem = PurePosixPath(file_mention.replace("\\", "/")).stem.lower()
            leftover = [
                t
                for t in leftover
                if file_mention.lower() not in t.lower() and t.lower() != file_stem
            ]
        if query_intent == "history_added" or not leftover:
            return f"{primary} 변경 이력", (
                "query_identifier+history"
                if query_intent == "history_added"
                else "query_identifier"
            )
        return f"{primary} {' '.join(leftover)}".strip(), "query_identifier+query"

    if file_mention:
        leftover = [t for t in cleaned_tokens if file_mention.lower() not in t.lower()]
        if leftover:
            return f"{file_mention} {' '.join(leftover)}".strip(), "file_mention+query"
        return f"{file_mention} 변경 이력", "file_mention"

    if cleaned_query:
        return cleaned_query, "query_cleaned"

    return "", "missing_context"


def has_searchable_context(
    raw_query: str, symbols: list[str], file_mention: str | None
) -> bool:
    """True when the adapter has a concrete symbol/file/identifier to search on."""
    if symbols or file_mention:
        return True
    normalized = normalize_query_text(raw_query)
    if extract_c_identifiers(normalized):
        return True
    if extract_file_mention(normalized):
        return True
    tokens = _tokenize(normalized)
    return any(not _is_weak_or_instruction_token(t) for t in tokens)


_CONFIDENCE_LABELS = {"high": "높음", "medium": "보통", "low": "낮음"}


def _short_hash(commit: str | None) -> str:
    if not commit:
        return "(hash 없음)"
    return commit[:7] if len(commit) > 7 else commit


def _related_sources(
    evidence_result: EvidenceResult, *, primary_symbol: str | None = None
) -> list[str]:
    """Related source/function names from the Top Evidence Link only.

    When ``selected_symbol`` is set, that symbol is listed first and unrelated
    file-level functions (card_sc_decode 등) are not dumped.
    """
    items: list[str] = []
    try:
        if primary_symbol:
            items.append(primary_symbol)
        if evidence_result.evidence_links:
            top: EvidenceLink = evidence_result.evidence_links[0]
            for sf in _source_function_entries(top.change_item):
                for fn in sf.get("functions") or []:
                    if not fn:
                        continue
                    text = str(fn)
                    if primary_symbol and not _text_matches_symbol(text, primary_symbol):
                        continue
                    items.append(text)
            git = top.git_candidate
            if primary_symbol:
                if git_candidate_matches_symbol(git, primary_symbol):
                    file_path = getattr(git, "file_path", None)
                    if file_path:
                        items.append(file_path)
            else:
                file_path = getattr(git, "file_path", None)
                if file_path:
                    items.append(file_path)
        elif evidence_result.git_candidates and not primary_symbol:
            top_git: GitCandidate = evidence_result.git_candidates[0]
            if top_git.file_path:
                items.append(top_git.file_path)
    except Exception:
        return [primary_symbol] if primary_symbol else []

    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out[:5]


def _truncate_field(text: str | None, limit: int = 240) -> str | None:
    if text is None:
        return None
    cleaned = " ".join(str(text).split())
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def _summary_from_top_link(
    evidence_result: EvidenceResult,
    *,
    primary_symbol: str | None,
    fallback_summary: str | None,
) -> str:
    """Summary must come from Top Evidence Link — never raw candidates[0]."""
    try:
        if evidence_result.evidence_links:
            title = getattr(
                evidence_result.evidence_links[0].change_item, "change_title", None
            )
            title_text = _safe_text(title, "(제목 없음)")
            return f"가장 관련 높은 변경 항목은 `{title_text}`입니다."
        if primary_symbol:
            return (
                f"선택한 심볼 `{primary_symbol}`과 직접 연결된 변경 근거를 찾지 못했습니다."
            )
    except Exception:
        pass
    return fallback_summary or "확인 불가"


def _reason_from_top_link(
    evidence_result: EvidenceResult,
    *,
    primary_symbol: str | None,
    fallback_reason: str | None,
) -> str:
    """변경 이유/배경은 Top Evidence Link change item에서만 가져온다."""
    try:
        if not evidence_result.evidence_links:
            if primary_symbol:
                return "선택한 심볼과 직접 연결된 변경 이유를 확인하지 못했습니다."
            return fallback_reason or "근거 부족으로 확인할 수 없습니다."

        item = evidence_result.evidence_links[0].change_item
        parts: list[str] = []
        field_labels = (
            ("제목", "change_title"),
            ("업무 배경", "business_background"),
            ("현황", "current_status"),
            ("As-Is", "as_is"),
            ("To-Be", "to_be"),
        )
        for label, field in field_labels:
            value = _truncate_field(getattr(item, field, None))
            if value:
                parts.append(f"- {label}: {value}")
        if parts:
            return "\n".join(parts)
        return "해당 변경항목의 사유/상세 필드가 부족합니다."
    except Exception:
        return fallback_reason or "근거 부족으로 확인할 수 없습니다."


def _citations_from_top_link(
    evidence_result: EvidenceResult,
    fallback_refs: list[EvidenceRef],
) -> list[str]:
    """근거 섹션도 Top Evidence Link와 동일 출처만 사용."""
    try:
        if evidence_result.evidence_links:
            top = evidence_result.evidence_links[0]
            lines: list[str] = []
            commit = getattr(top.git_candidate, "commit_hash", None)
            if commit:
                lines.append(f"- Commit: {_short_hash(commit)}")
            file_name = getattr(top.change_item, "file_name", None) or getattr(
                top.change_item, "file_path", None
            )
            slide = getattr(top.change_item, "slide_no", None)
            title = getattr(top.change_item, "change_title", None)
            slide_text = f", Slide {slide}" if slide is not None else ""
            doc_label = file_name or title or "(문서명 없음)"
            lines.append(f"- 변경내역서: {doc_label}{slide_text}")
            return lines
    except Exception:
        pass
    return _citation_lines(fallback_refs or [])


def _citation_lines(evidence_refs: list[EvidenceRef]) -> list[str]:
    lines: list[str] = []
    for ref in evidence_refs:
        if ref.type == "git" and ref.commit:
            lines.append(f"- Commit: {_short_hash(ref.commit)}")
        elif ref.type == "document":
            slide = f", Slide {ref.slide}" if ref.slide is not None else ""
            lines.append(f"- 변경내역서: {ref.file or '(문서명 없음)'}{slide}")
    return lines


def _safe_text(value: object | None, fallback: str = "확인되지 않음") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


_PPT_DOC_DATE_RE = re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])")


def extract_document_baseline_date(file_name: str | None) -> str | None:
    """Parse YYYYMMDD from a change-document filename into ``YYYY-MM-DD``.

    Example: ``프로그램변경내역서_20210226_V221_휴대용정산기.pptx`` → ``2021-02-26``.
    """
    if not file_name:
        return None
    match = _PPT_DOC_DATE_RE.search(str(file_name))
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def lookup_git_commit_meta(
    *,
    commit_id: int | None = None,
    commit_hash: str | None = None,
) -> dict[str, str | None]:
    """Load commit_date / message from ``git_commit`` (read-only, no schema change)."""
    empty: dict[str, str | None] = {
        "commit_hash": None,
        "commit_date": None,
        "message": None,
    }
    if commit_id is None and not commit_hash:
        return empty
    try:
        from app.db.database import get_connection

        conn = get_connection()
        try:
            row = None
            if commit_id is not None:
                row = conn.execute(
                    """
                    SELECT commit_hash, commit_date, message
                    FROM git_commit
                    WHERE id = ?
                    """,
                    (commit_id,),
                ).fetchone()
            if row is None and commit_hash:
                row = conn.execute(
                    """
                    SELECT commit_hash, commit_date, message
                    FROM git_commit
                    WHERE commit_hash = ?
                       OR commit_hash LIKE ?
                    ORDER BY LENGTH(commit_hash) ASC
                    LIMIT 1
                    """,
                    (commit_hash, f"{commit_hash}%"),
                ).fetchone()
            if row is None:
                return empty
            return {
                "commit_hash": row["commit_hash"],
                "commit_date": row["commit_date"],
                "message": row["message"],
            }
        finally:
            conn.close()
    except Exception:
        return empty


def _enrich_top_link_git(git) -> dict[str, str | None]:
    """Prefer link fields; fill missing date/message from git_commit table."""
    commit_hash = getattr(git, "commit_hash", None) or None
    commit_id = getattr(git, "commit_id", None)
    commit_date = getattr(git, "commit_date", None) or None
    message = getattr(git, "message", None) or None

    need_lookup = bool(commit_hash or commit_id) and (
        not commit_date or not (message and str(message).strip())
    )
    if need_lookup:
        meta = lookup_git_commit_meta(
            commit_id=int(commit_id) if commit_id is not None else None,
            commit_hash=str(commit_hash) if commit_hash else None,
        )
        if not commit_hash and meta.get("commit_hash"):
            commit_hash = meta["commit_hash"]
        if not commit_date and meta.get("commit_date"):
            commit_date = meta["commit_date"]
        if (not message or not str(message).strip()) and meta.get("message"):
            message = meta["message"]

    return {
        "commit_hash": commit_hash,
        "commit_date": commit_date,
        "message": message,
    }


def resolve_history_evidence(
    evidence_result: EvidenceResult,
    *,
    primary_symbol: str | None,
) -> dict:
    """Build the history section from the same Top Evidence Link as summary/citations.

    Once links are symbol-filtered (or Top Link already qualifies), the paired
    Git Commit on that link is always shown — never hidden just because
    ``git_candidate_matches_symbol`` failed. Raw ``git_candidates[0]`` fallback
    remains forbidden.
    """
    debug: dict = {
        "history_source": "none",
        "history_commit_hash": None,
        "history_commit_date": None,
        "history_document_title": None,
        "history_document_baseline_date": None,
        "history_guard_reason": "no_evidence",
        "history_unrelated_candidate_skipped": 0,
        "history_git_lookup": False,
    }
    lines = ["", "### 추가/변경 시점"]

    try:
        links = list(evidence_result.evidence_links or [])
        skipped = 0
        for git in evidence_result.git_candidates or []:
            if primary_symbol and not git_candidate_matches_symbol(git, primary_symbol):
                skipped += 1
        debug["history_unrelated_candidate_skipped"] = skipped

        if not links:
            lines.append("- 정확한 최초 추가 시점은 확인되지 않음")
            debug["history_guard_reason"] = "no_evidence_links"
            return {"lines": lines, "debug": debug}

        matching = (
            [link for link in links if evidence_link_matches_symbol(link, primary_symbol)]
            if primary_symbol
            else list(links)
        )
        if primary_symbol and not matching:
            lines.append("- 선택한 심볼과 직접 연결된 변경내역서를 찾지 못했습니다.")
            lines.append("- 정확한 최초 추가 시점은 확인되지 않음")
            debug["history_guard_reason"] = "no_symbol_match"
            debug["history_source"] = "none"
            return {"lines": lines, "debug": debug}

        # Answer Top Evidence Link = matching[0] (already guard-ordered upstream).
        chosen = matching[0]
        item_ok = (
            change_item_matches_symbol(chosen.change_item, primary_symbol)
            if primary_symbol
            else True
        )
        git_ok = (
            git_candidate_matches_symbol(chosen.git_candidate, primary_symbol)
            if primary_symbol
            else True
        )
        if item_ok and git_ok:
            source = "evidence_link_top"
            guard_reason = "symbol_matched_both"
        elif item_ok:
            source = "evidence_link_top"
            guard_reason = "top_link_git_included"
        elif git_ok:
            source = "evidence_link_top"
            guard_reason = "git_symbol_matched"
        else:
            # Link still passed evidence_link_matches_symbol (e.g. link reasons).
            source = "evidence_link_top"
            guard_reason = "top_link_after_symbol_guard"

        title = _safe_text(getattr(chosen.change_item, "change_title", None), "확인되지 않음")
        slide = getattr(chosen.change_item, "slide_no", None)
        slide_text = f" (Slide {slide})" if slide is not None else ""
        debug["history_document_title"] = title if title != "확인되지 않음" else None
        debug["history_source"] = source
        debug["history_guard_reason"] = guard_reason

        git = chosen.git_candidate
        before_date = getattr(git, "commit_date", None)
        before_msg = getattr(git, "message", None)
        enriched = _enrich_top_link_git(git)
        commit_hash = enriched.get("commit_hash")
        commit_date = enriched.get("commit_date")
        message = enriched.get("message")
        debug["history_git_lookup"] = bool(
            (commit_date and not before_date)
            or (
                message
                and str(message).strip()
                and not (before_msg and str(before_msg).strip())
            )
        )
        debug["history_commit_hash"] = commit_hash
        debug["history_commit_date"] = commit_date

        if commit_hash:
            lines.append(f"- Commit: `{_short_hash(commit_hash)}`")
        else:
            lines.append("- Commit: 확인되지 않음")

        lines.append(f"- 날짜: {_safe_text(commit_date, '확인되지 않음')}")
        msg_text = _safe_text(message, "")
        lines.append(
            f"- Commit 메시지: {msg_text[:240]}"
            if msg_text
            else "- Commit 메시지: 확인되지 않음"
        )
        lines.append(f"- 관련 변경내역서: {title}{slide_text}")

        doc_name = getattr(chosen.change_item, "file_name", None) or getattr(
            chosen.change_item, "file_path", None
        )
        baseline = extract_document_baseline_date(
            str(doc_name) if doc_name else None
        )
        debug["history_document_baseline_date"] = baseline
        if baseline:
            lines.append(f"- 변경내역서 기준일: {baseline}")

        return {"lines": lines, "debug": debug}
    except Exception:
        lines.append("- 정확한 최초 추가 시점은 확인되지 않음")
        debug["history_guard_reason"] = "format_error"
        return {"lines": lines, "debug": debug}


def _history_evidence_lines(
    evidence_result: EvidenceResult,
    *,
    symbol_guard_applied: bool,
    primary_symbol: str | None,
) -> list[str]:
    """Backward-compatible wrapper — prefer ``resolve_history_evidence``. """
    _ = symbol_guard_applied
    return resolve_history_evidence(
        evidence_result, primary_symbol=primary_symbol
    )["lines"]


def _query_meta_footer(*existing_parts: str) -> list[str]:
    """Concise trailing meta line — actual query time, no AI-usage wording.

    AI 보조 설명(Ollama) 사용 여부는 더 이상 사용자 Markdown에 표시하지 않는다
    (Backend 분석 로직·API 필드는 그대로 유지 — 표시만 생략).
    Skips when the body already ends with a Backend lifecycle ``조회:`` footer.
    """
    blob = "\n".join(str(p) for p in existing_parts if p)
    if re.search(r"(?m)^조회:\s*\d{4}-\d{2}-\d{2}", blob):
        return []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return ["", "---", f"조회: {timestamp}"]


def build_markdown_answer(
    evidence_result: EvidenceResult,
    result: OllamaAnalysisResult,
    *,
    use_ollama: bool,
    query_intent: str = "general",
    primary_symbol: str | None = None,
    symbol_guard_applied: bool = False,
    file_path: str | None = None,
) -> tuple[str, dict]:
    """Render the Extension's official Markdown answer. Returns ``(markdown, history_debug)``.

    When ``primary_symbol`` is set, Git function lifecycle (all related commits
    chronologically) drives the answer. PPT Evidence Links are enrichment only —
    never the sole filter that drops Git-only or creation commits.
    """
    _ = symbol_guard_applied
    history_debug: dict = {}
    try:
        lifecycle = None
        if primary_symbol:
            try:
                from app.services.function_git_lifecycle_service import (
                    resolve_function_git_lifecycle,
                )

                lifecycle = resolve_function_git_lifecycle(
                    evidence_result,
                    primary_symbol,
                    file_path=file_path,
                )
                history_debug.update(lifecycle.debug or {})
            except Exception as exc:
                history_debug["function_lifecycle_error"] = type(exc).__name__
                lifecycle = None

        if lifecycle and lifecycle.entries:
            history_debug["history_source"] = "function_git_lifecycle"
            history_debug["analyzed_symbol"] = primary_symbol
            if lifecycle.creation:
                history_debug["history_commit_hash"] = lifecycle.creation.commit_hash
                history_debug["history_commit_date"] = lifecycle.creation.commit_date
                history_debug["history_guard_reason"] = lifecycle.creation.change_type
            elif lifecycle.entries:
                history_debug["history_commit_hash"] = lifecycle.entries[0].commit_hash
                history_debug["history_commit_date"] = lifecycle.entries[0].commit_date
                history_debug["history_guard_reason"] = "function_timeline_first"

            lines = [lifecycle.document_text, *_query_meta_footer(lifecycle.document_text)]
            markdown = "\n".join(lines).strip()
            history_debug["_lifecycle"] = lifecycle
            return markdown, history_debug
        else:
            history_debug.setdefault("analyzed_symbol", primary_symbol)
            summary = _summary_from_top_link(
                evidence_result,
                primary_symbol=primary_symbol,
                fallback_summary=result.evidence_summary or result.evidence_answer,
            )
            lines = ["## 변경 이력 분석 결과", "", "### 요약", summary]

            if query_intent == "history_added" or primary_symbol:
                try:
                    resolved = resolve_history_evidence(
                        evidence_result, primary_symbol=primary_symbol
                    )
                    lines.extend(resolved["lines"])
                    history_debug.update(resolved["debug"] or {})
                except Exception:
                    lines += [
                        "",
                        "### 추가/변경 시점",
                        "- 정확한 최초 추가 시점은 확인되지 않음",
                    ]
                    history_debug.setdefault("history_source", "none")
                    history_debug.setdefault("history_guard_reason", "format_error")

        # PPT enrichment (Top Link) — separate from Git timeline.
        reason = _reason_from_top_link(
            evidence_result,
            primary_symbol=primary_symbol,
            fallback_reason=result.evidence_reason,
        )
        lines += ["", "### 변경 이유 / 배경 (변경내역서 보강)"]
        if lifecycle and lifecycle.entries and not any(
            e.ppt_link_level == "direct" for e in lifecycle.entries
        ):
            lines.append("연결된 변경내역서 직접 근거 없음. Git Diff 이력만 확인되었습니다.")
        else:
            lines.append(reason)

        sources = _related_sources(evidence_result, primary_symbol=primary_symbol)
        lines += ["", "### 관련 소스/함수"]
        lines += [f"- {s}" for s in sources] if sources else ["- 없음"]

        if lifecycle and lifecycle.citation_lines:
            citation_lines = lifecycle.citation_lines
        else:
            citation_lines = _citations_from_top_link(
                evidence_result, result.evidence_refs or []
            )
        lines += ["", "### 참조 근거"]
        lines += citation_lines if citation_lines else ["- 없음"]

        if lifecycle and lifecycle.entries:
            confidence = lifecycle.overall_confidence or "low"
            conf_label = lifecycle.overall_confidence_label or _CONFIDENCE_LABELS.get(
                confidence, confidence
            )
            lines += ["", "### 신뢰도", conf_label]
            high_n = sum(1 for e in lifecycle.entries if e.confidence == "high")
            low_n = sum(1 for e in lifecycle.entries if e.confidence == "low")
            lines.append(
                f"- 사유: {len(lifecycle.entries)}건 중 핵심 "
                f"{sum(1 for e in lifecycle.entries if e.is_core)}건, "
                f"높음 {high_n}건 / 낮음 {low_n}건"
            )
        else:
            confidence = result.confidence or "low"
            lines += ["", "### 신뢰도", _CONFIDENCE_LABELS.get(confidence, confidence)]

        lines += _query_meta_footer(*lines)
        history_debug.setdefault("analyzed_symbol", primary_symbol)

        markdown = "\n".join("" if line is None else str(line) for line in lines).strip()
        return markdown, history_debug
    except Exception:
        fallback = (
            result.evidence_answer
            or result.evidence_summary
            or "변경 이력 분석 결과를 표시하는 중 오류가 발생했습니다. "
            "서버 근거는 조회되었으나 요약 포맷에 실패했습니다."
        )
        return f"## 변경 이력 분석 결과\n\n### 요약\n{fallback}", history_debug
