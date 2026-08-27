"""PPT ↔ function lifecycle linking (phase- and action-aware).

Evidence Link scoring is unchanged. This module only decides how change-item
documents attach to lifecycle entries after Git classification.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

from app.services.source_path_utils import PathMatchLevel, source_path_match_level
from app.services.symbol_utils import is_valid_symbol, normalize_symbol, symbols_equivalent

_PPT_DOC_DATE_RE = re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])")
_VERSION_RE = re.compile(r"V\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
_FILE_PATH_RE = re.compile(
    r"(?i)(?:[A-Za-z]:)?(?:[/\\][\w.\-]+)+\.(?:c|h|cpp|hpp|cc|cxx)\b|"
    r"(?:[\w.\-]+[/\\])+[\w.\-]+\.(?:c|h|cpp|hpp|cc|cxx)\b"
)
_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]+")

# Change-action buckets (not hardcoded to a specific feature).
_ACTION_APPLY_RE = re.compile(
    r"적용|추가|도입|신규|신설|지원\s*추가|기능\s*추가", re.IGNORECASE
)
_ACTION_MODIFY_RE = re.compile(
    r"수정|보완|변경|개선|판정|설정\s*변경|조건\s*변경", re.IGNORECASE
)
_ACTION_DELETE_RE = re.compile(
    r"삭제|제거|폐기|비교\s*로직\s*삭제|하드코딩\s*(삭제|제거)", re.IGNORECASE
)
_ACTION_LOG_RE = re.compile(r"로그|printf|디버그|테스트\s*로그|주석", re.IGNORECASE)

ACTION_APPLY = "apply"
ACTION_MODIFY = "modify"
ACTION_DELETE = "delete"
ACTION_LOG = "log"
ACTION_UNKNOWN = "unknown"

LINK_COMMIT_DIRECT = "commit_direct"
LINK_FEATURE_RELEASE = "feature_release"
LINK_DEV_REFERENCE = "development_reference"
LINK_MAINTENANCE = "maintenance_reference"
LINK_RELATED = "related_reference"

# User-facing connection strength (§11.1). Internal LINK_* enums are unchanged.
STRENGTH_COMMIT_DIRECT = "commit_direct"
STRENGTH_STAGE = "stage_link"
STRENGTH_RELATED = "related_ref"

_STRENGTH_LABEL = {
    STRENGTH_COMMIT_DIRECT: "Commit 직접 근거",
    STRENGTH_STAGE: "단계 연결 근거",
    STRENGTH_RELATED: "관련 참고",
}

# Map internal link enums → connection strength (display / aggregation only).
_LINK_TO_STRENGTH = {
    LINK_COMMIT_DIRECT: STRENGTH_COMMIT_DIRECT,
    LINK_FEATURE_RELEASE: STRENGTH_STAGE,
    LINK_DEV_REFERENCE: STRENGTH_RELATED,
    LINK_MAINTENANCE: STRENGTH_RELATED,
    LINK_RELATED: STRENGTH_RELATED,
}

_LINK_TYPE_USER = {
    LINK_COMMIT_DIRECT: _STRENGTH_LABEL[STRENGTH_COMMIT_DIRECT],
    LINK_FEATURE_RELEASE: _STRENGTH_LABEL[STRENGTH_STAGE],
    LINK_DEV_REFERENCE: _STRENGTH_LABEL[STRENGTH_RELATED],
    LINK_MAINTENANCE: _STRENGTH_LABEL[STRENGTH_RELATED],
    LINK_RELATED: _STRENGTH_LABEL[STRENGTH_RELATED],
}

# Creation / early feature commits must not take delete/maintenance docs as release proof.
_CORE_INTRO_TYPES = frozenset(
    {
        "function_creation",
        "function_creation_estimated",
        "card_type_setting",
        "body_change",
        "branch_change",
        "signature_change",
        "return_handling_change",
    }
)
_MAINT_TYPES = frozenset({"date_logic_change", "function_deletion"})


@dataclass
class PptLink:
    document_name: str | None = None
    slide_number: int | None = None
    change_title: str | None = None
    link_type: str = LINK_RELATED
    link_reason_user: str = ""
    linked_commit_hashes: list[str] = field(default_factory=list)
    related_symbols: list[str] = field(default_factory=list)
    related_source_paths: list[str] = field(default_factory=list)
    confidence: str = "medium"
    csr_no: str | None = None
    business_background: str | None = None
    to_be: str | None = None
    as_is: str | None = None
    document_path: str | None = None
    document_date: str | None = None
    versions: list[str] = field(default_factory=list)
    change_action: str = ACTION_UNKNOWN
    phase: str = "development"  # development | maintenance
    change_item_cache_id: int | None = None
    equipment_id: int | None = None

    @property
    def link_type_label(self) -> str:
        return connection_strength_label(self.link_type)

    def identity_key(self) -> str:
        """Document identity — never commit hash. Equipment-scoped."""
        return (
            f"{self.equipment_id if self.equipment_id is not None else ''}|"
            f"{self.change_item_cache_id if self.change_item_cache_id is not None else ''}|"
            f"{(self.document_path or self.document_name or '').replace(chr(92), '/').lower()}|"
            f"{self.slide_number}|{self.change_title or ''}"
        )


def ppt_link_type_user_label(link_type: str) -> str:
    return connection_strength_label(link_type)


def connection_strength(link_type: str | None) -> str:
    """Normalize internal LINK_* to §11.1 connection strength."""
    if not link_type:
        return STRENGTH_RELATED
    return _LINK_TO_STRENGTH.get(link_type, STRENGTH_RELATED)


def connection_strength_label(link_type: str | None) -> str:
    return _STRENGTH_LABEL.get(connection_strength(link_type), "관련 참고")


def strength_rank(strength: str) -> int:
    return {
        STRENGTH_COMMIT_DIRECT: 3,
        STRENGTH_STAGE: 2,
        STRENGTH_RELATED: 1,
    }.get(strength, 0)


def strongest_link_type(*link_types: str | None) -> str:
    """Pick the strongest internal link_type among candidates."""
    best = LINK_RELATED
    best_rank = -1
    for lt in link_types:
        if not lt:
            continue
        r = strength_rank(connection_strength(lt))
        if r > best_rank:
            best = lt
            best_rank = r
    return best


def extract_document_date(file_name: str | None) -> str | None:
    if not file_name:
        return None
    match = _PPT_DOC_DATE_RE.search(str(file_name))
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"


def extract_versions(*texts: str | None) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for m in _VERSION_RE.finditer(text):
            ver = f"V{m.group(1)}"
            key = ver.lower()
            if key not in seen:
                seen.add(key)
                found.append(ver)
    return found


def classify_change_action(*texts: str | None) -> str:
    blob = " ".join(t for t in texts if t) or ""
    if not blob.strip():
        return ACTION_UNKNOWN
    # Delete beats apply when both appear (e.g. "날짜비교 로직 삭제").
    if _ACTION_DELETE_RE.search(blob):
        return ACTION_DELETE
    if _ACTION_LOG_RE.search(blob) and not _ACTION_APPLY_RE.search(blob):
        return ACTION_LOG
    if _ACTION_APPLY_RE.search(blob):
        return ACTION_APPLY
    if _ACTION_MODIFY_RE.search(blob):
        return ACTION_MODIFY
    return ACTION_UNKNOWN


def commit_change_action(change_type: str, message: str | None) -> str:
    if change_type == "comment_or_log":
        return ACTION_LOG
    if change_type in {"function_creation", "function_creation_estimated"}:
        return ACTION_APPLY
    if change_type in {"date_logic_change", "function_deletion"}:
        # Prefer message if it clearly says delete/remove.
        msg_action = classify_change_action(message)
        return msg_action if msg_action == ACTION_DELETE else ACTION_DELETE
    if change_type in {"card_type_setting", "body_change", "branch_change"}:
        msg_action = classify_change_action(message)
        if msg_action in {ACTION_APPLY, ACTION_MODIFY, ACTION_DELETE}:
            return msg_action
        return ACTION_MODIFY
    return classify_change_action(message)


def actions_compatible(doc_action: str, commit_action: str, change_type: str) -> bool:
    """Opposite actions must not form direct/feature-release links."""
    if doc_action == ACTION_UNKNOWN or commit_action == ACTION_UNKNOWN:
        return True
    if doc_action == ACTION_DELETE and commit_action in {ACTION_APPLY, ACTION_MODIFY}:
        if change_type in _CORE_INTRO_TYPES:
            return False
    if doc_action in {ACTION_APPLY, ACTION_MODIFY} and commit_action == ACTION_DELETE:
        if change_type in _MAINT_TYPES or commit_action == ACTION_DELETE:
            # apply-doc to delete-commit is weak; disallow as release proof
            if doc_action == ACTION_APPLY:
                return False
    if doc_action == ACTION_DELETE and commit_action == ACTION_LOG:
        return False
    if doc_action in {ACTION_APPLY, ACTION_MODIFY} and commit_action == ACTION_LOG:
        return True  # allowed only as development_reference (caller enforces)
    return True


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def date_delta_days(commit_date: str | None, doc_date: str | None) -> int | None:
    c = _parse_date(commit_date)
    d = _parse_date(doc_date)
    if not c or not d:
        return None
    return abs((c - d).days)


def time_compatible(
    commit_date: str | None,
    doc_date: str | None,
    *,
    doc_action: str,
    change_type: str,
) -> tuple[bool, str]:
    """Return (always_ok, band) where band is near|mid|far|unknown.

    PROJECT_SPEC v2.4 §11.5 — date distance is never a mandatory dropout for
  linking. ``time_band`` is used only for candidate ordering, confidence
  hints, and user-facing caution text. Action/type contradictions are
  handled separately via ``actions_compatible`` and explicit evidence gates.
    """
    _ = (doc_action, change_type)
    delta = date_delta_days(commit_date, doc_date)
    if delta is None:
        return True, "unknown"
    if delta <= 120:
        return True, "near"
    if delta <= 365:
        return True, "mid"
    return True, "far"


def _far_date_caution(time_band: str) -> str:
    if time_band == "far":
        return " 문서 작성·적용 시점과 Commit 시점 차이가 큽니다."
    return ""


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return _CTRL_RE.sub(" ", str(value)).strip()


def extract_related_source_paths(item: Any) -> list[str]:
    """File paths only — never function names."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(path: str | None) -> None:
        if not path:
            return
        text = clean_text(path).replace("\\", "/")
        text = re.sub(r"/+", "/", text).strip("/")
        if not text or not re.search(r"\.(c|h|cpp|hpp|cc|cxx)$", text, re.I):
            # try extract from noisy cell
            m = _FILE_PATH_RE.search(clean_text(path))
            if not m:
                return
            text = m.group(0).replace("\\", "/")
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(text)

    for sf in getattr(item, "source_functions", None) or []:
        if isinstance(sf, dict):
            _add(sf.get("file_path"))
            raw = sf.get("raw_text")
            if raw:
                for m in _FILE_PATH_RE.finditer(clean_text(raw)):
                    _add(m.group(0))
        else:
            _add(getattr(sf, "file_path", None))
    return out


