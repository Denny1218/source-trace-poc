"""Git 변경 이력 수집 서비스 (Repository 단위).

Merge Commit parent_hash 정책:
    parent가 여러 개인 경우 첫 번째 parent hash만 parent_hash에 저장한다.

Binary 파일 정책:
    - file_path, change_type은 저장
    - additions/deletions는 NULL
    - diff에는 "[binary file]" 플레이스홀더만 저장 (바이너리 내용 미저장)
"""

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass

from app.core.logging import get_logger
from app.db.database import get_connection
from app.services.equipment_service import get_equipment
from app.services.git_repository_service import (
    GitRepositoryError,
    fetch_remote_repository,
    get_repository,
    get_working_path,
    list_repositories,
    validate_local_git_path,
)
from app.services.git_url_utils import git_subprocess_env
from app.services.path_validation_service import NOT_GIT_REPO_MESSAGE

logger = get_logger()

BINARY_DIFF_PLACEHOLDER = "[binary file]"
GIT_ENCODING = "utf-8"

_STATUS_MAP = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "modified",
    "T": "modified",
}


class GitSyncError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class FileChangeInfo:
    file_path: str
    change_type: str
    additions: int | None
    deletions: int | None
    is_binary: bool


@dataclass
class SyncResult:
    equipment_id: int
    repository_id: int | None
    scanned_commits: int
    new_commits: int
    skipped_commits: int
    new_changes: int
    status: str = "completed"


def _run_git(args: list[str], repo_path: str) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", repo_path, *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=GIT_ENCODING,
            errors="replace",
            timeout=120,
            env=git_subprocess_env(),
        )
    except Exception as exc:
        logger.error(
            "Git command error command=%s return_code=exception error=%s",
            " ".join(command),
            exc,
        )
        raise GitSyncError("Git 명령 실행 중 오류가 발생했습니다.") from exc

    if result.returncode != 0:
        logger.error(
            "Git command error command=%s return_code=%s stderr=%s",
            " ".join(command),
            result.returncode,
            (result.stderr or "").strip()[:500],
        )
        raise GitSyncError("Git 저장소 정보를 읽는 중 오류가 발생했습니다.")

    return result


def get_existing_commit_hashes(repository_id: int) -> set[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT commit_hash FROM git_commit WHERE repository_id = ?",
            (repository_id,),
        ).fetchall()
        return {row["commit_hash"] for row in rows}
    finally:
        conn.close()


def list_all_commit_hashes(repo_path: str) -> list[str]:
    result = _run_git(["log", "--all", "--pretty=format:%H", "--reverse"], repo_path)
    if not result.stdout.strip():
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_commit_metadata(repo_path: str, commit_hash: str) -> dict:
    date_result = _run_git(
        ["log", "-1", "--pretty=format:%aI", commit_hash], repo_path
    )
    author_result = _run_git(
        ["log", "-1", "--pretty=format:%an", commit_hash], repo_path
    )
    message_result = _run_git(
        ["log", "-1", "--pretty=format:%B", commit_hash], repo_path
    )
    parent_result = _run_git(
        ["log", "-1", "--pretty=format:%P", commit_hash], repo_path
    )

    parents = parent_result.stdout.strip().split()
    parent_hash = parents[0] if parents else None

    return {
        "commit_hash": commit_hash,
        "commit_date": date_result.stdout.strip(),
        "author": author_result.stdout.strip(),
        "message": message_result.stdout.rstrip("\n"),
        "parent_hash": parent_hash,
    }


def _parse_name_status(repo_path: str, commit_hash: str) -> list[FileChangeInfo]:
    result = _run_git(
        ["show", "--name-status", "--pretty=format:", commit_hash],
        repo_path,
    )
    numstat_map = _parse_numstat(repo_path, commit_hash)

    changes: list[FileChangeInfo] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_code = parts[0]
        change_type_key = status_code[0] if status_code else "M"
        change_type = _STATUS_MAP.get(change_type_key, "modified")

        if change_type == "renamed" and len(parts) >= 3:
            file_path = parts[2]
        elif change_type == "deleted" and len(parts) >= 2:
            file_path = parts[1]
        elif len(parts) >= 2:
            file_path = parts[1]
        else:
            continue

        stat_key = _resolve_numstat_key(file_path, numstat_map)
        additions, deletions, is_binary = numstat_map.get(
            stat_key, (None, None, False)
        )
        if is_binary:
            additions, deletions = None, None

        changes.append(
            FileChangeInfo(
                file_path=file_path,
                change_type=change_type,
                additions=additions,
                deletions=deletions,
                is_binary=is_binary,
            )
        )

    return changes


