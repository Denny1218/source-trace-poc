"""PROJECT_SPEC v2.6 — shared equipment Repository / path resolver.

Function history and selection-code analysis MUST use this module so the same
equipment + repo-relative path resolves to the same server clone.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from app.core.logging import get_logger
from app.services.git_repository_service import get_repository, list_repositories
from app.services.git_url_utils import git_subprocess_env

logger = get_logger()

CODE_AMBIGUOUS = "AMBIGUOUS_REPOSITORY"
CODE_NOT_FOUND = "REPOSITORY_NOT_FOUND"
CODE_INVALID = "INVALID_PATH"
CODE_HINT_INVALID = "REPO_HINT_INVALID"


class RepositoryResolveError(Exception):
    """User-facing repository resolution failure."""

    def __init__(self, message: str, *, code: str = CODE_NOT_FOUND):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ResolvedRepository:
    repository_id: int
    repository_name: str
    repo_path: str
    rel_path: str
    method: str


def _posix(path: str) -> str:
    return (path or "").replace("\\", "/").strip()


def normalize_repo_relative_path(rel_path: str) -> str:
    """Normalize a repo-relative path; reject empty / absolute / traversal."""
    raw = _posix(rel_path).lstrip("/")
    if not raw:
        raise RepositoryResolveError("repo_relative_path가 비어 있습니다.", code=CODE_INVALID)
    if raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise RepositoryResolveError(
            "repo_relative_path는 Repository 상대경로여야 합니다.",
            code=CODE_INVALID,
        )
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise RepositoryResolveError(
            "repo_relative_path에 상위 경로 탐색(`..`)은 허용되지 않습니다.",
            code=CODE_INVALID,
        )
    return "/".join(parts)


def safe_join_under_repo(repo_path: str, rel_path: str) -> str:
    """Join and resolve; raise if the result escapes the repository root."""
    root = os.path.realpath(repo_path)
    target = os.path.realpath(os.path.join(root, rel_path.replace("/", os.sep)))
    root_cmp = root.lower() if os.name == "nt" else root
    target_cmp = target.lower() if os.name == "nt" else target
    if target_cmp != root_cmp and not target_cmp.startswith(root_cmp + os.sep):
        raise RepositoryResolveError(
            "선택한 파일이 장비 Git Repository 내부에서 확인되지 않았습니다.",
            code=CODE_INVALID,
        )
    return target


def _run_git(repo_path: str, args: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", repo_path, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=git_subprocess_env(),
    )


def file_exists_in_repo(repo_path: str, rel_path: str, revision: str = "HEAD") -> bool:
    try:
        result = _run_git(repo_path, ["cat-file", "-e", f"{revision}:{rel_path}"], timeout=15)
        if result.returncode == 0:
            return True
    except Exception:
        pass
    return os.path.isfile(os.path.join(repo_path, rel_path.replace("/", os.sep)))


def _ready_repos(equipment_id: int) -> list:
    try:
        repos = [r for r in list_repositories(equipment_id) if r.status == "ready"]
    except Exception as exc:
        logger.error("Repository list failed equipment_id=%s error=%s", equipment_id, exc)
        raise RepositoryResolveError(
            "장비 Repository 정보를 조회하지 못했습니다.",
            code=CODE_NOT_FOUND,
        ) from exc
    if not repos:
        raise RepositoryResolveError(
            "장비에 등록된 Git Repository가 없습니다.",
            code=CODE_NOT_FOUND,
        )
    return repos


def _repo_worktree_ok(repo_path: str) -> bool:
    if not repo_path or not os.path.isdir(repo_path):
        return False
    if os.path.isdir(os.path.join(repo_path, ".git")) or os.path.isfile(
        os.path.join(repo_path, ".git")
    ):
        return True
    try:
        probe = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"], timeout=15)
        return probe.returncode == 0
    except Exception:
        return False


def strip_local_path_prefix(file_path: str, equipment_id: int) -> tuple[str | None, str]:
    """Best-effort abs → repo-relative using registered local_path prefixes.

    Same order as historical ``normalize_file_path`` repository_relative step.
    Never raises.
    """
    posix = _posix(file_path)
    if not posix or equipment_id is None:
        return None, "none"
    try:
        repos = list_repositories(equipment_id)
    except Exception:
        return None, "none"
    for repo in repos:
        local = _posix(getattr(repo, "local_path", None) or "").rstrip("/")
        if not local:
            continue
        if posix.lower() == local.lower():
            return "", "repository_relative"
        if posix.lower().startswith(local.lower() + "/"):
            return posix[len(local) + 1 :], "repository_relative"
    return None, "none"


def coerce_repo_relative_path(
    *,
    equipment_id: int,
    repo_relative_path: str | None = None,
    file_path: str | None = None,
) -> str:
    """Derive a repo-relative path from official or legacy inputs."""
    if repo_relative_path and repo_relative_path.strip():
        return normalize_repo_relative_path(repo_relative_path)

    raw = _posix(file_path or "")
    if not raw:
        raise RepositoryResolveError(
            "repo_relative_path가 필요합니다.",
            code=CODE_INVALID,
        )

    stripped, method = strip_local_path_prefix(raw, equipment_id)
    if method == "repository_relative" and stripped is not None:
        if not stripped:
            raise RepositoryResolveError(
                "파일 경로가 Repository 루트입니다.",
                code=CODE_INVALID,
            )
        return normalize_repo_relative_path(stripped)

    # Already relative (no drive / leading root only)
    if not (raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":")):
        return normalize_repo_relative_path(raw)

    # Absolute client path (Remote-SSH): keep last segments as soft relative
    parts = [p for p in raw.split("/") if p]
    if len(parts) >= 3:
        return normalize_repo_relative_path("/".join(parts[-3:]))
    if parts:
        return normalize_repo_relative_path(parts[-1])
    raise RepositoryResolveError("유효한 파일 경로가 없습니다.", code=CODE_INVALID)


def _try_resolve_in_repo(
    repo,
    rel: str,
    *,
    revision: str,
    method: str,
) -> ResolvedRepository | None:
    repo_path = (getattr(repo, "local_path", None) or "").strip()
    if not _repo_worktree_ok(repo_path):
        return None
    try:
        safe_join_under_repo(repo_path, rel)
    except RepositoryResolveError:
        return None
    if not file_exists_in_repo(repo_path, rel, revision):
        return None
    return ResolvedRepository(
        repository_id=int(repo.id),
        repository_name=str(repo.name),
        repo_path=repo_path,
        rel_path=rel,
        method=method,
    )


def resolve_equipment_repository(
    *,
    equipment_id: int,
    repo_relative_path: str | None = None,
    repo_id_hint: int | None = None,
    file_path: str | None = None,
    revision: str = "HEAD",
) -> ResolvedRepository:
    """Shared resolver for function history and selection-code flows.

    Priority:
    1. Valid ``repo_id_hint`` + path exists in that ready repo
    2. Unique ready repo that contains ``repo_relative_path``
    3. Ambiguity / not-found errors
    """
    rel = coerce_repo_relative_path(
        equipment_id=equipment_id,
        repo_relative_path=repo_relative_path,
        file_path=file_path,
    )
    repos = _ready_repos(equipment_id)
    rev = (revision or "HEAD").strip() or "HEAD"

    if repo_id_hint is not None:
        hinted = get_repository(int(repo_id_hint))
        if hinted is None or hinted.equipment_id != equipment_id:
            logger.info(
                "repo_id_hint ignored equipment_id=%s hint=%s",
                equipment_id,
                repo_id_hint,
            )
        elif hinted.status != "ready":
            logger.info(
                "repo_id_hint not ready equipment_id=%s hint=%s status=%s",
                equipment_id,
                repo_id_hint,
                hinted.status,
            )
        else:
            resolved = _try_resolve_in_repo(
                hinted, rel, revision=rev, method="repo_id_hint"
            )
            if resolved:
                return resolved
            logger.info(
                "repo_id_hint path miss equipment_id=%s hint=%s path=%s",
                equipment_id,
                repo_id_hint,
                rel,
            )

    matches: list[ResolvedRepository] = []
    for repo in repos:
        hit = _try_resolve_in_repo(repo, rel, revision=rev, method="path_unique")
        if hit:
            matches.append(hit)

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(f"{m.repository_name}(#{m.repository_id})" for m in matches)
        raise RepositoryResolveError(
            "동일한 파일 경로가 여러 장비 Repository에서 확인되어 "
            f"하나를 결정할 수 없습니다 ({names}).",
            code=CODE_AMBIGUOUS,
        )
    raise RepositoryResolveError(
        "선택한 파일이 장비 Git Repository 내부에서 확인되지 않았습니다.",
        code=CODE_NOT_FOUND,
    )