_PATH_DIR_TOKENS = frozenset(
    {
        "lib",
        "libcommon",
        "include",
        "card",
        "mif_post",
        "src",
        "sc_kscc",
        "common",
        "inc",
        "source",
        "sources",
        "header",
        "headers",
        "subwaylib",
    }
)


def _looks_like_file_path(text: str) -> bool:
    from app.services.symbol_utils import looks_like_path_or_source_file

    t = clean_text(text)
    if not t:
        return False
    if looks_like_path_or_source_file(t):
        return True
    if _FILE_PATH_RE.search(t):
        return True
    if re.match(
        r"(?i)^(lib|card|common|include|src|source)[/\\]",
        t.replace("\\", "/"),
    ):
        return True
    return False


def _path_stem_tokens(paths: list[str]) -> set[str]:
    stems: set[str] = set()
    for path in paths:
        text = clean_text(path).replace("\\", "/")
        for part in text.split("/"):
            part = part.strip()
            if not part:
                continue
            stem = re.sub(r"\.(c|h|cpp|hpp|cc|cxx)$", "", part, flags=re.I)
            if stem:
                stems.add(stem.lower())
            # Also keep directory segment tokens.
            stems.add(part.lower())
    return stems


def _accept_symbol_candidate(
    cand: str,
    *,
    seen: set[str],
    path_stems: set[str],
) -> str | None:
    if _looks_like_file_path(cand):
        return None
    if re.search(r"[/\\]", cand):
        return None
    if re.search(r"\.(c|h|cpp|hpp|cc|cxx)\b", cand, re.I):
        return None
    sym = normalize_symbol(cand)
    if not sym or not is_valid_symbol(sym):
        return None
    from app.services.symbol_utils import is_suffix_only_symbol

    if is_suffix_only_symbol(sym):
        return None
    key = sym.lower()
    if key in _PATH_DIR_TOKENS:
        return None
    if key in path_stems:
        return None
    if len(sym) < 4 and "_" not in sym:
        return None
    # Reject bare file-stem-like tokens ending with common suffixes when short.
    if key.endswith((".c", ".h")):
        return None
    if key in seen:
        return None
    seen.add(key)
    return sym


