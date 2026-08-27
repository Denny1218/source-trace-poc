"""Function/symbol normalization and matching for Git <-> Change Item linking.

Initial rule-based normalization only. No C/C++ parser, no template/namespace
parsing, no function-signature parser.
"""

from __future__ import annotations

import re

_TRAILING_CALL_RE = re.compile(r"\(\s*\)\s*$")
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Whitespace only between identifier characters (not Hangul sentence spaces).
_IDENT_INTERNAL_WS_RE = re.compile(r"(?<=[A-Za-z0-9_])[\t\n\r\f\v ]+(?=[A-Za-z0-9_])")
# Call-site / declaration form: identifier( — allows mid-identifier WS.
_SPACED_IDENT_CALL_RE = re.compile(
    r"\b([A-Za-z_](?:[A-Za-z0-9_]|[\t\n\r\f\v ]+(?=[A-Za-z0-9_]))+)\s*\("
)
# Bare identifier (only for dedicated function-list cells, not raw path blobs).
_SPACED_IDENT_RE = re.compile(
    r"\b([A-Za-z_](?:[A-Za-z0-9_]|[\t\n\r\f\v ]+(?=[A-Za-z0-9_]))+)\b"
)
_FILE_EXT_RE = re.compile(r"\.(c|h|cpp|hpp|cc|cxx)\b", re.I)
_IDENT_START_RE = re.compile(r"^[A-Za-z_]")


def normalize_symbol(raw: str | None) -> str:
    """Normalize a PPT/Git function name for comparison.

    Applied only to Symbol/identifier candidates — not to free-form sentences.

    - strip leading/trailing whitespace
    - strip trailing empty ``()``
    - remove spaces / tabs / newlines inserted *inside* a C identifier
      (e.g. ``foo_ bar``, ``foo_\\nbar``, ``birthday_ usertype``)
    - case is preserved; callers compare case-insensitively when needed
    """
    if not raw:
        return ""
    text = str(raw).strip()
    text = _TRAILING_CALL_RE.sub("", text).strip()
    # Collapse identifier-internal whitespace only (between [A-Za-z0-9_]).
    text = _IDENT_INTERNAL_WS_RE.sub("", text)
    text = text.strip()
    return text


def symbols_equivalent(a: str | None, b: str | None) -> bool:
    """True when two raw symbols normalize to the same identifier (case-insensitive)."""
    na = normalize_symbol(a)
    nb = normalize_symbol(b)
    if not na or not nb:
        return False
    if not is_valid_symbol(na) or not is_valid_symbol(nb):
        return False
    return na.lower() == nb.lower()


def is_suffix_only_symbol(normalized: str) -> bool:
    """True for truncated leading-underscore fragments like ``_usertype``."""
    if not normalized:
        return False
    # Single leading-underscore segment (no further ``_``) is a wrap fragment.
    if normalized.startswith("_") and normalized.count("_") == 1:
        return True
    return False


def drop_suffix_symbol_duplicates(symbols: list[str]) -> list[str]:
    """Remove suffix-only fragments when a longer parent symbol is present."""
    norms = [(s, normalize_symbol(s)) for s in symbols]
    norms = [(s, n) for s, n in norms if n and is_valid_symbol(n)]
    drop: set[str] = set()
    for _s1, n1 in norms:
        if is_suffix_only_symbol(n1):
            drop.add(n1.lower())
            continue
        for _s2, n2 in norms:
            if n1.lower() == n2.lower():
                continue
            if len(n2) <= len(n1):
                continue
            # n1 is underscore-boundary suffix of n2.
            if n2.lower().endswith(n1.lower()) and n2.lower()[: -len(n1)].endswith("_"):
                drop.add(n1.lower())
            elif n1.startswith("_") and n2.lower().endswith(n1.lower()):
                drop.add(n1.lower())
    out: list[str] = []
    seen: set[str] = set()
    for s, n in norms:
        key = n.lower()
        if key in drop or key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def is_valid_symbol(normalized: str) -> bool:
    """True when normalized text looks like a real C/C++ identifier."""
    return bool(normalized) and bool(_VALID_IDENTIFIER_RE.match(normalized))


