"""Source code path normalization for Git <-> Change Item file matching (STEP 7).

Not to be confused with `unc_path_utils.py`, which handles Windows UNC
*document* (변경내역서) paths on the frontend/backend document-path features.
This module compares source *code* paths as they appear in Git diffs/file
changes and in Change Item "소스/함수명" fields — both of which may be partial
(relative) paths rooted at different depths of the same repository tree.
"""

from __future__ import annotations

from enum import Enum


class PathMatchLevel(str, Enum):
    EXACT = "EXACT"
    SUFFIX = "SUFFIX"
    BASENAME = "BASENAME"
    NONE = "NONE"


_LEVEL_RANK = {
    PathMatchLevel.NONE: 0,
    PathMatchLevel.BASENAME: 1,
    PathMatchLevel.SUFFIX: 2,
    PathMatchLevel.EXACT: 3,
}


def normalize_source_path(path: str | None) -> str:
    """Normalize a source code path for comparison.

    Rules:
    - backslash -> forward slash
    - collapse duplicate slashes
    - strip leading "./"
    - strip leading/trailing slashes and whitespace
    - lowercase

    Case policy: source paths are compared case-insensitively. This matches
    the existing STEP 4 policy in `trace_service._normalize_path`/`_paths_match`
    (Git file_path vs user query file_path), so Git<->Change Item file
    matching stays consistent with the already-established Git<->Query file
    matching behavior in this codebase.
    """
    if not path:
        return ""
    text = path.strip().replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")
    if text.startswith("./"):
        text = text[2:]
    text = text.strip("/")
    return text.lower()


def source_path_basename(normalized_path: str) -> str:
    if not normalized_path:
        return ""
    return normalized_path.rsplit("/", 1)[-1]


def source_path_match_level(
    git_path: str | None, change_item_path: str | None
) -> PathMatchLevel:
    """Classify how strongly two source paths identify the same file.

    EXACT    - normalized paths are identical
    SUFFIX   - one normalized path is a trailing directory-aligned subset of
               the other (e.g. "fare/src/fare_calc.c" is a suffix of
               "subwaylib/fare/src/fare_calc.c")
    BASENAME - only the final path segment (filename incl. extension) matches
    NONE     - no structural relationship (plain substring matches do not
               count — see STEP 7 report)
    """
    a = normalize_source_path(git_path)
    b = normalize_source_path(change_item_path)
    if not a or not b:
        return PathMatchLevel.NONE

    if a == b:
        return PathMatchLevel.EXACT

    if a.endswith("/" + b) or b.endswith("/" + a):
        return PathMatchLevel.SUFFIX

    if source_path_basename(a) == source_path_basename(b):
        return PathMatchLevel.BASENAME

    return PathMatchLevel.NONE


def best_match_level(
    levels: list[PathMatchLevel],
) -> PathMatchLevel:
    """Return the strongest (highest-rank) level among candidates."""
    best = PathMatchLevel.NONE
    for level in levels:
        if _LEVEL_RANK[level] > _LEVEL_RANK[best]:
            best = level
        if best == PathMatchLevel.EXACT:
            break
    return best


def level_rank(level: PathMatchLevel) -> int:
    return _LEVEL_RANK[level]