def extract_related_symbols(item: Any) -> list[str]:
    """Function/symbol names only — never file-path segments or filename stems.

    Sources:
    - explicit ``functions`` list entries (identifier / identifier(...))
    - ``identifier(...`` call forms in non-path text
    Newline joining only when a prior token ends with ``_`` and the next starts
    with an identifier character *within the same function item*.
    """
    from app.services.symbol_utils import (
        drop_suffix_symbol_duplicates,
        iter_call_symbol_candidates,
        join_underscore_wrapped_lines,
        looks_like_path_or_source_file,
    )

    out: list[str] = []
    seen: set[str] = set()
    path_stems = _path_stem_tokens(extract_related_source_paths(item))

    def _add_function_item(raw: str | None) -> None:
        if not raw:
            return
        # Preserve newlines for underscore-wrap recovery; do not flatten first.
        text = _CTRL_RE.sub("\n", str(raw)).strip()
        if not text:
            return
        if looks_like_path_or_source_file(text) and "(" not in text:
            return

        # Same-item underscore wrap only (never across separate list entries).
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        joined_parts = join_underscore_wrapped_lines(lines) if lines else [text]
        for part in joined_parts:
            if looks_like_path_or_source_file(part) and "(" not in part:
                continue
            if looks_like_path_or_source_file(part):
                # Mixed path + call on one line: call forms only.
                for cand in iter_call_symbol_candidates(part):
                    sym = _accept_symbol_candidate(
                        cand, seen=seen, path_stems=path_stems
                    )
                    if sym:
                        out.append(sym)
                continue
            # Dedicated function cell: allow bare identifier or call form.
            calls = iter_call_symbol_candidates(part)
            if calls:
                for cand in calls:
                    sym = _accept_symbol_candidate(
                        cand, seen=seen, path_stems=path_stems
                    )
                    if sym:
                        out.append(sym)
                continue
            # Whole cell is one symbol (e.g. "foo_ bar" without parens).
            cleaned = clean_text(part)
            if "," in cleaned or ";" in cleaned:
                for piece in re.split(r"[,;]+", cleaned):
                    piece = piece.strip()
                    if not piece or looks_like_path_or_source_file(piece):
                        continue
                    sym = _accept_symbol_candidate(
                        piece, seen=seen, path_stems=path_stems
                    )
                    if sym:
                        out.append(sym)
            else:
                sym = _accept_symbol_candidate(
                    cleaned, seen=seen, path_stems=path_stems
                )
                if sym:
                    out.append(sym)

    def _add_raw_text(raw: str | None) -> None:
        if not raw:
            return
        text = _CTRL_RE.sub("\n", str(raw)).strip()
        if not text:
            return
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        joined = join_underscore_wrapped_lines(lines)
        for part in joined:
            if looks_like_path_or_source_file(part):
                # Path line / path+call: call forms only; never path stems.
                for cand in iter_call_symbol_candidates(part):
                    sym = _accept_symbol_candidate(
                        cand, seen=seen, path_stems=path_stems
                    )
                    if sym:
                        out.append(sym)
                continue
            for cand in iter_call_symbol_candidates(part):
                sym = _accept_symbol_candidate(
                    cand, seen=seen, path_stems=path_stems
                )
                if sym:
                    out.append(sym)

    for sf in getattr(item, "source_functions", None) or []:
        if isinstance(sf, dict):
            for fn in sf.get("functions") or []:
                _add_function_item(str(fn))
            if sf.get("raw_text"):
                _add_raw_text(str(sf["raw_text"]))
        else:
            for fn in getattr(sf, "functions", None) or []:
                _add_function_item(str(fn))
    return drop_suffix_symbol_duplicates(out)


def symbol_listed_in_functions(item: Any, symbol: str) -> bool:
    """True only when the symbol appears in the document's explicit related-
    functions list (``source_functions[].functions``), never from a loose
    text-blob match (title/background/as-is/to-be prose).

    PROJECT_SPEC v2.4 §11 — the "대상 함수가 관련 함수로 확인됩니다" wording
    must only be generated when the target function is actually present in
    the document's own printed related-function list, not merely mentioned
    somewhere in free text.
    """
    target = normalize_symbol(symbol)
    if not target or not is_valid_symbol(target):
        return False
    for fn in extract_related_symbols(item):
        if symbols_equivalent(fn, symbol):
            return True
    return False


