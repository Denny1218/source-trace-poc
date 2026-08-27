"""Windows UNC network path utilities for document_path policy."""

from __future__ import annotations

import os
from pathlib import Path

LOCAL_PATH_NOT_ALLOWED_MESSAGE = (
    "변경내역서 폴더는 네트워크 공유 경로만 사용할 수 있습니다."
)
INVALID_UNC_MESSAGE = "유효한 UNC 네트워크 경로가 아닙니다."
UNC_HELP_EXAMPLE = r"예: \\서버명\공유폴더\장비명"


def normalize_unc_path(path_str: str) -> str:
    cleaned = path_str.strip().strip('"').replace("/", "\\")
    while len(cleaned) > 3 and cleaned.endswith("\\"):
        cleaned = cleaned.rstrip("\\")
    return cleaned


def is_unc_network_path(path_str: str) -> bool:
    """True when path is \\server\\share or deeper (not a drive letter path)."""
    normalized = normalize_unc_path(path_str)
    if not normalized.startswith("\\\\"):
        return False
    parts = [part for part in normalized[2:].split("\\") if part]
    return len(parts) >= 2


def is_local_drive_path(path_str: str) -> bool:
    normalized = normalize_unc_path(path_str)
    return len(normalized) >= 2 and normalized[1] == ":" and normalized[0].isalpha()


def normalize_path(path_str: str) -> Path:
    cleaned = normalize_unc_path(path_str)
    path = Path(cleaned)
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return path.absolute()


def _same_path(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except OSError:
        return str(left).rstrip("\\/").lower() == str(right).rstrip("\\/").lower()


def is_path_under_root(path: Path, root: Path) -> bool:
    if _same_path(path, root):
        return True
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