def looks_like_path_or_source_file(text: str | None) -> bool:
    """True when text is a path or C/C++ source filename (not a function name)."""
    if not text:
        return False
    t = str(text).strip()
    if not t:
        return False
    if re.search(r"[/\\]", t):
        return True
    if _FILE_EXT_RE.search(t):
        return True
    return False


def join_underscore_wrapped_lines(lines: list[str]) -> list[str]:
    """Join wrapped identifier lines only when prev ends with ``_`` and next is ident.

    Different function items / path lines must not be merged.
    """
    out: list[str] = []
    buf = ""
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if buf:
                out.append(buf)
                buf = ""
            continue
        if looks_like_path_or_source_file(line):
            if buf:
                out.append(buf)
                buf = ""
            out.append(line)
            continue
        if buf and buf.rstrip().endswith("_") and _IDENT_START_RE.match(line):
            buf = buf.rstrip() + line.lstrip()
            continue
        # Orphan leading-underscore fragment on next line (``birthday`` + ``_usertype``).
        if (
            buf
            and line.startswith("_")
            and len(line) > 1
            and _IDENT_START_RE.match(line[1:])
            and re.search(r"[A-Za-z0-9_]$", buf.rstrip())
        ):
            buf = buf.rstrip() + line.lstrip()
            continue
        if buf:
            out.append(buf)
        buf = line
    if buf:
        out.append(buf)
    return out


def iter_call_symbol_candidates(text: str | None) -> list[str]:
    """Extract symbols only from ``identifier(...`` forms (allows internal WS)."""
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for m in _SPACED_IDENT_CALL_RE.finditer(str(text)):
        cand = m.group(1)
        norm = normalize_symbol(cand)
        if not norm or not is_valid_symbol(norm):
            continue
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(cand)
    return found


def iter_symbol_candidates(
    text: str | None,
    *,
    call_forms_only: bool = False,
) -> list[str]:
    """Extract identifier-like candidates from a PPT cell (allows internal WS).

    When ``call_forms_only`` is True (raw_text / mixed cells), only
    ``identifier(`` forms are returned — path stems are never candidates.
    """
    if not text:
        return []
    if call_forms_only or looks_like_path_or_source_file(text):
        # Path-bearing blobs: call forms only (never bare path stems).
        return iter_call_symbol_candidates(text)

    found: list[str] = []
    seen: set[str] = set()
    raw = str(text)
    for rx in (_SPACED_IDENT_CALL_RE, _SPACED_IDENT_RE):
        for m in rx.finditer(raw):
            cand = m.group(1)
            norm = normalize_symbol(cand)
            if not norm or not is_valid_symbol(norm):
                continue
            key = norm.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(cand)
    whole = normalize_symbol(raw)
    if is_valid_symbol(whole) and whole.lower() not in seen:
        found.append(raw.strip())
    return found


def symbol_appears_in_text(symbol: str, text: str | None) -> bool:
    """Search for symbol in text, allowing PPT mid-identifier whitespace.

    Comparison is case-insensitive. Does not strip spaces from Korean prose —
    only matches the identifier pattern with optional internal whitespace.
    """
    normalized = normalize_symbol(symbol)
    if not normalized or not text or not is_valid_symbol(normalized):
        return False
    # Contiguous form.
    if re.search(r"\b" + re.escape(normalized) + r"\b", text, flags=re.IGNORECASE):
        return True
    # Flexible form: optional whitespace between each identifier character.
    flex = r"[\t\n\r\f\v ]*".join(re.escape(ch) for ch in normalized)
    return bool(re.search(r"\b" + flex + r"\b", text, flags=re.IGNORECASE))