def item_mentions_symbol(item: Any, symbol: str) -> bool:
    from app.services.symbol_utils import (
        iter_call_symbol_candidates,
        join_underscore_wrapped_lines,
        symbol_appears_in_text,
    )

    target = normalize_symbol(symbol)
    if not target or not is_valid_symbol(target):
        return False
    for fn in extract_related_symbols(item):
        if symbols_equivalent(fn, symbol):
            return True
    blobs: list[str] = []
    for sf in getattr(item, "source_functions", None) or []:
        if isinstance(sf, dict):
            for x in sf.get("functions") or []:
                blobs.append(str(x))
            if sf.get("raw_text"):
                # Preserve wrap; join underscore continuations only.
                raw = _CTRL_RE.sub("\n", str(sf["raw_text"]))
                joined = join_underscore_wrapped_lines(
                    [ln.strip() for ln in raw.splitlines() if ln.strip()]
                )
                blobs.extend(joined)
        else:
            blobs.extend(str(x) for x in (getattr(sf, "functions", None) or []))
    for field_name in ("raw_text", "to_be", "as_is", "business_background", "change_title"):
        val = getattr(item, field_name, None)
        if val:
            blobs.append(str(val))
    for val in blobs:
        if not val:
            continue
        if _looks_like_file_path(val) and "(" not in val:
            continue
        if symbols_equivalent(val, symbol):
            return True
        if symbol_appears_in_text(symbol, val):
            return True
        for cand in iter_call_symbol_candidates(val):
            if symbols_equivalent(cand, symbol):
                return True
        stripped = _FILE_PATH_RE.sub(" ", clean_text(val))
        if symbol_appears_in_text(symbol, stripped):
            return True
    return False


def item_path_match_level(item: Any, file_path: str | None) -> PathMatchLevel:
    if not file_path:
        return PathMatchLevel.NONE
    best = PathMatchLevel.NONE
    rank = {
        PathMatchLevel.NONE: 0,
        PathMatchLevel.BASENAME: 1,
        PathMatchLevel.SUFFIX: 2,
        PathMatchLevel.EXACT: 3,
    }
    for path in extract_related_source_paths(item):
        level = source_path_match_level(file_path, path)
        if rank[level] > rank[best]:
            best = level
    return best


def is_feature_document_for_symbol(item: Any, symbol: str, file_path: str | None) -> bool:
    """Lifecycle official-candidate gate.

    Path-only matches are intentionally excluded here. Shared source files
    (e.g. many features in one ``.c``) must not enter user-facing official
    collections. Path-only recall remains Evidence candidate search's job.
    """
    _ = file_path
    return item_mentions_symbol(item, symbol)


def feature_token_overlap(doc_texts: list[str | None], commit_message: str | None) -> bool:
    """True when non-trivial tokens overlap between document and commit message."""
    stop = {
        "카드",
        "변경",
        "적용",
        "삭제",
        "제거",
        "수정",
        "보완",
        "로직",
        "기능",
        "관련",
        "처리",
        "추가",
        "문서",
        "건",
    }
    msg_tokens = {
        t
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|[가-힣]{2,}", commit_message or "")
        if t.lower() not in stop and t not in stop
    }
    if not msg_tokens:
        return False
    blob = " ".join(t for t in doc_texts if t)
    doc_tokens = {
        t
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|[가-힣]{2,}", blob)
        if t.lower() not in stop and t not in stop
    }
    return bool(msg_tokens & doc_tokens)


def strong_initial_context_match(
    *,
    symbol_hit: bool,
    path_level: PathMatchLevel,
    time_band: str,
    action_ok: bool,
    doc_action: str,
    change_type: str,
    phase: str,
    item: Any,
    message: str | None,
) -> bool:
    """Initial-development fallback when symbol cells are noisy but context is strong.

    Requires date + feature tokens + action + source + core intro commit.
    Never used for maintenance/delete docs.
    """
    if symbol_hit:
        return False  # not needed
    if phase != "development" or doc_action == ACTION_DELETE:
        return False
    if change_type not in _CORE_INTRO_TYPES:
        return False
    if path_level not in {PathMatchLevel.EXACT, PathMatchLevel.SUFFIX}:
        return False
    if not action_ok:
        return False
    if doc_action not in {ACTION_APPLY, ACTION_MODIFY, ACTION_UNKNOWN}:
        return False
    if not extract_related_symbols(item):
        # Shared source path only — topic overlap must not create official links
        # when the document has no related-function cells or symbol-like tokens.
        doc_blob = " ".join(
            str(getattr(item, f, "") or "")
            for f in ("to_be", "as_is", "business_background", "change_title")
        )
        if not doc_blob.strip():
            return False
        if not re.search(r"[A-Za-z_][A-Za-z0-9_]{4,}", doc_blob):
            return False
    return feature_token_overlap(
        [
            getattr(item, "change_title", None),
            getattr(item, "business_background", None),
            getattr(item, "to_be", None),
            getattr(item, "as_is", None),
        ],
        message,
    )


def document_phase(doc_action: str, doc_date: str | None, creation_date: str | None) -> str:
    """Phase hint from change action only — never from fixed day gaps.

    ``doc_date`` / ``creation_date`` are accepted for call-site compatibility
    and may be used by callers for sorting; they do not decide phase here.
    """
    _ = (doc_date, creation_date)
    if doc_action == ACTION_DELETE:
        return "maintenance"
    return "development"


@dataclass
class FeatureDocument:
    item: Any
    commit_hashes: list[str] = field(default_factory=list)

    @property
    def file_name(self) -> str | None:
        return getattr(self.item, "file_name", None) or getattr(self.item, "file_path", None)

    @property
    def slide_no(self) -> int | None:
        return getattr(self.item, "slide_no", None)

    @property
    def change_title(self) -> str | None:
        return getattr(self.item, "change_title", None)


def resolve_item_equipment_id(item: Any) -> int | None:
    """Resolve document_cache.equipment_id (discovery scope — not applicability)."""
    eid = getattr(item, "equipment_id", None)
    if eid is not None:
        try:
            return int(eid)
        except (TypeError, ValueError):
            pass
    doc_id = getattr(item, "document_cache_id", None)
    if doc_id is None:
        return None
    try:
        from app.services.ppt_cache_service import get_document_cache_by_id

        doc = get_document_cache_by_id(int(doc_id))
        if doc is not None and getattr(doc, "equipment_id", None) is not None:
            return int(doc.equipment_id)
    except Exception:
        return None
    return None


def _load_known_equipment() -> list[tuple[int, str]]:
    try:
        from app.services.equipment_service import list_equipment

        return [(int(e.id), str(e.name)) for e in list_equipment()]
    except Exception:
        return []