def _parse_numstat(
    repo_path: str, commit_hash: str
) -> dict[str, tuple[int | None, int | None, bool]]:
    result = _run_git(["show", "--numstat", "--pretty=format:", commit_hash], repo_path)
    stats: dict[str, tuple[int | None, int | None, bool]] = {}

    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add_raw, del_raw, path = parts[0], parts[1], parts[2]
        if add_raw == "-" and del_raw == "-":
            stats[path] = (None, None, True)
        else:
            stats[path] = (int(add_raw), int(del_raw), False)

    return stats


def _resolve_numstat_key(file_path: str, numstat_map: dict) -> str:
    if file_path in numstat_map:
        return file_path
    for key in numstat_map:
        if "=>" in key:
            new_part = key.split("=>")[-1].strip()
            if new_part == file_path or new_part.endswith("/" + file_path):
                return key
    return file_path


def fetch_commit_file_diff(repo_path: str, commit_hash: str, file_path: str) -> str | None:
    """Public wrapper for on-demand exact file patch (lifecycle diff fallback)."""
    if not repo_path or not commit_hash or not file_path:
        return None
    text = _get_file_diff(repo_path, commit_hash, file_path)
    return text if text else None


def _get_file_diff(repo_path: str, commit_hash: str, file_path: str) -> str:
    if file_path:
        result = _run_git(
            [
                "show",
                commit_hash,
                "--pretty=format:",
                "--no-color",
                "--unified=3",
                "--",
                file_path,
            ],
            repo_path,
        )
    else:
        return ""

    raw = result.stdout
    if "Binary files" in raw:
        return BINARY_DIFF_PLACEHOLDER

    return _extract_file_diff_body(raw)


def _extract_file_diff_body(raw_diff: str) -> str:
    lines = raw_diff.splitlines()
    body_lines: list[str] = []
    in_body = False

    for line in lines:
        if line.startswith("@@"):
            in_body = True
            body_lines.append(line)
        elif in_body:
            if line.startswith(("+", "-", " ")):
                body_lines.append(line)
            elif line.startswith("\\ No newline"):
                body_lines.append(line)

    if body_lines:
        return "\n".join(body_lines)

    cleaned = []
    for line in lines:
        if line.startswith("diff --git"):
            continue
        if line.startswith("index "):
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def _insert_commit(conn: sqlite3.Connection, repository_id: int, meta: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO git_commit
            (repository_id, commit_hash, commit_date, author, message, parent_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            repository_id,
            meta["commit_hash"],
            meta["commit_date"],
            meta["author"],
            meta["message"],
            meta["parent_hash"],
        ),
    )
    return cursor.lastrowid


