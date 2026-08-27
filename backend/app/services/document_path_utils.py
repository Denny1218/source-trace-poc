"""Shared document path file iteration (aligned with STEP 5 PPT candidate policy)."""

from __future__ import annotations

from pathlib import Path


def is_pptx_candidate(path: Path) -> bool:
    if path.name.startswith("~$"):
        return False
    return path.suffix.lower() == ".pptx"


def iter_pptx_files(root: Path):
    """Recursively yield .pptx files under root (case-insensitive suffix)."""
    for path in root.rglob("*"):
        try:
            if path.is_file() and is_pptx_candidate(path):
                yield path
        except OSError:
            continue


def count_pptx_files(root: Path) -> int:
    return sum(1 for _ in iter_pptx_files(root))
