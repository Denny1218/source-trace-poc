import os
from pathlib import Path

from app.core.logging import get_logger
from app.services.document_path_utils import count_pptx_files, is_pptx_candidate
from app.services.git_url_utils import run_git_command
from app.services.unc_path_utils import (
    LOCAL_PATH_NOT_ALLOWED_MESSAGE,
    INVALID_UNC_MESSAGE,
    is_local_drive_path,
    is_unc_network_path,
)

logger = get_logger()

PATH_NOT_FOUND_MESSAGE = "경로를 찾을 수 없습니다."
NOT_GIT_REPO_MESSAGE = "Git Repository가 아닙니다."
DOCUMENT_NOT_READABLE_MESSAGE = (
    "Backend 서버에서 해당 네트워크 폴더에 접근할 수 없습니다."
)
NETWORK_ACCESS_MESSAGE = (
    "Backend 실행 계정의 공유 폴더 읽기 권한을 확인해 주세요."
)


def validate_local_git_path(repo_path: str) -> tuple[bool, str]:
    """Validate a local Git working tree path."""
    path = Path(repo_path)

    if not path.exists():
        return False, PATH_NOT_FOUND_MESSAGE

    if shutil_which_git() is None:
        logger.error("Git CLI not available")
        return False, "Git이 설치되어 있지 않습니다."

    try:
        result = run_git_command(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            timeout=30,
        )
    except Exception as exc:
        logger.error("Git validation failed path=%s error=%s", repo_path, exc)
        return False, NOT_GIT_REPO_MESSAGE

    if result.returncode != 0 or result.stdout.strip().lower() != "true":
        logger.info("Not a git repository path=%s", repo_path)
        return False, NOT_GIT_REPO_MESSAGE

    return True, "Git Repository 경로가 유효합니다."


def validate_git_path(repo_path: str) -> tuple[bool, str]:
    """Backward-compatible alias for local path validation."""
    return validate_local_git_path(repo_path)


def validate_document_path_basic(folder_path: str) -> tuple[bool, str]:
    """Fast UNC document_path check (format, exists, directory, read access)."""
    if is_local_drive_path(folder_path):
        return False, LOCAL_PATH_NOT_ALLOWED_MESSAGE
    if not is_unc_network_path(folder_path):
        return False, INVALID_UNC_MESSAGE

    path = Path(folder_path)

    try:
        if not path.exists():
            return False, PATH_NOT_FOUND_MESSAGE
    except OSError as exc:
        logger.warning("Document path exists check failed path=%s error=%s", folder_path, exc)
        return False, NETWORK_ACCESS_MESSAGE

    if not path.is_dir():
        return False, "변경내역서 경로는 폴더여야 합니다."

    if not os.access(path, os.R_OK):
        logger.warning("Document path not readable path=%s", folder_path)
        return False, DOCUMENT_NOT_READABLE_MESSAGE

    return True, "유효한 네트워크 폴더입니다."


def validate_document_path(folder_path: str) -> tuple[bool, str, int]:
    """Validate UNC document_path including recursive PPTX count."""
    ok, message = validate_document_path_basic(folder_path)
    if not ok:
        return False, message, 0

    path = Path(folder_path)
    try:
        pptx_count = count_pptx_files(path)
    except OSError as exc:
        logger.error("Document path list failed path=%s error=%s", folder_path, exc)
        return False, NETWORK_ACCESS_MESSAGE, 0

    return (
        True,
        f"유효한 네트워크 폴더입니다. PPTX {pptx_count}개 (하위 폴더 포함)",
        pptx_count,
    )


def shutil_which_git() -> str | None:
    import shutil

    return shutil.which("git")
