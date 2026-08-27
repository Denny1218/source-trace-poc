"""CSR exact-match helper for Git <-> Change Item linking (STEP 7).

Uses the Change Item Parser's extracted `csr_no` string as-is. No SR/C prefix
hardcoding — any CSR value the parser produced is compared with identifier-
boundary matching so longer/shorter identifier-adjacent suffixes cannot
falsely trigger `csr_exact`.
"""

from __future__ import annotations

import re

# Identifier characters that must NOT abut a matched CSR token.
_IDENT_CHAR_RE = re.compile(r"[A-Za-z0-9_]")


def _is_ident_char(ch: str) -> bool:
    return bool(_IDENT_CHAR_RE.match(ch))


def csr_appears_in_text(csr: str | None, text: str | None) -> bool:
    """True when `csr` occurs in `text` as a bounded token (case-insensitive).

    A match is accepted only when both sides of the occurrence are free of
    identifier characters (A-Z / a-z / 0-9 / _). Brackets, colons, whitespace,
    and punctuation are allowed as separators.

    Examples (csr = ``SR260529_42025``):
        ``SR260529_42025 반영``   → True
        ``[SR260529_42025]``     → True
        ``CSR:SR260529_42025``   → True
        ``SR260529_420251``      → False  (longer suffix)
        ``XSR260529_42025``      → False  (leading identifier)
    """
    if not csr or not text:
        return False
    needle = csr.strip()
    if not needle:
        return False

    haystack_lower = text.lower()
    needle_lower = needle.lower()
    start = 0
    while True:
        idx = haystack_lower.find(needle_lower, start)
        if idx < 0:
            return False
        before_ok = idx == 0 or not _is_ident_char(text[idx - 1])
        after_idx = idx + len(needle)
        after_ok = after_idx >= len(text) or not _is_ident_char(text[after_idx])
        if before_ok and after_ok:
            return True
        start = idx + 1
