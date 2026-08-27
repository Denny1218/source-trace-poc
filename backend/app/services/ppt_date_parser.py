"""Extract dates from PPT file/folder path strings.

Supported formats:
    20240315
    2024-03-15
    2024_03_15
    2024.03.15

Invalid dates (e.g. 20241345) are skipped silently.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

_DATE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)"), "ymd"),
    (re.compile(r"(20\d{2})[-_.](0[1-9]|1[0-2])[-_.](0[1-9]|[12]\d|3[01])"), "ymd_sep"),
]

# Preserve short uppercase tokens when filtering keywords for matching
SHORT_UPPER_TOKENS = frozenset({"IO", "ID", "AG"})


def parse_date_from_text(text: str) -> date | None:
    """Return first valid date found in text, or None."""
    for pattern, kind in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            if kind == "ymd":
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            else:
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return date(y, m, d)
        except ValueError:
            continue
    return None


def extract_dates_from_path(file_path: str, document_root: str) -> tuple[date | None, date | None]:
    """Return (filename_date, folder_date) from absolute path."""
    from pathlib import Path

    path = Path(file_path)
    filename_date = parse_date_from_text(path.stem)

    folder_date: date | None = None
    try:
        rel = path.relative_to(document_root)
        for part in rel.parent.parts:
            found = parse_date_from_text(part)
            if found:
                folder_date = found
                break
    except ValueError:
        pass

    return filename_date, folder_date


def parse_iso_date(value: str) -> date:
    """Parse YYYY-MM-DD or ISO datetime string to date."""
    cleaned = value.strip()
    if "T" in cleaned:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00")).date()
    return date.fromisoformat(cleaned[:10])


def range_center(date_from: str, date_to: str) -> date:
    start = parse_iso_date(date_from)
    end = parse_iso_date(date_to)
    if end < start:
        start, end = end, start
    delta_days = (end - start).days
    return start + timedelta(days=delta_days // 2)