def _resolve_request_equipment_name(
    evidence_result: Any,
    request_equipment_id: int | None,
) -> str | None:
    name = getattr(evidence_result, "equipment_name", None)
    if name:
        return str(name).strip() or None
    if request_equipment_id is None:
        return None
    try:
        from app.services.equipment_service import get_equipment

        eq = get_equipment(int(request_equipment_id))
        if eq is not None:
            return str(eq.name).strip() or None
    except Exception:
        return None
    return None


def _strong_unknown_equipment_grounds(
    item: Any,
    symbol: str,
    file_path: str | None,
) -> bool:
    """Unknown applicable-equipment: require more than CSR / generic tokens / path-only."""
    if not item_mentions_symbol(item, symbol):
        return False
    path_level = item_path_match_level(item, file_path)
    if path_level == PathMatchLevel.NONE:
        return False
    # Path alone is insufficient — need apply/delete/modify action signal in title/body.
    action = classify_change_action(
        getattr(item, "change_title", None),
        getattr(item, "business_background", None),
        getattr(item, "to_be", None),
        getattr(item, "as_is", None),
    )
    if action not in {ACTION_APPLY, ACTION_MODIFY, ACTION_DELETE}:
        return False
    # Sparse feature tokens beyond generic 카드/후불.
    title = clean_text(getattr(item, "change_title", None))
    if not title:
        return False
    generic = {"카드", "후불", "변경", "적용", "삭제", "수정", "기능", "로직"}
    tokens = {t for t in re.split(r"[^\w가-힣]+", title.lower()) if len(t) >= 2}
    if not (tokens - generic):
        return False
    return True


def item_matches_request_equipment(
    item: Any,
    request_equipment_id: int | None,
    *,
    request_equipment_name: str | None = None,
    known_equipment: list[tuple[int, str]] | None = None,
    symbol: str | None = None,
    file_path: str | None = None,
    for_official: bool = True,
) -> bool:
    """Gate official promotion by document-declared applicable equipment.

    ``document_cache.equipment_id`` only reflects discovery via shared
    document_path and must NOT alone decide official promotion.
    """
    if not for_official:
        return True
    if request_equipment_id is None and not request_equipment_name:
        return True

    from app.services.equipment_name_utils import (
        MATCH_CLEAR,
        MATCH_MISMATCH,
        MATCH_MULTI,
        MATCH_UNKNOWN,
        analyze_document_equipment_match,
    )

    known = known_equipment if known_equipment is not None else _load_known_equipment()
    match = analyze_document_equipment_match(
        item,
        request_equipment_id=request_equipment_id,
        request_equipment_name=request_equipment_name,
        known_equipment=known,
    )
    if match.match_type in {MATCH_CLEAR, MATCH_MULTI}:
        return True
    if match.match_type == MATCH_MISMATCH:
        return False
    if match.match_type == MATCH_UNKNOWN:
        if symbol:
            return _strong_unknown_equipment_grounds(item, symbol, file_path)
        return False
    return False


def collect_feature_documents(
    evidence_result: Any,
    symbol: str,
    *,
    file_path: str | None = None,
) -> list[FeatureDocument]:
    """Gather symbol-matching change items applicable to the request equipment."""
    by_key: dict[str, FeatureDocument] = {}
    request_equipment_id = getattr(evidence_result, "equipment_id", None)
    try:
        request_equipment_id = (
            int(request_equipment_id) if request_equipment_id is not None else None
        )
    except (TypeError, ValueError):
        request_equipment_id = None

    known_equipment = _load_known_equipment()
    request_equipment_name = _resolve_request_equipment_name(
        evidence_result, request_equipment_id
    )

    def _add(item: Any, commit_hash: str | None) -> None:
        if item is None:
            return
        if not item_matches_request_equipment(
            item,
            request_equipment_id,
            request_equipment_name=request_equipment_name,
            known_equipment=known_equipment,
            symbol=symbol,
            file_path=file_path,
            for_official=True,
        ):
            return
        if not is_feature_document_for_symbol(item, symbol, file_path):
            return
        # Stamp discovery equipment_id for identity only (not applicability proof).
        if getattr(item, "equipment_id", None) is None and request_equipment_id is not None:
            try:
                item.equipment_id = request_equipment_id
            except Exception:
                pass
        key = (
            f"{request_equipment_id}|"
            f"{getattr(item, 'change_item_cache_id', None)}|"
            f"{getattr(item, 'slide_no', None)}|"
            f"{getattr(item, 'file_name', None)}|"
            f"{getattr(item, 'change_title', None)}"
        )
        doc = by_key.get(key)
        if doc is None:
            doc = FeatureDocument(item=item)
            by_key[key] = doc
        if commit_hash and commit_hash not in doc.commit_hashes:
            doc.commit_hashes.append(commit_hash)

    for link in getattr(evidence_result, "evidence_links", None) or []:
        git = getattr(link, "git_candidate", None)
        h = getattr(git, "commit_hash", None) if git else None
        _add(getattr(link, "change_item", None), h)

    for item in getattr(evidence_result, "change_item_candidates", None) or []:
        _add(item, None)

    # Lifecycle enrichment: shared-path cache may contain other-equipment PPTs
    # discovered under this equipment_id — applicability gate filters them out.
    if request_equipment_id is not None:
        try:
            from app.services.change_item_cache_service import list_change_items_for_equipment
            from app.services.change_item_candidate_service import ChangeItemCandidate

            for row in list_change_items_for_equipment(int(request_equipment_id)):
                try:
                    source_functions = json.loads(row.source_functions_json or "[]")
                except json.JSONDecodeError:
                    source_functions = []
                if not isinstance(source_functions, list):
                    source_functions = []
                scopes: list = []
                try:
                    scopes = json.loads(row.applicable_scopes_json or "[]")
                except json.JSONDecodeError:
                    scopes = []
                if not isinstance(scopes, list):
                    scopes = []
                item = ChangeItemCandidate(
                    change_item_cache_id=row.id,
                    document_cache_id=row.document_cache_id,
                    slide_no=row.slide_no,
                    file_path=row.file_path or "",
                    file_name=row.file_name or "",
                    item_no=row.item_no,
                    change_title=row.change_title,
                    csr_no=row.csr_no,
                    business_background=row.business_background,
                    current_status=row.current_status,
                    as_is=row.as_is,
                    to_be=row.to_be,
                    source_functions=source_functions,
                    test_cases=[],
                    applicable_scopes=scopes,
                    raw_text=row.raw_text or "",
                    matched_keywords=[],
                    candidate_score=0,
                    equipment_id=row.equipment_id
                    if row.equipment_id is not None
                    else request_equipment_id,
                )
                if item_mentions_symbol(item, symbol):
                    _add(item, None)
        except Exception:
            pass

    return list(by_key.values())


