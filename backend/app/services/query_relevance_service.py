"""Evidence-only query intent + relevance (STEP 7).

Separates Query Relevance from Link Strength. Does NOT change STEP 4/6
keyword_extractor stopwords or Link Score weights.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from app.schemas.trace import GitCandidate
from app.services.change_item_candidate_service import ChangeItemCandidate

# Intent / filler terms — strong Query Relevance must not rely on these alone.
# Includes request phrasings ("보여줘", "내역") and conjugated/particle forms
# handled by _is_stopword prefix rules.
EVIDENCE_QUERY_STOPWORDS = frozenset(
    {
        "변경",
        "변경사항",
        "변경사항을",
        "변경이유",
        "변경이력",
        "변경이력을",
        "변경내역",
        "변경내역을",
        "관련",
        "이유",
        "뭐야",
        "무엇",
        "왜",
        "함수",
        "소스",
        "내용",
        "내용을",
        "사항",
        "사항을",
        "내역",
        "내역을",
        "이력",
        "이력을",
        "목록",
        "목록을",
        "보자",
        "보자고",
        "보여",
        "보여줘",
        "보여줘요",
        "알려",
        "알려줘",
        "알려줘요",
        "찾아",
        "찾아줘",
        "찾아줘요",
        "확인해줘",
        "주세요",
        "해줘",
        "해줘요",
        "줘",
        "좀",
        "대한",
        "대해",
        "관한",
        "요청",
        "검색",
        "조회",
        "확인",
        "설명",
        "change",
        "changes",
        "changed",
        "related",
        "regarding",
        "about",
        "reason",
        "why",
        "what",
        "how",
        "function",
        "functions",
        "show",
        "please",
        "tell",
        "the",
        "and",
        "for",
    }
)

_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_UPPER_SYMBOL_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
_KOREAN_RE = re.compile(r"[가-힣]{2,}")
_DIGIT_KO_RE = re.compile(r"\d+[가-힣]+|[가-힣]+\d+")
_FILE_IN_QUERY_RE = re.compile(
    r"\b[\w.-]+\.(?:c|h|cpp|hpp|cc|cxx|py|js|ts|java|md|txt)\b", re.IGNORECASE
)
_CODE_FILE_EXTS = frozenset(
    {".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".py", ".js", ".ts", ".java", ".md", ".txt"}
)

# Generic directory segments — never use as Query Relevance core keywords
# when derived from a directory path. File stems (e.g. card.c → card) remain allowed.
GENERIC_PATH_SEGMENTS = frozenset(
    {
        "src",
        "source",
        "lib",
        "common",
        "include",
        "inc",
        "proc",
        "app",
        "device",
        "card",
        "fare",
        "util",
        "utils",
        "api",
        "test",
        "tests",
        "bin",
        "obj",
        "build",
        "tmp",
        "temp",
        "docs",
        "doc",
        "data",
        "cfg",
        "config",
        "scripts",
        "script",
        "main",
        "public",
        "private",
        "internal",
        "external",
        "third_party",
        "vendor",
        "node_modules",
    }
)

# Same keyword may match many fields; cap prevents directory/noise flood.
_KEYWORD_CORE_SCORE_CAP = 50

# Display / ranking weights for Query Relevance (independent of LINK_SCORE_CONFIG).
_FIELD_SCORE = {
    "change_title": 40,
    "to_be": 30,
    "as_is": 25,
    "business_background": 25,
    "current_status": 20,
    "csr_no": 20,
    "source_function": 40,
    "file_name": 15,
    "raw_text": 10,
    "commit_message": 35,
    "git_file_path": 30,
    "selected_code": 40,
    "request_file_path": 40,
    "path_scope": 5,  # directory scope hint only (weak)
}

_SNIPPET_MAX = 80


@dataclass
class QueryMatchReason:
    keyword: str
    field: str
    value: str
    score: int
    strength: str = "core"  # core | weak


@dataclass
class ParsedFilePathInput:
    """Result of classifying Evidence file_path input."""

    is_file: bool
    request_files: list[str] = field(default_factory=list)
    path_scope: str | None = None


@dataclass
class QueryIntent:
    """Evidence query intent classification (display + relevance matching).

    - query_keywords: core business/topic terms from the query text
    - request_functions: C-style identifiers / function names from query or selected_code
    - request_files: basename/stem from a *file* path (not directory segments)
    - path_scopes: directory search-range hints (display / weak only)
    - weak_query_terms: filler / request phrasings (not core search intent)
    """

    query_keywords: list[str] = field(default_factory=list)
    weak_query_terms: list[str] = field(default_factory=list)
    request_functions: list[str] = field(default_factory=list)
    request_files: list[str] = field(default_factory=list)
    path_scopes: list[str] = field(default_factory=list)


@dataclass
class QueryRelevanceResult:
    score: int
    level: str  # 높음 | 보통 | 낮음 | 없음
    match_reasons: list[QueryMatchReason] = field(default_factory=list)
    has_core_match: bool = False
    passes_gate: bool = False


def _norm(text: str | None) -> str:
    return (text or "").strip().lower()


def _is_stopword(token: str) -> bool:
    t = token.strip()
    if not t:
        return True
    tl = t.lower()
    if tl in EVIDENCE_QUERY_STOPWORDS or t in EVIDENCE_QUERY_STOPWORDS:
        return True
    # Korean conjugated / particle forms: "함수가", "변경됐어", "내역을", "보여줘요"
    for sw in EVIDENCE_QUERY_STOPWORDS:
        swl = sw.lower()
        if len(swl) < 2:
            # Single-char terms (e.g. 왜 / 줘): exact match only
            continue
        if tl.startswith(swl) and len(tl) <= len(swl) + 4:
            return True
    return False


def _is_function_like_token(token: str) -> bool:
    """C identifier / symbol shape — not plain English topic words like 'receipt'."""
    if not token or _is_stopword(token):
        return False
    if _FILE_IN_QUERY_RE.fullmatch(token):
        return False
    if not _IDENTIFIER_RE.fullmatch(token):
        return False
    if "_" in token:
        return True
    if token.isupper() and len(token) >= 3:
        return True
    # CamelCase / PascalCase
    if any(c.isupper() for c in token[1:]):
        return True
    return False


def _is_file_token(token: str) -> bool:
    return bool(_FILE_IN_QUERY_RE.fullmatch(token))


def _collect_raw_tokens(query: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        token = token.strip()
        if not token or len(token) < 2:
            return
        key = token.lower()
        if key in seen:
            return
        seen.add(key)
        found.append(token)

    for token in _DIGIT_KO_RE.findall(query):
        add(token)
    for token in _IDENTIFIER_RE.findall(query):
        add(token)
    for token in _UPPER_SYMBOL_RE.findall(query):
        add(token)
    for token in _KOREAN_RE.findall(query):
        add(token)
    for token in _FILE_IN_QUERY_RE.findall(query):
        add(token)
    return found


def _append_unique(target: list[str], seen: set[str], token: str) -> None:
    key = token.lower()
    if not token or key in seen:
        return
    seen.add(key)
    target.append(token)


def _normalize_path_text(path: str) -> str:
    return path.replace("\\", "/").strip()


def parse_file_path_input(file_path: str | None) -> ParsedFilePathInput:
    """Distinguish file path vs directory path for Evidence file_path input.

    Directory paths (trailing slash, or no code extension) yield path_scope only.
    File paths yield request_files (name + stem) and optional parent as path_scope.
    """
    if not file_path or not str(file_path).strip():
        return ParsedFilePathInput(is_file=False)

    raw = _normalize_path_text(str(file_path))
    trailing_slash = raw.endswith("/")
    cleaned = raw.rstrip("/")
    if not cleaned:
        return ParsedFilePathInput(is_file=False)

    path = PurePosixPath(cleaned)
    name = path.name
    suffix = path.suffix.lower()

    if not trailing_slash and suffix in _CODE_FILE_EXTS:
        files: list[str] = [name]
        stem = path.stem
        if stem and stem.lower() != name.lower():
            files.append(stem)
        parent = str(path.parent).replace("\\", "/")
        scope = parent if parent not in {"", ".", "/"} else None
        return ParsedFilePathInput(is_file=True, request_files=files, path_scope=scope)

    # Directory (or non-file path): never promote last segment (e.g. src) to request file
    return ParsedFilePathInput(is_file=False, request_files=[], path_scope=cleaned)


def core_match_keywords(intent: QueryIntent) -> list[str]:
    """All core tokens used for Query Relevance matching (not display-only)."""
    out: list[str] = []
    seen: set[str] = set()
    for token in [
        *intent.query_keywords,
        *intent.request_functions,
        *intent.request_files,
    ]:
        if token.lower() in GENERIC_PATH_SEGMENTS:
            # Guard: never use bare directory generics as core even if leaked.
            continue
        _append_unique(out, seen, token)
    return out


def split_evidence_query_intent(
    query: str,
    file_path: str | None = None,
    selected_code: str | None = None,
) -> QueryIntent:
    """Classify query tokens for Evidence ranking / display only (not STEP 4/6)."""
    business: list[str] = []
    functions: list[str] = []
    files: list[str] = []
    scopes: list[str] = []
    weak: list[str] = []
    seen_business: set[str] = set()
    seen_functions: set[str] = set()
    seen_files: set[str] = set()
    seen_scopes: set[str] = set()
    seen_weak: set[str] = set()

    for token in _collect_raw_tokens(query or ""):
        if _is_stopword(token):
            _append_unique(weak, seen_weak, token)
            continue
        if _is_file_token(token):
            _append_unique(files, seen_files, token)
            stem = PurePosixPath(token).stem
            if stem and stem.lower() != token.lower():
                _append_unique(files, seen_files, stem)
            continue
        if _is_function_like_token(token):
            _append_unique(functions, seen_functions, token)
            continue
        if token.lower() in GENERIC_PATH_SEGMENTS:
            # Bare generic segment in free text is not a business core keyword.
            _append_unique(weak, seen_weak, token)
            continue
        _append_unique(business, seen_business, token)

    parsed = parse_file_path_input(file_path)
    for token in parsed.request_files:
        _append_unique(files, seen_files, token)
    if parsed.path_scope:
        _append_unique(scopes, seen_scopes, parsed.path_scope)

    if selected_code:
        for token in _IDENTIFIER_RE.findall(selected_code):
            if len(token) < 3 and not token[0].isupper():
                continue
            if _is_stopword(token):
                continue
            if _is_function_like_token(token) or _IDENTIFIER_RE.fullmatch(token):
                _append_unique(functions, seen_functions, token)

    return QueryIntent(
        query_keywords=business,
        weak_query_terms=weak,
        request_functions=functions,
        request_files=files,
        path_scopes=scopes,
    )


def _snippet(text: str, keyword: str) -> str:
    text = " ".join(text.split())
    if len(text) <= _SNIPPET_MAX:
        return text
    lower = text.lower()
    idx = lower.find(keyword.lower())
    if idx < 0:
        return text[: _SNIPPET_MAX - 1] + "…"
    start = max(0, idx - 20)
    end = min(len(text), start + _SNIPPET_MAX)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def _keyword_in_text(keyword: str, text: str | None) -> bool:
    if not text:
        return False
    return _norm(keyword) in _norm(text)


def _level_for_score(score: int, has_core: bool) -> str:
    if score <= 0:
        return "없음"
    if not has_core:
        return "낮음"
    if score >= 40:
        return "높음"
    if score >= 20:
        return "보통"
    return "낮음"


def _match_fields(
    keywords: list[str],
    fields: list[tuple[str, str | None]],
    *,
    strength: str,
) -> list[QueryMatchReason]:
    reasons: list[QueryMatchReason] = []
    seen: set[tuple[str, str]] = set()
    for keyword in keywords:
        for field_name, value in fields:
            if not _keyword_in_text(keyword, value):
                continue
            key = (keyword.lower(), field_name)
            if key in seen:
                continue
            seen.add(key)
            reasons.append(
                QueryMatchReason(
                    keyword=keyword,
                    field=field_name,
                    value=_snippet(value or "", keyword),
                    score=_FIELD_SCORE.get(field_name, 10),
                    strength=strength,
                )
            )
    return reasons


def evaluate_git_query_relevance(
    git: GitCandidate,
    intent: QueryIntent,
    *,
    request_file_path: str | None = None,
    selected_code: str | None = None,
) -> QueryRelevanceResult:
    fields = [
        ("commit_message", git.message),
        ("git_file_path", git.file_path),
    ]
    reasons = _match_fields(core_match_keywords(intent), fields, strength="core")
    reasons.extend(_match_fields(intent.weak_query_terms, fields, strength="weak"))

    parsed = parse_file_path_input(request_file_path)
    # File path: strong core match when Git file matches requested file.
    if parsed.is_file and request_file_path and _paths_match(request_file_path, git.file_path):
        keyword = PurePosixPath(_normalize_path_text(request_file_path)).name
        reasons.append(
            QueryMatchReason(
                keyword=keyword,
                field="request_file_path",
                value=_snippet(git.file_path, keyword),
                score=_FIELD_SCORE["request_file_path"],
                strength="core",
            )
        )
    # Directory path: weak scope hint only — must not drive Query Match 높음.
    elif parsed.path_scope:
        git_norm = _normalize_path_text(git.file_path).lower()
        scope_norm = parsed.path_scope.lower().rstrip("/")
        if scope_norm and scope_norm in git_norm:
            reasons.append(
                QueryMatchReason(
                    keyword=parsed.path_scope,
                    field="path_scope",
                    value=_snippet(git.file_path, PurePosixPath(scope_norm).name),
                    score=_FIELD_SCORE["path_scope"],
                    strength="weak",
                )
            )

    if selected_code:
        for token in _IDENTIFIER_RE.findall(selected_code):
            if len(token) < 3:
                continue
            if _keyword_in_text(token, git.message) or _keyword_in_text(token, git.file_path):
                reasons.append(
                    QueryMatchReason(
                        keyword=token,
                        field="selected_code",
                        value=_snippet(git.message or git.file_path, token),
                        score=_FIELD_SCORE["selected_code"],
                        strength="core",
                    )
                )
                break

    return _finalize_relevance(reasons, intent)


def evaluate_change_item_query_relevance(
    item: ChangeItemCandidate,
    intent: QueryIntent,
    *,
    request_file_path: str | None = None,
    selected_code: str | None = None,
) -> QueryRelevanceResult:
    source_text_parts: list[str] = []
    for entry in item.source_functions or []:
        if entry.get("raw_text"):
            source_text_parts.append(str(entry["raw_text"]))
        if entry.get("file_path"):
            source_text_parts.append(str(entry["file_path"]))
        for fn in entry.get("functions") or []:
            source_text_parts.append(str(fn))
    source_blob = " ".join(source_text_parts)

    fields = [
        ("change_title", item.change_title),
        ("to_be", item.to_be),
        ("as_is", item.as_is),
        ("business_background", item.business_background),
        ("current_status", item.current_status),
        ("csr_no", item.csr_no),
        ("source_function", source_blob or None),
        ("file_name", item.file_name),
        ("raw_text", item.raw_text),
    ]
    reasons = _match_fields(core_match_keywords(intent), fields, strength="core")
    reasons.extend(_match_fields(intent.weak_query_terms, fields, strength="weak"))

    parsed = parse_file_path_input(request_file_path)
    if parsed.is_file and request_file_path:
        req_name = PurePosixPath(_normalize_path_text(request_file_path)).name
        req_stem = PurePosixPath(_normalize_path_text(request_file_path)).stem
        for entry in item.source_functions or []:
            sf_path = str(entry.get("file_path") or "")
            if _paths_match(request_file_path, sf_path):
                reasons.append(
                    QueryMatchReason(
                        keyword=req_name,
                        field="request_file_path",
                        value=_snippet(sf_path, req_name),
                        score=_FIELD_SCORE["request_file_path"],
                        strength="core",
                    )
                )
                break
            if req_stem and req_stem.lower() not in GENERIC_PATH_SEGMENTS and _keyword_in_text(
                req_stem, sf_path
            ):
                reasons.append(
                    QueryMatchReason(
                        keyword=req_stem,
                        field="request_file_path",
                        value=_snippet(sf_path, req_stem),
                        score=_FIELD_SCORE["request_file_path"],
                        strength="core",
                    )
                )
                break
    elif parsed.path_scope:
        scope_norm = parsed.path_scope.lower().rstrip("/")
        for entry in item.source_functions or []:
            sf_path = str(entry.get("file_path") or "")
            if scope_norm and scope_norm in _normalize_path_text(sf_path).lower():
                reasons.append(
                    QueryMatchReason(
                        keyword=parsed.path_scope,
                        field="path_scope",
                        value=_snippet(sf_path, PurePosixPath(scope_norm).name),
                        score=_FIELD_SCORE["path_scope"],
                        strength="weak",
                    )
                )
                break

    if selected_code:
        for token in _IDENTIFIER_RE.findall(selected_code):
            if len(token) < 3:
                continue
            if _keyword_in_text(token, source_blob) or _keyword_in_text(
                token, item.change_title
            ):
                reasons.append(
                    QueryMatchReason(
                        keyword=token,
                        field="selected_code",
                        value=_snippet(source_blob or item.change_title or "", token),
                        score=_FIELD_SCORE["selected_code"],
                        strength="core",
                    )
                )
                break

    return _finalize_relevance(reasons, intent)


def evaluate_link_query_relevance(
    git: GitCandidate,
    item: ChangeItemCandidate,
    intent: QueryIntent,
    *,
    request_file_path: str | None = None,
    selected_code: str | None = None,
) -> QueryRelevanceResult:
    git_rel = evaluate_git_query_relevance(
        git,
        intent,
        request_file_path=request_file_path,
        selected_code=selected_code,
    )
    ci_rel = evaluate_change_item_query_relevance(
        item,
        intent,
        request_file_path=request_file_path,
        selected_code=selected_code,
    )
    # Deduplicate reasons by (keyword, field, strength).
    merged: list[QueryMatchReason] = []
    seen: set[tuple[str, str, str]] = set()
    for reason in [*git_rel.match_reasons, *ci_rel.match_reasons]:
        key = (reason.keyword.lower(), reason.field, reason.strength)
        if key in seen:
            continue
        seen.add(key)
        merged.append(reason)
    return _finalize_relevance(merged, intent)


def _paths_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    a = left.replace("\\", "/").lower()
    b = right.replace("\\", "/").lower()
    if a == b:
        return True
    return PurePosixPath(a).name == PurePosixPath(b).name


def _is_valid_core_keyword(keyword: str) -> bool:
    key = keyword.strip().lower()
    if not key:
        return False
    if key in GENERIC_PATH_SEGMENTS:
        return False
    return True


def _score_core_reasons_with_cap(reasons: list[QueryMatchReason]) -> tuple[int, bool]:
    """Sum core scores with per-keyword cap; ignore generic path-segment keywords."""
    used: dict[str, int] = {}
    total = 0
    has_core = False
    for reason in reasons:
        if reason.strength != "core":
            continue
        if not _is_valid_core_keyword(reason.keyword):
            continue
        has_core = True
        key = reason.keyword.lower()
        already = used.get(key, 0)
        add = min(reason.score, max(0, _KEYWORD_CORE_SCORE_CAP - already))
        if add <= 0:
            continue
        used[key] = already + add
        total += add
    return total, has_core


def _finalize_relevance(
    reasons: list[QueryMatchReason], intent: QueryIntent
) -> QueryRelevanceResult:
    # Drop accidental core matches on generic path segments from the visible list.
    cleaned: list[QueryMatchReason] = []
    for reason in reasons:
        if reason.strength == "core" and not _is_valid_core_keyword(reason.keyword):
            continue
        cleaned.append(reason)

    score, has_core = _score_core_reasons_with_cap(cleaned)
    if not has_core:
        weak_score = sum(r.score for r in cleaned if r.strength == "weak")
        score = min(weak_score, 15)

    # Gate: at least one real core keyword/context match.
    passes_gate = has_core
    if not core_match_keywords(intent) and not has_core:
        passes_gate = False

    return QueryRelevanceResult(
        score=score,
        level=_level_for_score(score, has_core),
        match_reasons=cleaned,
        has_core_match=has_core,
        passes_gate=passes_gate,
    )
