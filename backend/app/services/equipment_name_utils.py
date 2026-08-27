"""Equipment name matching and document applicable-equipment detection.

``document_cache.equipment_id`` means which equipment setting discovered the
file via a shared document_path — not which equipment the PPT describes.

Official promotion must use document-declared applicable equipment (title /
filename / scopes), never cache discovery id alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# Collapse whitespace / underscore / hyphen / dots / parentheses so
# "휴대용 정산기", "휴대용_정산기", "휴대용.정산기" compare as the same token.
# Deliberately not fuzzy — no edit-distance / partial-token matching.
_SEP_RE = re.compile(r"[\s_\-\.\(\)\[\]{}]+")
_PAREN_CONTENT_RE = re.compile(r"\([^)]*\)|\[[^\]]*\]|\{[^}]*\}")
_CHANGE_HISTORY_NAME_RE = re.compile(r"변경내역|프로그램\s*변경", re.IGNORECASE)
# Keep prior filename-filter threshold (len < 2 rejected).
_MIN_EQUIPMENT_TOKEN_LEN = 2

MATCH_CLEAR = "clear_match"
MATCH_MULTI = "multi_match"
MATCH_MISMATCH = "clear_mismatch"
MATCH_UNKNOWN = "unknown"


def normalize_equipment_name(name: str | None) -> str:
    """Normalize an equipment or filename token for containment checks."""
    if not name:
        return ""
    text = name.strip().lower()
    # Bracket characters are separators; inner tokens remain
    # (Portable(Device) → portabledevice).
    text = _SEP_RE.sub("", text)
    return text


def equipment_name_aliases(name: str | None) -> list[str]:
    """Return comparable aliases for an equipment name (no hardcoded product list).

    Includes the raw name and a parenthesis-content-stripped form. Future
    config/DB aliases can extend this list without changing call sites.
    """
    if not name:
        return []
    raw = str(name).strip()
    if not raw:
        return []
    aliases = [raw]
    stripped = _PAREN_CONTENT_RE.sub("", raw).strip()
    if stripped and stripped not in aliases:
        aliases.append(stripped)
    compact = normalize_equipment_name(raw)
    if compact and compact not in {normalize_equipment_name(a) for a in aliases}:
        aliases.append(compact)
    return aliases


def document_basename(document_path: str | None) -> str:
    """Return filename only — never use parent folder for equipment matching."""
    if not document_path:
        return ""
    text = str(document_path).strip()
    if not text:
        return ""
    return Path(text.replace("\\", "/")).name


def filename_matches_equipment(
    file_name: str | None, equipment_name: str | None
) -> bool:
    """True when normalized equipment.name is contained in the document filename."""
    equipment = normalize_equipment_name(equipment_name)
    if len(equipment) < _MIN_EQUIPMENT_TOKEN_LEN:
        return False
    filename = normalize_equipment_name(file_name)
    if not filename:
        return False
    return equipment in filename


def is_document_for_equipment(
    document_path: str | None, equipment_name: str | None
) -> bool:
    """Filename hard filter used by PPT candidate search (shared folders OK)."""
    return filename_matches_equipment(
        document_basename(document_path), equipment_name
    )


def text_mentions_equipment(text: str | None, equipment_name: str | None) -> bool:
    """True when any alias of equipment_name appears in normalized text."""
    if not text or not equipment_name:
        return False
    blob = normalize_equipment_name(text)
    if not blob:
        return False
    for alias in equipment_name_aliases(equipment_name):
        token = normalize_equipment_name(alias)
        if len(token) < _MIN_EQUIPMENT_TOKEN_LEN:
            continue
        if token in blob:
            return True
    return False


def detect_equipment_names_in_texts(
    texts: Iterable[str | None],
    known_equipment_names: Iterable[str],
) -> list[str]:
    """Return known equipment names detected in texts (longest-first, stable)."""
    parts = [str(t) for t in texts if t and str(t).strip()]
    if not parts:
        return []
    blob = normalize_equipment_name("\n".join(parts))
    if not blob:
        return []

    scored: list[tuple[int, str]] = []
    seen_norm: set[str] = set()
    for name in known_equipment_names:
        if not name or not str(name).strip():
            continue
        display = str(name).strip()
        token = normalize_equipment_name(display)
        if len(token) < _MIN_EQUIPMENT_TOKEN_LEN:
            continue
        if token in seen_norm:
            continue
        if token in blob:
            seen_norm.add(token)
            scored.append((len(token), display))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [name for _, name in scored]


@dataclass
class DocumentEquipmentMatch:
    match_type: str
    detected_equipment_names: list[str] = field(default_factory=list)
    applicable_equipment_ids: list[int] = field(default_factory=list)
    equipment_match_reason: str = ""
    request_equipment_name: str | None = None

    @property
    def allows_official(self) -> bool:
        return self.match_type in {MATCH_CLEAR, MATCH_MULTI}


def _item_equipment_evidence_texts(item: Any) -> list[tuple[str, str]]:
    """Priority-ordered (label, text) evidence for applicable-equipment detection."""
    out: list[tuple[str, str]] = []

    def _add(label: str, value: Any) -> None:
        if value is None:
            return
        text = str(value).strip()
        if text:
            out.append((label, text))

    # 1) Change-item / document title fields
    _add("change_title", getattr(item, "change_title", None))
    # 2) Applicable scopes / target system fields from slide
    scopes = getattr(item, "applicable_scopes", None) or []
    if isinstance(scopes, list):
        for scope in scopes:
            _add("applicable_scope", scope)
    # 3) Filename (high signal for change-history PPT naming convention)
    _add("file_name", getattr(item, "file_name", None))
    _add("file_path_basename", document_basename(getattr(item, "file_path", None)))
    # 4) Body fields / raw slide text (may include cover title)
    _add("business_background", getattr(item, "business_background", None))
    _add("to_be", getattr(item, "to_be", None))
    _add("as_is", getattr(item, "as_is", None))
    _add("raw_text", getattr(item, "raw_text", None))
    return out


def analyze_document_equipment_match(
    item: Any,
    *,
    request_equipment_id: int | None,
    request_equipment_name: str | None,
    known_equipment: list[tuple[int, str]] | None = None,
) -> DocumentEquipmentMatch:
    """Decide whether a change-item PPT is applicable to the request equipment.

    known_equipment: list of (id, name) for all registered equipment — used to
    detect clear mismatches (other equipment named, current not named).
    """
    known = list(known_equipment or [])
    known_names = [name for _, name in known]
    evidence = _item_equipment_evidence_texts(item)
    texts = [t for _, t in evidence]
    detected = detect_equipment_names_in_texts(texts, known_names)

    # Also detect request name even if not yet in known list (tests / partial DB).
    req_name = (request_equipment_name or "").strip() or None
    req_mentioned = bool(req_name and any(text_mentions_equipment(t, req_name) for t in texts))
    if req_name and req_mentioned and req_name not in detected:
        detected = [req_name, *[d for d in detected if normalize_equipment_name(d) != normalize_equipment_name(req_name)]]

    applicable_ids: list[int] = []
    for eid, name in known:
        if any(
            normalize_equipment_name(d) == normalize_equipment_name(name)
            for d in detected
        ):
            applicable_ids.append(int(eid))

    reason_bits: list[str] = []
    for label, text in evidence:
        if req_name and text_mentions_equipment(text, req_name):
            reason_bits.append(f"{label}:request")
            break
    for label, text in evidence:
        for other in detected:
            if req_name and normalize_equipment_name(other) == normalize_equipment_name(req_name):
                continue
            if text_mentions_equipment(text, other):
                reason_bits.append(f"{label}:other:{other}")
                break

    if req_mentioned:
        if len(detected) > 1:
            return DocumentEquipmentMatch(
                match_type=MATCH_MULTI,
                detected_equipment_names=detected,
                applicable_equipment_ids=applicable_ids,
                equipment_match_reason="multi_equipment_declared:" + ",".join(reason_bits),
                request_equipment_name=req_name,
            )
        return DocumentEquipmentMatch(
            match_type=MATCH_CLEAR,
            detected_equipment_names=detected or ([req_name] if req_name else []),
            applicable_equipment_ids=applicable_ids,
            equipment_match_reason="request_equipment_declared:" + ",".join(reason_bits),
            request_equipment_name=req_name,
        )

    if detected:
        # Other registered equipment named; current not named → clear mismatch.
        return DocumentEquipmentMatch(
            match_type=MATCH_MISMATCH,
            detected_equipment_names=detected,
            applicable_equipment_ids=applicable_ids,
            equipment_match_reason="other_equipment_only:" + ",".join(reason_bits or detected),
            request_equipment_name=req_name,
        )

    # Change-history PPT naming convention: equipment name is normally present.
    # Request absent from title/scopes/filename of such a document → mismatch
    # (covers shared-folder other-equipment files even before that equipment is registered).
    file_name = getattr(item, "file_name", None) or document_basename(
        getattr(item, "file_path", None)
    )
    if (
        req_name
        and file_name
        and _CHANGE_HISTORY_NAME_RE.search(str(file_name))
        and not text_mentions_equipment(file_name, req_name)
    ):
        return DocumentEquipmentMatch(
            match_type=MATCH_MISMATCH,
            detected_equipment_names=[],
            applicable_equipment_ids=[],
            equipment_match_reason="request_absent_from_change_history_filename",
            request_equipment_name=req_name,
        )

    return DocumentEquipmentMatch(
        match_type=MATCH_UNKNOWN,
        detected_equipment_names=[],
        applicable_equipment_ids=[],
        equipment_match_reason="equipment_not_declared",
        request_equipment_name=req_name,
    )


def document_allows_official_for_equipment(
    item: Any,
    *,
    request_equipment_id: int | None,
    request_equipment_name: str | None,
    known_equipment: list[tuple[int, str]] | None = None,
    strong_unknown_grounds: bool = False,
) -> DocumentEquipmentMatch:
    """Official-promotion gate wrapper.

    - clear / multi match → allow
    - clear mismatch → deny (caller must exclude)
    - unknown → allow only when strong_unknown_grounds is True
    """
    match = analyze_document_equipment_match(
        item,
        request_equipment_id=request_equipment_id,
        request_equipment_name=request_equipment_name,
        known_equipment=known_equipment,
    )
    if match.match_type == MATCH_MISMATCH:
        return match
    if match.match_type == MATCH_UNKNOWN and not strong_unknown_grounds:
        # Treat as non-allowing for official; keep type unknown for callers.
        return match
    return match


def link_document_allows_official(
    *,
    document_name: str | None,
    document_path: str | None = None,
    change_title: str | None = None,
    request_equipment_name: str | None,
    known_equipment: list[tuple[int, str]] | None = None,
) -> DocumentEquipmentMatch:
    """Lightweight check for already-built PptLink rows (name/title only)."""

    class _Shim:
        pass

    shim = _Shim()
    shim.change_title = change_title
    shim.file_name = document_name
    shim.file_path = document_path or document_name
    shim.applicable_scopes = []
    shim.business_background = None
    shim.to_be = None
    shim.as_is = None
    shim.raw_text = change_title
    return analyze_document_equipment_match(
        shim,
        request_equipment_id=None,
        request_equipment_name=request_equipment_name,
        known_equipment=known_equipment,
    )