def _title_aligns_with_change(title: str | None, change_type: str, message: str | None) -> bool:
    doc_action = classify_change_action(title)
    commit_action = commit_change_action(change_type, message)
    return actions_compatible(doc_action, commit_action, change_type)


def build_ppt_link_for_entry(
    *,
    commit_hash: str,
    commit_date: str | None,
    message: str | None,
    change_type: str,
    file_path: str,
    symbol: str,
    feature_docs: list[FeatureDocument],
    creation_date: str | None = None,
    function_range_confirmed: bool = False,
    diff_available: bool = False,
) -> PptLink | None:
    """Pick the best *Commit-level* document link for one lifecycle entry.

    PROJECT_SPEC v2.5 — only ``Commit 직접 근거`` / ``단계 연결 근거`` are
    attached here. Weak ``관련 참고`` matches are collected separately at the
    function level and must not appear on Commit 상세.
    """
    if not feature_docs:
        return None

    is_log = change_type == "comment_or_log"
    commit_action = commit_change_action(change_type, message)
    is_coreish = change_type in _CORE_INTRO_TYPES or change_type in _MAINT_TYPES
    is_creation = change_type in {"function_creation", "function_creation_estimated"}

    best: PptLink | None = None
    best_rank = -1

    for doc in feature_docs:
        item = doc.item
        title = clean_text(doc.change_title) or None
        file_name = doc.file_name
        slide = doc.slide_no
        doc_date = extract_document_date(file_name)
        doc_action = classify_change_action(
            title,
            getattr(item, "business_background", None),
            getattr(item, "to_be", None),
            getattr(item, "as_is", None),
        )
        phase = document_phase(doc_action, doc_date, creation_date)
        symbol_hit = item_mentions_symbol(item, symbol)
        symbol_listed = symbol_listed_in_functions(item, symbol)
        path_level = item_path_match_level(item, file_path)
        hash_hit = commit_hash in doc.commit_hashes
        _, time_band = time_compatible(
            commit_date, doc_date, doc_action=doc_action, change_type=change_type
        )
        action_ok = actions_compatible(doc_action, commit_action, change_type)
        exact_diff_hit = bool(
            diff_available and function_range_confirmed and symbol_hit and action_ok
        )
        strong_context = strong_initial_context_match(
            symbol_hit=symbol_hit,
            path_level=path_level,
            time_band=time_band,
            action_ok=action_ok,
            doc_action=doc_action,
            change_type=change_type,
            phase=phase,
            item=item,
            message=message,
        )
        can_official = symbol_hit or exact_diff_hit or strong_context
        if not can_official:
            continue

        link_type = None
        reason = ""
        conf = "medium"
        rank = 0
        far_caution = _far_date_caution(time_band)

        # Log / action-mismatch / weak related → function-level only.
        if is_log or not action_ok:
            continue

        if (
            (hash_hit or symbol_listed)
            and symbol_hit
            and action_ok
            and diff_available
            and function_range_confirmed
            and (
                hash_hit
                or feature_token_overlap(
                    [
                        title,
                        getattr(item, "business_background", None),
                        getattr(item, "to_be", None),
                        getattr(item, "as_is", None),
                    ],
                    message,
                )
            )
        ):
            link_type = LINK_COMMIT_DIRECT if hash_hit else LINK_FEATURE_RELEASE
            reason = (
                "대상 함수 Diff와 문서 As-Is/To-Be가 직접 일치합니다."
                + far_caution
                if link_type == LINK_COMMIT_DIRECT
                else (
                    "Commit Diff와 문서의 기능 주제가 일치하고 "
                    "대상 함수가 관련 함수 목록에 명시되어 있습니다."
                    + far_caution
                )
            )
            conf = "high" if time_band != "far" else "medium"
            rank = 100 if link_type == LINK_COMMIT_DIRECT else 80
            if time_band == "far" and link_type == LINK_COMMIT_DIRECT:
                rank = 90
        elif (
            (change_type in _MAINT_TYPES or commit_action == ACTION_DELETE)
            and doc_action == ACTION_DELETE
            and action_ok
            and diff_available
            and function_range_confirmed
            and symbol_hit
            and (hash_hit or symbol_listed)
        ):
            link_type = LINK_COMMIT_DIRECT if hash_hit else LINK_FEATURE_RELEASE
            reason = (
                "날짜 비교/조건 삭제 Diff가 유지보수 문서와 직접 일치합니다."
                + far_caution
            )
            conf = "high" if time_band != "far" else "medium"
            rank = 95 if hash_hit else 70
        elif (
            not is_log
            and commit_action != ACTION_DELETE
            and change_type not in _MAINT_TYPES
            and doc_action in {ACTION_APPLY, ACTION_MODIFY, ACTION_UNKNOWN}
            and phase == "development"
            and action_ok
            and (symbol_hit or strong_context)
            and (
                change_type in _CORE_INTRO_TYPES
                or change_type
                in {
                    "related_candidate",
                    "diff_unavailable",
                    "call_site_change",
                    "callsite_change",
                    "test_or_debug",
                }
                or is_coreish
            )
        ):
            topic_overlap = feature_token_overlap(
                [
                    title,
                    getattr(item, "business_background", None),
                    getattr(item, "to_be", None),
                    getattr(item, "as_is", None),
                ],
                message,
            )

            # Creation commits need explicit functional lineage — Diff + listed
            # symbol + topic overlap (hash is helpful but not mandatory when
            # Diff confirms the same feature as the document).
            if is_creation:
                if not (
                    symbol_listed
                    and topic_overlap
                    and diff_available
                    and function_range_confirmed
                ):
                    continue

            if change_type in {"related_candidate", "diff_unavailable"}:
                if not topic_overlap:
                    continue

            # Stage link on Commit requires exact related_functions listing.
            if not symbol_listed:
                continue
            if not topic_overlap and not (diff_available and function_range_confirmed):
                continue

            link_type = LINK_FEATURE_RELEASE
            if not diff_available or not function_range_confirmed:
                if not topic_overlap:
                    continue
                reason = (
                    "Commit 메시지와 문서의 기능 주제가 일치하고 "
                    "대상 함수가 관련 함수 목록에 명시되어 있습니다. "
                    "대상 함수의 세부 Diff는 확보하지 못했습니다."
                    + far_caution
                )
            else:
                reason = (
                    "Commit 메시지와 문서의 기능 주제가 일치하고 "
                    "대상 함수가 관련 함수 목록에 명시되어 있습니다."
                    + far_caution
                )
            if change_type in _CORE_INTRO_TYPES and time_band == "near":
                conf = "high"
                rank = 80
            elif change_type in _CORE_INTRO_TYPES:
                conf = "medium"
                rank = 60 if time_band == "mid" else 50
            else:
                conf = "medium" if time_band in {"near", "mid", "unknown"} else "low"
                rank = 45 if time_band == "near" else 35
            if path_level in {PathMatchLevel.EXACT, PathMatchLevel.SUFFIX}:
                rank += 3
        else:
            continue

        if link_type not in {LINK_COMMIT_DIRECT, LINK_FEATURE_RELEASE}:
            continue

        if time_band == "near":
            rank += 3
        if doc_action == commit_action:
            rank += 2
        if symbol_listed:
            rank += 2

        paths = extract_related_source_paths(item)
        symbols = extract_related_symbols(item)
        versions = extract_versions(file_name, title, getattr(item, "to_be", None))
        candidate = PptLink(
            document_name=file_name,
            slide_number=slide,
            change_title=title,
            link_type=link_type,
            link_reason_user=reason,
            linked_commit_hashes=[commit_hash] if hash_hit else [],
            # Full lists retained — Markdown display truncates only (v2.5.1 §1.7).
            related_symbols=list(symbols),
            related_source_paths=list(paths),
            confidence=conf,
            csr_no=getattr(item, "csr_no", None),
            business_background=clean_text(getattr(item, "business_background", None))
            or None,
            to_be=clean_text(getattr(item, "to_be", None)) or None,
            as_is=clean_text(getattr(item, "as_is", None)) or None,
            document_path=getattr(item, "file_path", None),
            document_date=doc_date,
            versions=versions,
            change_action=doc_action,
            phase=phase,
            change_item_cache_id=getattr(item, "change_item_cache_id", None),
            equipment_id=resolve_item_equipment_id(item),
        )
        if rank > best_rank:
            best = candidate
            best_rank = rank

    return best