def _insert_changes(
    conn: sqlite3.Connection,
    commit_id: int,
    repo_path: str,
    commit_hash: str,
    changes: list[FileChangeInfo],
) -> int:
    count = 0
    for change in changes:
        if change.is_binary:
            diff_text = BINARY_DIFF_PLACEHOLDER
        elif change.change_type == "deleted":
            diff_text = _get_file_diff(repo_path, commit_hash, change.file_path)
            if not diff_text:
                diff_text = ""
        else:
            diff_text = _get_file_diff(repo_path, commit_hash, change.file_path)

        conn.execute(
            """
            INSERT INTO git_change
                (commit_id, file_path, change_type, additions, deletions, diff)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                commit_id,
                change.file_path,
                change.change_type,
                change.additions,
                change.deletions,
                diff_text,
            ),
        )
        count += 1
    return count


def sync_repository_git(repository_id: int) -> SyncResult:
    repo = get_repository(repository_id)
    if repo is None:
        raise GitSyncError("Repository를 찾을 수 없습니다.")

    if repo.status != "ready":
        raise GitSyncError("Repository가 준비되지 않았습니다.")

    try:
        repo_path = get_working_path(repository_id)
    except GitRepositoryError as exc:
        raise GitSyncError(exc.message) from exc

    if repo.source_type == "remote":
        try:
            fetch_remote_repository(repository_id)
        except GitRepositoryError as exc:
            raise GitSyncError(exc.message) from exc
    else:
        git_ok, git_msg = validate_local_git_path(repo_path)
        if not git_ok:
            raise GitSyncError(git_msg or NOT_GIT_REPO_MESSAGE)

    logger.info(
        "Git sync started repository_id=%s equipment_id=%s name=%s",
        repository_id,
        repo.equipment_id,
        repo.name,
    )

    existing_hashes = get_existing_commit_hashes(repository_id)
    all_hashes = list_all_commit_hashes(repo_path)

    scanned = len(all_hashes)
    skipped = 0
    new_commits = 0
    new_changes = 0

    conn = get_connection()
    try:
        for commit_hash in all_hashes:
            if commit_hash in existing_hashes:
                skipped += 1
                continue

            meta = get_commit_metadata(repo_path, commit_hash)
            file_changes = _parse_name_status(repo_path, commit_hash)

            commit_id = _insert_commit(conn, repository_id, meta)
            inserted = _insert_changes(
                conn, commit_id, repo_path, commit_hash, file_changes
            )
            conn.commit()

            existing_hashes.add(commit_hash)
            new_commits += 1
            new_changes += inserted

    except sqlite3.IntegrityError as exc:
        conn.rollback()
        logger.error(
            "Git sync integrity error repository_id=%s error=%s", repository_id, exc
        )
        raise GitSyncError("Git 이력 저장 중 중복 또는 무결성 오류가 발생했습니다.") from exc
    except GitSyncError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        logger.error("Git sync failed repository_id=%s error=%s", repository_id, exc)
        raise GitSyncError("Git 동기화 중 오류가 발생했습니다.") from exc
    finally:
        conn.close()

    logger.info(
        "Git sync completed repository_id=%s scanned_commits=%s new_commits=%s "
        "skipped_commits=%s new_changes=%s",
        repository_id,
        scanned,
        new_commits,
        skipped,
        new_changes,
    )

    return SyncResult(
        equipment_id=repo.equipment_id,
        repository_id=repository_id,
        scanned_commits=scanned,
        new_commits=new_commits,
        skipped_commits=skipped,
        new_changes=new_changes,
    )


def sync_equipment_git(equipment_id: int) -> SyncResult:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise GitSyncError("장비를 찾을 수 없습니다.")

    repositories = list_repositories(equipment_id)
    ready_repos = [r for r in repositories if r.status == "ready"]
    if not ready_repos:
        raise GitSyncError("동기화할 Git Repository가 없습니다.")

    total = SyncResult(
        equipment_id=equipment_id,
        repository_id=None,
        scanned_commits=0,
        new_commits=0,
        skipped_commits=0,
        new_changes=0,
    )

    for repo in ready_repos:
        result = sync_repository_git(repo.id)
        total.scanned_commits += result.scanned_commits
        total.new_commits += result.new_commits
        total.skipped_commits += result.skipped_commits
        total.new_changes += result.new_changes

    return total


def count_commits_for_equipment(equipment_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM git_commit gc
            JOIN git_repository gr ON gr.id = gc.repository_id
            WHERE gr.equipment_id = ?
            """,
            (equipment_id,),
        ).fetchone()
        return row["cnt"]
    finally:
        conn.close()


def count_changes_for_equipment(equipment_id: int) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM git_change gch
            JOIN git_commit gc ON gch.commit_id = gc.id
            JOIN git_repository gr ON gr.id = gc.repository_id
            WHERE gr.equipment_id = ?
            """,
            (equipment_id,),
        ).fetchone()
        return row["cnt"]
    finally:
        conn.close()
