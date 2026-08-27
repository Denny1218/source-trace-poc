import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import REPOSITORIES_ROOT
from app.core.logging import get_logger
from app.db.database import get_connection
from app.schemas.git_repository import (
    GitRepositoryCreate,
    GitRepositoryResponse,
    GitRepositoryUpdate,
)
from app.services.git_url_utils import (
    ParsedRepositoryUrl,
    YONA_AUTH_FAILURE_MESSAGE,
    build_git_access_url,
    git_access_username_for_log,
    mask_repository_url,
    parse_repository_url,
    require_yona_default_username,
    run_git_command,
    safe_url_for_log,
)
from app.services.path_validation_service import validate_local_git_path, shutil_which_git

logger = get_logger()

DUPLICATE_REPOSITORY_NAME_MESSAGE = "동일 장비에 이미 등록된 Repository 이름입니다."
DUPLICATE_CANONICAL_REPOSITORY_MESSAGE = (
    "동일 장비에 이미 등록된 Repository URL입니다."
)

class GitRepositoryError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DuplicateRepositoryNameError(GitRepositoryError):
    pass


class DuplicateCanonicalRepositoryError(GitRepositoryError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _managed_clone_path(equipment_id: int, repository_id: int) -> Path:
    return REPOSITORIES_ROOT / str(equipment_id) / str(repository_id)


def _display_repository_url(row: sqlite3.Row) -> str | None:
    if row["source_type"] != "remote":
        return None
    canonical = _row_canonical(row)
    if canonical:
        return canonical
    return mask_repository_url(row["repository_url"])


def _row_to_response(row: sqlite3.Row) -> GitRepositoryResponse:
    display_url = _display_repository_url(row)
    canonical = row["canonical_repository_url"] or (
        display_url if row["source_type"] == "remote" else None
    )
    return GitRepositoryResponse(
        id=row["id"],
        equipment_id=row["equipment_id"],
        name=row["name"],
        source_type=row["source_type"],
        repository_url=display_url,
        canonical_repository_url=canonical,
        yona_username=None,
        local_path=row["local_path"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _parse_remote_input(url: str) -> ParsedRepositoryUrl:
    try:
        return parse_repository_url(url)
    except ValueError as exc:
        raise GitRepositoryError(str(exc)) from exc


def _git_access_url(parsed: ParsedRepositoryUrl) -> str:
    try:
        return build_git_access_url(parsed.canonical_url)
    except ValueError as exc:
        raise GitRepositoryError(str(exc)) from exc



def _find_canonical_duplicate(
    conn: sqlite3.Connection,
    equipment_id: int,
    canonical_url: str,
    exclude_id: int | None = None,
) -> bool:
    sql = """
        SELECT id FROM git_repository
        WHERE equipment_id = ?
          AND source_type = 'remote'
          AND canonical_repository_url = ?
    """
    params: list = [equipment_id, canonical_url]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return conn.execute(sql, params).fetchone() is not None


def list_repositories(equipment_id: int) -> list[GitRepositoryResponse]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM git_repository
            WHERE equipment_id = ?
            ORDER BY name COLLATE NOCASE
            """,
            (equipment_id,),
        ).fetchall()
        return [_row_to_response(row) for row in rows]
    finally:
        conn.close()


def get_repository(repository_id: int) -> GitRepositoryResponse | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM git_repository WHERE id = ?", (repository_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_response(row)
    finally:
        conn.close()


def get_repository_raw(repository_id: int) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM git_repository WHERE id = ?", (repository_id,)
        ).fetchone()
    finally:
        conn.close()


def _classify_ls_remote_error(stderr: str) -> str:
    text = stderr.lower()
    if (
        "authentication failed" in text
        or "401" in text
        or "403" in text
        or "invalid credentials" in text
        or "terminal prompts disabled" in text
        or "could not read username" in text
    ):
        return YONA_AUTH_FAILURE_MESSAGE
    if "not found" in text or "404" in text or "does not exist" in text:
        return "Repository를 찾을 수 없습니다."
    if "repository not found" in text:
        return "Repository를 찾을 수 없습니다."
    if "could not resolve host" in text or "connection refused" in text:
        return "Git Repository에 연결할 수 없습니다."
    return "Git Repository에 연결할 수 없습니다."


def _run_git_command(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return run_git_command(args, timeout=timeout)


def validate_remote_repository_url(repository_url: str) -> tuple[bool, str, ParsedRepositoryUrl | None]:
    if shutil_which_git() is None:
        logger.error("Git CLI not available for remote validation")
        return False, "Git이 설치되어 있지 않습니다.", None

    try:
        parsed = _parse_remote_input(repository_url)
    except GitRepositoryError as exc:
        return False, exc.message, None

    try:
        require_yona_default_username()
    except ValueError as exc:
        return False, str(exc), parsed

    access_url = _git_access_url(parsed)
    logger.info(
        "Git ls-remote access_user=%s canonical_url=%s",
        git_access_username_for_log(access_url),
        safe_url_for_log(parsed.canonical_url),
    )
    validation_started = time.perf_counter()

    try:
        result = _run_git_command(["git", "ls-remote", access_url], timeout=60)
    except Exception as exc:
        logger.error(
            "Remote validation failed url=%s error=%s",
            safe_url_for_log(access_url),
            exc,
        )
        return False, "Git 명령 실행에 실패했습니다.", parsed

    validation_ms = (time.perf_counter() - validation_started) * 1000
    logger.info("Repository remote validation elapsed_ms=%.1f", validation_ms)

    if result.returncode != 0:
        logger.info(
            "Remote validation failed url=%s stderr=%s",
            safe_url_for_log(access_url),
            (result.stderr or "").strip()[:500],
        )
        return False, _classify_ls_remote_error(result.stderr or ""), parsed

    return True, "Remote Git Repository에 연결할 수 있습니다.", parsed


def _cleanup_clone_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _clone_remote(access_url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        _cleanup_clone_dir(target)

    logger.info(
        "Git clone access_user=%s target=%s",
        git_access_username_for_log(access_url),
        target,
    )
    clone_started = time.perf_counter()
    result = _run_git_command(
        ["git", "clone", access_url.strip(), str(target)],
        timeout=600,
    )
    clone_ms = (time.perf_counter() - clone_started) * 1000
    logger.info("Repository clone elapsed_ms=%.1f", clone_ms)

    if result.returncode != 0:
        _cleanup_clone_dir(target)
        logger.error(
            "Git clone failed url=%s stderr=%s",
            safe_url_for_log(access_url),
            (result.stderr or "").strip()[:500],
        )
        msg = _classify_ls_remote_error(result.stderr or "")
        raise GitRepositoryError(msg)


def _set_remote_origin(local_path: str, access_url: str) -> None:
    result = _run_git_command(
        ["git", "-C", local_path, "remote", "set-url", "origin", access_url],
        timeout=30,
    )
    if result.returncode != 0:
        logger.error(
            "Git remote set-url failed path=%s stderr=%s",
            local_path,
            (result.stderr or "").strip()[:500],
        )
        raise GitRepositoryError("Remote origin URL 갱신에 실패했습니다.")


def create_repository(
    equipment_id: int, data: GitRepositoryCreate
) -> GitRepositoryResponse:
    flow_started = time.perf_counter()
    now = _now_iso()
    source_type = data.source_type
    stored_url: str | None = None
    canonical_url: str | None = None
    local_path = ""

    if source_type == "local":
        local_path = data.local_path.strip() if data.local_path else ""
        ok, msg = validate_local_git_path(local_path)
        if not ok:
            raise GitRepositoryError(msg)
        status = "ready"
    else:
        parsed = _parse_remote_input(data.repository_url or "")
        stored_url = parsed.canonical_url
        canonical_url = parsed.canonical_url
        status = "pending"

    conn = get_connection()
    try:
        if source_type == "remote" and canonical_url:
            if _find_canonical_duplicate(conn, equipment_id, canonical_url):
                raise DuplicateCanonicalRepositoryError(
                    DUPLICATE_CANONICAL_REPOSITORY_MESSAGE
                )

        insert_started = time.perf_counter()
        cursor = conn.execute(
            """
            INSERT INTO git_repository
                (equipment_id, name, source_type, repository_url,
                 canonical_repository_url, yona_username,
                 local_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment_id,
                data.name.strip(),
                source_type,
                stored_url,
                canonical_url,
                None,
                local_path,
                status,
                now,
                now,
            ),
        )
        conn.commit()
        repository_id = cursor.lastrowid
        insert_ms = (time.perf_counter() - insert_started) * 1000
        logger.info(
            "Repository db_insert repository_id=%s elapsed_ms=%.1f",
            repository_id,
            insert_ms,
        )
    except sqlite3.IntegrityError as exc:
        raise DuplicateRepositoryNameError(DUPLICATE_REPOSITORY_NAME_MESSAGE) from exc
    finally:
        conn.close()

    if source_type == "remote":
        clone_target = _managed_clone_path(equipment_id, repository_id)
        _update_repository_paths(repository_id, str(clone_target), "pending")

    total_ms = (time.perf_counter() - flow_started) * 1000
    logger.info(
        "Repository create flow complete equipment_id=%s repository_id=%s source_type=%s total_elapsed_ms=%.1f",
        equipment_id,
        repository_id,
        source_type,
        total_ms,
    )
    return get_repository(repository_id)  # type: ignore[return-value]


def prepare_repository(repository_id: int) -> GitRepositoryResponse:
    flow_started = time.perf_counter()
    row = get_repository_raw(repository_id)
    if row is None:
        raise GitRepositoryError("Repository를 찾을 수 없습니다.")

    if row["status"] == "ready" and row["local_path"]:
        existing = Path(row["local_path"])
        if existing.exists() and (existing / ".git").exists():
            logger.info(
                "Repository prepare skipped already ready repository_id=%s elapsed_ms=%.1f",
                repository_id,
                (time.perf_counter() - flow_started) * 1000,
            )
            return get_repository(repository_id)  # type: ignore[return-value]

    if row["source_type"] == "local":
        local_path = row["local_path"]
        ok, msg = validate_local_git_path(local_path)
        if not ok:
            _update_repository_paths(repository_id, local_path, "error")
            raise GitRepositoryError(msg)
        _update_repository_paths(repository_id, local_path, "ready")
        logger.info(
            "Repository prepare flow complete repository_id=%s source_type=local total_elapsed_ms=%.1f",
            repository_id,
            (time.perf_counter() - flow_started) * 1000,
        )
        return get_repository(repository_id)  # type: ignore[return-value]

    canonical_url = _row_canonical(row)
    if not canonical_url:
        raise GitRepositoryError("Repository URL이 설정되지 않았습니다.")

    parsed = ParsedRepositoryUrl(
        canonical_url=canonical_url,
        yona_username=None,
        display_url=row["repository_url"] or canonical_url,
        had_password=False,
    )
    clone_target = Path(row["local_path"] or _managed_clone_path(row["equipment_id"], repository_id))

    _update_repository_paths(repository_id, str(clone_target), "preparing")
    try:
        if clone_target.exists():
            git_dir = clone_target / ".git"
            if git_dir.exists():
                _update_repository_paths(repository_id, str(clone_target), "ready")
                logger.info(
                    "Repository prepare skipped existing clone repository_id=%s elapsed_ms=%.1f",
                    repository_id,
                    (time.perf_counter() - flow_started) * 1000,
                )
                return get_repository(repository_id)  # type: ignore[return-value]
            _cleanup_clone_dir(clone_target)

        _clone_remote(_git_access_url(parsed), clone_target)
        _update_repository_paths(repository_id, str(clone_target), "ready")
    except GitRepositoryError:
        _update_repository_paths(repository_id, str(clone_target), "error")
        raise

    logger.info(
        "Repository prepare flow complete repository_id=%s source_type=remote total_elapsed_ms=%.1f",
        repository_id,
        (time.perf_counter() - flow_started) * 1000,
    )
    return get_repository(repository_id)  # type: ignore[return-value]


def _update_repository_paths(
    repository_id: int, local_path: str, status: str
) -> None:
    now = _now_iso()
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE git_repository
            SET local_path = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (local_path, status, now, repository_id),
        )
        conn.commit()
    finally:
        conn.close()


def _row_canonical(row: sqlite3.Row) -> str | None:
    if row["canonical_repository_url"]:
        return row["canonical_repository_url"]
    if row["repository_url"] and row["source_type"] == "remote":
        try:
            return parse_repository_url(row["repository_url"]).canonical_url
        except ValueError:
            return None
    return None


def update_repository(
    repository_id: int, data: GitRepositoryUpdate
) -> GitRepositoryResponse | None:
    row = get_repository_raw(repository_id)
    if row is None:
        return None

    now = _now_iso()
    source_type = row["source_type"]
    display_url = row["repository_url"]
    canonical_url = row["canonical_repository_url"]
    local_path = row["local_path"]
    status = row["status"]

    if source_type == "local":
        if data.local_path:
            local_path = data.local_path.strip()
            ok, msg = validate_local_git_path(local_path)
            if not ok:
                raise GitRepositoryError(msg)
            status = "ready"
    elif data.repository_url:
        parsed_new = _parse_remote_input(data.repository_url)
        old_canonical = _row_canonical(row)

        if old_canonical and parsed_new.canonical_url == old_canonical:
            display_url = parsed_new.canonical_url
            canonical_url = parsed_new.canonical_url
            logger.info(
                "Repository update metadata only repository_id=%s same_canonical=true",
                repository_id,
            )
        else:
            conn = get_connection()
            try:
                if _find_canonical_duplicate(
                    conn, row["equipment_id"], parsed_new.canonical_url, repository_id
                ):
                    raise DuplicateCanonicalRepositoryError(
                        DUPLICATE_CANONICAL_REPOSITORY_MESSAGE
                    )
            finally:
                conn.close()

            display_url = parsed_new.canonical_url
            canonical_url = parsed_new.canonical_url
            clone_target = _managed_clone_path(row["equipment_id"], repository_id)
            if local_path:
                _cleanup_clone_dir(Path(local_path))
            local_path = str(clone_target)
            status = "pending"
            logger.info(
                "Repository URL changed repository_id=%s status=pending (prepare required)",
                repository_id,
            )

    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE git_repository
            SET name = ?, repository_url = ?, canonical_repository_url = ?,
                yona_username = ?, local_path = ?, status = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data.name.strip(),
                display_url,
                canonical_url,
                None,
                local_path,
                status,
                now,
                repository_id,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise DuplicateRepositoryNameError(DUPLICATE_REPOSITORY_NAME_MESSAGE) from exc
    finally:
        conn.close()

    return get_repository(repository_id)


def delete_repository(repository_id: int) -> bool:
    row = get_repository_raw(repository_id)
    if row is None:
        return False

    if row["source_type"] == "remote" and row["local_path"]:
        _cleanup_clone_dir(Path(row["local_path"]))

    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM git_repository WHERE id = ?", (repository_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_working_path(repository_id: int) -> str:
    row = get_repository_raw(repository_id)
    if row is None:
        raise GitRepositoryError("Repository를 찾을 수 없습니다.")
    if row["status"] != "ready":
        raise GitRepositoryError("Repository가 준비되지 않았습니다.")
    path = row["local_path"]
    if not path:
        raise GitRepositoryError("Repository 경로가 설정되지 않았습니다.")
    return path


def fetch_remote_repository(repository_id: int) -> None:
    row = get_repository_raw(repository_id)
    if row is None:
        raise GitRepositoryError("Repository를 찾을 수 없습니다.")
    if row["source_type"] != "remote":
        return

    repo_path = row["local_path"]
    if not repo_path or not Path(repo_path).exists():
        raise GitRepositoryError("Remote Clone 경로가 존재하지 않습니다.")

    canonical = _row_canonical(row)
    if canonical:
        parsed = ParsedRepositoryUrl(
            canonical_url=canonical,
            yona_username=None,
            display_url=row["repository_url"] or canonical,
            had_password=False,
        )
        _set_remote_origin(repo_path, _git_access_url(parsed))

    result = _run_git_command(
        ["git", "-C", repo_path, "fetch", "--all", "--prune"],
        timeout=300,
    )
    if result.returncode != 0:
        logger.error(
            "Git fetch failed repository_id=%s stderr=%s",
            repository_id,
            (result.stderr or "").strip()[:500],
        )
        msg = _classify_ls_remote_error(result.stderr or "")
        raise GitRepositoryError(msg)