def ppt_link_from_feature_document(
    doc: FeatureDocument,
    *,
    creation_date: str | None = None,
    link_type: str = LINK_RELATED,
    symbol: str | None = None,
    file_path: str | None = None,
) -> PptLink:
    """Function-level official document — independent of a single commit match.

    PROJECT_SPEC v2.5 — these links populate ``## 관련 공식 문서`` as
    ``관련 참고`` unless a Commit-level direct/stage link upgrades them.
    """
    item = doc.item
    title = clean_text(doc.change_title) or None
    file_name = doc.file_name
    doc_date = extract_document_date(file_name)
    doc_action = classify_change_action(
        title,
        getattr(item, "business_background", None),
        getattr(item, "to_be", None),
        getattr(item, "as_is", None),
    )
    phase = document_phase(doc_action, doc_date, creation_date)
    symbol_listed = bool(symbol and symbol_listed_in_functions(item, symbol))
    path_level = item_path_match_level(item, file_path) if file_path else PathMatchLevel.NONE
    if symbol_listed:
        reason = "대상 함수가 관련 함수 목록에 명시되어 있습니다."
    elif path_level in {PathMatchLevel.EXACT, PathMatchLevel.SUFFIX}:
        reason = "대상 파일이 문서 관련 소스에 포함되어 있습니다."
    else:
        reason = (
            "대상 함수·파일과 관련된 공식 변경내역서입니다. "
            "개별 Commit과의 직접·단계 연결은 확인되지 않았습니다."
        )
    return PptLink(
        document_name=file_name,
        slide_number=doc.slide_no,
        change_title=title,
        link_type=LINK_RELATED,
        link_reason_user=reason,
        linked_commit_hashes=list(doc.commit_hashes),
        related_symbols=list(extract_related_symbols(item)),
        related_source_paths=list(extract_related_source_paths(item)),
        confidence="medium",
        csr_no=getattr(item, "csr_no", None),
        business_background=clean_text(getattr(item, "business_background", None)) or None,
        to_be=clean_text(getattr(item, "to_be", None)) or None,
        as_is=clean_text(getattr(item, "as_is", None)) or None,
        document_path=getattr(item, "file_path", None),
        document_date=doc_date,
        versions=extract_versions(file_name, title, getattr(item, "to_be", None)),
        change_action=doc_action,
        phase=phase,
        change_item_cache_id=getattr(item, "change_item_cache_id", None),
        equipment_id=resolve_item_equipment_id(item),
    )


def collect_stage_official_docs(
    feature_docs: list[FeatureDocument],
    *,
    symbol: str,
    creation_date: str | None = None,
    request_equipment_id: int | None = None,
    request_equipment_name: str | None = None,
    known_equipment: list[tuple[int, str]] | None = None,
    file_path: str | None = None,
) -> list[PptLink]:
    """Function-level related official docs (관련 참고).

    Includes documents where the symbol is listed in related_functions OR the
    file path matches related_sources. Does **not** invent Commit-level stage
    strength — that comes only from ``build_ppt_link_for_entry``.
    """
    out: list[PptLink] = []
    seen: set[str] = set()
    known = known_equipment if known_equipment is not None else _load_known_equipment()
    for doc in feature_docs:
        if not item_matches_request_equipment(
            doc.item,
            request_equipment_id,
            request_equipment_name=request_equipment_name,
            known_equipment=known,
            symbol=symbol,
            file_path=file_path,
            for_official=True,
        ):
            continue
        symbol_listed = symbol_listed_in_functions(doc.item, symbol)
        path_level = item_path_match_level(doc.item, file_path) if file_path else PathMatchLevel.NONE
        path_ok = path_level in {PathMatchLevel.EXACT, PathMatchLevel.SUFFIX}
        if not symbol_listed and not path_ok:
            continue
        link = ppt_link_from_feature_document(
            doc,
            creation_date=creation_date,
            link_type=LINK_RELATED,
            symbol=symbol,
            file_path=file_path,
        )
        if request_equipment_id is not None and link.equipment_id is None:
            link = replace(link, equipment_id=int(request_equipment_id))
        if link.change_action == ACTION_LOG:
            continue
        key = link.identity_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(link)
    return out


def merge_official_doc_collections(
    *groups: list[PptLink],
    request_equipment_id: int | None = None,
    request_equipment_name: str | None = None,
    known_equipment: list[tuple[int, str]] | None = None,
) -> list[PptLink]:
    """Dedupe by document identity; prefer stronger link types."""
    from app.services.equipment_name_utils import (
        MATCH_MISMATCH,
        link_document_allows_official,
    )

    rank = {
        LINK_COMMIT_DIRECT: 3,
        LINK_FEATURE_RELEASE: 2,
        LINK_MAINTENANCE: 1,
        LINK_RELATED: 1,
        LINK_DEV_REFERENCE: 1,
    }
    known = known_equipment if known_equipment is not None else _load_known_equipment()
    best: dict[str, PptLink] = {}
    for group in groups:
        for link in group:
            if request_equipment_name:
                em = link_document_allows_official(
                    document_name=link.document_name,
                    document_path=link.document_path,
                    change_title=link.change_title,
                    request_equipment_name=request_equipment_name,
                    known_equipment=known,
                )
                if em.match_type == MATCH_MISMATCH:
                    continue
            # Do not promote development_reference to feature_release — that
            # invented a stronger connection strength than evidence supports.
            if link.link_type == LINK_DEV_REFERENCE:
                link = replace(link, link_type=LINK_RELATED)
            if link.link_type not in {
                LINK_COMMIT_DIRECT,
                LINK_FEATURE_RELEASE,
                LINK_MAINTENANCE,
                LINK_RELATED,
            }:
                continue
            key = link.identity_key()
            prev = best.get(key)
            if prev is None or rank.get(link.link_type, 0) > rank.get(prev.link_type, 0):
                best[key] = link
    return list(best.values())


def unique_official_docs(
    links: list[PptLink],
    *,
    request_equipment_id: int | None = None,
) -> list[PptLink]:
    """Deduplicate official docs (feature + maintenance + commit-direct)."""
    return merge_official_doc_collections(
        links, request_equipment_id=request_equipment_id
    )


def unique_feature_release_docs(links: list[PptLink]) -> list[PptLink]:
    """Development-phase official docs only (stage apply / feature release)."""
    seen: set[str] = set()
    out: list[PptLink] = []
    for link in unique_official_docs(links):
        if link.change_action == ACTION_DELETE:
            continue
        if link.phase == "maintenance" and link.link_type == LINK_MAINTENANCE:
            continue
        if link.link_type not in {LINK_COMMIT_DIRECT, LINK_FEATURE_RELEASE}:
            continue
        if link.change_action == ACTION_DELETE and link.link_type != LINK_COMMIT_DIRECT:
            continue
        key = link.identity_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(link)
    return out


def pick_primary_feature_title(
    links: list[PptLink],
    *,
    creation_message: str | None = None,
) -> str | None:
    """Prefer first-release apply/modify title — never a later delete title."""
    official = unique_official_docs(links)
    apply_docs = [
        d
        for d in official
        if d.change_action == ACTION_APPLY and d.phase == "development"
    ]
    if apply_docs:
        apply_docs.sort(key=lambda d: d.document_date or "9999")
        return apply_docs[0].change_title
    dev_docs = [
        d
        for d in official
        if d.phase == "development" and d.change_action != ACTION_DELETE
    ]
    if dev_docs:
        return dev_docs[0].change_title
    # Soft fallback: any non-delete linked title (e.g. related apply doc).
    soft = [
        d
        for d in links
        if d.change_title
        and d.change_action != ACTION_DELETE
        and d.phase != "maintenance"
    ]
    if soft:
        return soft[0].change_title
    if creation_message:
        msg = clean_text(creation_message)
        if msg and classify_change_action(msg) != ACTION_DELETE:
            return msg
    return None


def maintenance_docs(links: list[PptLink]) -> list[PptLink]:
    seen: set[str] = set()
    out: list[PptLink] = []
    for link in links:
        if link.phase != "maintenance" and link.change_action != ACTION_DELETE:
            if link.link_type != LINK_MAINTENANCE:
                continue
        if link.link_type not in {
            LINK_MAINTENANCE,
            LINK_COMMIT_DIRECT,
            LINK_FEATURE_RELEASE,
            LINK_RELATED,
        }:
            continue
        if link.change_action != ACTION_DELETE and link.link_type != LINK_MAINTENANCE:
            continue
        key = link.identity_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(link)
    return out


# Token helpers for search-order independence (tests / keyword recall).
def normalize_search_tokens(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    parts = [t for t in re.split(r"[^\w가-힣]+", text.lower()) if len(t) >= 2]
    return set(parts) | ({compact} if compact else set())


def search_token_sets_equivalent(a: str, b: str) -> bool:
    """True when token bags match ignoring order (e.g. 청소년 후불 vs 후불 청소년)."""
    ta = {t for t in re.split(r"[^\w가-힣]+", a.lower()) if len(t) >= 2}
    tb = {t for t in re.split(r"[^\w가-힣]+", b.lower()) if len(t) >= 2}
    if not ta or not tb:
        return False
    return ta == tb
