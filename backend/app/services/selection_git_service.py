"""PROJECT_SPEC v2.4 §6 — 선택 코드(라인·블록) Git 근거 수집.

이 모듈은 선택된 라인/코드 블록의 실제 Git 변경 근거(``git blame`` + Diff +
``git log -L``)만을 다룬다. 함수 전체 이력 조회(§4 함수 변경 이력 조회)와는
완전히 분리된 흐름이며, 키워드 기반 Git/PPT candidate search 점수는 여기서
대표 Commit을 결정하는 데 절대 사용하지 않는다 (§6.4).
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.services.git_repository_service import list_repositories
from app.services.git_service import fetch_commit_file_diff, get_commit_metadata
from app.services.git_url_utils import git_subprocess_env

logger = get_logger()

GIT_ENCODING = "utf-8"
_BLAME_TIMEOUT = 30
_LOG_L_TIMEOUT = 45
_SHOW_TIMEOUT = 30
UNCOMMITTED_HASH = "0" * 40

MAX_SELECTION_LINES = 400


class SelectionGitError(Exception):
    """User-facing selection Git failure (validation or Git command failure)."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class RepoResolution:
    repository_id: int
    repository_name: str
    repo_path: str
    rel_path: str


@dataclass
class BlameLine:
    commit_hash: str
    orig_line: int
    final_line: int
    content: str
    author: str | None = None
    author_time: str | None = None
    summary: str | None = None
    boundary: bool = False

    @property
    def is_uncommitted(self) -> bool:
        return self.commit_hash == UNCOMMITTED_HASH


@dataclass
class BlameGroup:
    commit_hash: str
    start_line: int
    end_line: int
    author: str | None
    author_time: str | None
    summary: str | None
    boundary: bool
    is_uncommitted: bool
    sample_lines: list[str] = field(default_factory=list)


@dataclass
class LineHistoryEntry:
    commit_hash: str
    date: str | None
    subject: str | None


def _run(args: list[str], repo_path: str, timeout: int) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", repo_path, *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=GIT_ENCODING,
            errors="replace",
            timeout=timeout,
            env=git_subprocess_env(),
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("Selection git command timeout command=%s", " ".join(command))
        raise SelectionGitError("Git 명령 실행이 시간 초과되었습니다.") from exc
    except Exception as exc:
        logger.error(
            "Selection git command error command=%s error=%s", " ".join(command), exc
        )
        raise SelectionGitError("Git 명령 실행 중 오류가 발생했습니다.") from exc
    return result


def _posix(path: str) -> str:
    return (path or "").replace("\\", "/").strip()


def _normalize_rel_path(rel_path: str) -> str:
    from app.services.repository_resolver import normalize_repo_relative_path
    from app.services.repository_resolver import RepositoryResolveError as RRE

    try:
        return normalize_repo_relative_path(rel_path)
    except RRE as exc:
        raise SelectionGitError(exc.message) from exc


def _safe_join_under_repo(repo_path: str, rel_path: str) -> str:
    from app.services.repository_resolver import safe_join_under_repo
    from app.services.repository_resolver import RepositoryResolveError as RRE

    try:
        return safe_join_under_repo(repo_path, rel_path)
    except RRE as exc:
        raise SelectionGitError(exc.message) from exc


def resolve_repository_by_id(
    equipment_id: int,
    repo_id: int,
    repo_relative_path: str,
    *,
    revision: str = "HEAD",
) -> RepoResolution:
    """Resolve via shared resolver with an explicit repo_id hint."""
    from app.services.repository_resolver import (
        RepositoryResolveError,
        resolve_equipment_repository,
    )

    try:
        resolved = resolve_equipment_repository(
            equipment_id=equipment_id,
            repo_relative_path=repo_relative_path,
            repo_id_hint=repo_id,
            revision=revision,
        )
    except RepositoryResolveError as exc:
        raise SelectionGitError(exc.message) from exc
    return RepoResolution(
        repository_id=resolved.repository_id,
        repository_name=resolved.repository_name,
        repo_path=resolved.repo_path,
        rel_path=resolved.rel_path,
    )


def resolve_repository_for_file(
    equipment_id: int, file_path: str, *, revision: str = "HEAD"
) -> RepoResolution:
    """Deprecated fallback: absolute/relative path heuristics via shared resolver."""
    from app.services.repository_resolver import (
        RepositoryResolveError,
        resolve_equipment_repository,
    )

    try:
        resolved = resolve_equipment_repository(
            equipment_id=equipment_id,
            file_path=file_path,
            revision=revision,
        )
    except RepositoryResolveError as exc:
        raise SelectionGitError(exc.message) from exc
    return RepoResolution(
        repository_id=resolved.repository_id,
        repository_name=resolved.repository_name,
        repo_path=resolved.repo_path,
        rel_path=resolved.rel_path,
    )


def resolve_selection_repository(
    *,
    equipment_id: int,
    repo_id: int | None,
    repo_relative_path: str | None,
    file_path: str | None,
    revision: str = "HEAD",
    repo_id_hint: int | None = None,
) -> tuple[RepoResolution, str]:
    """Resolve selection target via shared ``resolve_equipment_repository``.

    Returns (resolution, method). ``repo_id`` is treated as ``repo_id_hint``.
    """
    from app.services.repository_resolver import (
        RepositoryResolveError,
        resolve_equipment_repository,
    )

    hint = repo_id_hint if repo_id_hint is not None else repo_id
    if not (repo_relative_path and str(repo_relative_path).strip()) and not (
        file_path and str(file_path).strip()
    ):
        raise SelectionGitError(
            "repo_relative_path가 필요합니다. "
            "구버전 Extension이면 서버/Extension을 업데이트하세요."
        )
    try:
        resolved = resolve_equipment_repository(
            equipment_id=equipment_id,
            repo_relative_path=repo_relative_path,
            repo_id_hint=hint,
            file_path=file_path,
            revision=revision,
        )
    except RepositoryResolveError as exc:
        raise SelectionGitError(exc.message) from exc
    return (
        RepoResolution(
            repository_id=resolved.repository_id,
            repository_name=resolved.repository_name,
            repo_path=resolved.repo_path,
            rel_path=resolved.rel_path,
        ),
        resolved.method,
    )


def _file_exists_at_revision(repo_path: str, rel_path: str, revision: str) -> bool:
    try:
        result = _run(
            ["cat-file", "-e", f"{revision}:{rel_path}"], repo_path, timeout=15
        )
    except SelectionGitError:
        return False
    return result.returncode == 0


def validate_revision(repo_path: str, revision: str) -> bool:
    if not revision:
        return False
    try:
        result = _run(["rev-parse", "--verify", f"{revision}^{{commit}}"], repo_path, timeout=15)
    except SelectionGitError:
        return False
    return result.returncode == 0


def git_show_file_at_revision(
    repo_path: str, rel_path: str, revision: str = "HEAD"
) -> str:
    """Return blob text for ``revision:rel_path`` (not the working tree)."""
    rel = _normalize_rel_path(rel_path)
    rev = (revision or "HEAD").strip() or "HEAD"
    result = _run(["show", f"{rev}:{rel}"], repo_path, _SHOW_TIMEOUT)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:300]
        logger.info(
            "git show file failed rel_path=%s revision=%s stderr=%s",
            rel,
            rev,
            stderr,
        )
        raise SelectionGitError(
            "서버 Git revision에서 해당 파일 내용을 확인하지 못했습니다."
        )
    return result.stdout if result.stdout is not None else ""


def extract_revision_line_block(
    file_text: str, start_line: int, end_line: int
) -> str | None:
    """Extract 1-based inclusive lines from a revision file blob."""
    if start_line < 1 or end_line < start_line:
        return None
    normalized = (file_text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.splitlines()
    if end_line > len(lines):
        return None
    return "\n".join(lines[start_line - 1 : end_line])


def normalize_selection_compare_text(text: str) -> str:
    """Light normalization for IDE vs server selection compare.

    Allows CRLF/LF, block leading/trailing blank lines, and per-line trailing
    whitespace only — does not collapse internal whitespace or retokenize.
    """
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in normalized.split("\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def selected_code_matches_server_block(
    selected_code: str | None, server_block: str | None
) -> bool:
    """True when normalized selected_code equals or is contained in the server block."""
    sel = normalize_selection_compare_text(selected_code or "")
    srv = normalize_selection_compare_text(server_block or "")
    if not sel or not srv:
        return False
    return sel == srv or sel in srv


def verify_selection_against_revision(
    repo_path: str,
    rel_path: str,
    *,
    start_line: int,
    end_line: int,
    selected_code: str | None,
    revision: str = "HEAD",
) -> tuple[bool, str | None]:
    """Compare IDE selected_code to ``git show revision:path`` line range.

    Returns ``(matched, server_block_or_none)``.
    """
    file_text = git_show_file_at_revision(repo_path, rel_path, revision)
    block = extract_revision_line_block(file_text, start_line, end_line)
    if block is None:
        return False, None
    return selected_code_matches_server_block(selected_code, block), block


_BLAME_HEADER_RE = re.compile(r"^([0-9a-f]{40}) (\d+) (\d+)(?: (\d+))?$")


def git_blame_lines(
    repo_path: str,
    rel_path: str,
    start_line: int,
    end_line: int,
    *,
    revision: str = "HEAD",
) -> list[BlameLine]:
    args = ["blame", "--line-porcelain", "-L", f"{start_line},{end_line}"]
    # "HEAD" is treated as "current worktree" so uncommitted local edits are
    # reported with the all-zero commit hash (git blame's own convention) —
    # passing "HEAD" explicitly as a revision would blame the committed blob
    # only and hide uncommitted lines (§6.1 uncommitted 여부 수집 요구).
    if revision and revision.upper() != "HEAD":
        args.append(revision)
    args += ["--", rel_path]
    result = _run(args, repo_path, _BLAME_TIMEOUT)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:300]
        logger.info("git blame failed rel_path=%s stderr=%s", rel_path, stderr)
        raise SelectionGitError(
            "선택 범위에 대한 git blame 조회에 실패했습니다. "
            "코드 이동, 대규모 리팩터링 또는 잘못된 행 번호일 수 있습니다."
        )
    return _parse_blame_porcelain(result.stdout)


def _parse_blame_porcelain(output: str) -> list[BlameLine]:
    lines = output.split("\n")
    n = len(lines)
    i = 0
    results: list[BlameLine] = []
    while i < n:
        header = _BLAME_HEADER_RE.match(lines[i])
        if not header:
            i += 1
            continue
        commit_hash = header.group(1)
        orig_line = int(header.group(2))
        final_line = int(header.group(3))
        i += 1
        meta: dict[str, str] = {}
        boundary = False
        content = ""
        while i < n:
            line = lines[i]
            if line.startswith("\t"):
                content = line[1:]
                i += 1
                break
            if line == "boundary":
                boundary = True
                i += 1
                continue
            if not line:
                i += 1
                continue
            key, _, val = line.partition(" ")
            meta[key] = val
            i += 1
        results.append(
            BlameLine(
                commit_hash=commit_hash,
                orig_line=orig_line,
                final_line=final_line,
                content=content,
                author=meta.get("author"),
                author_time=meta.get("author-time"),
                summary=meta.get("summary"),
                boundary=boundary,
            )
        )
    return results


def group_blame_lines(lines: list[BlameLine]) -> list[BlameGroup]:
    """Merge contiguous final-line ranges that share the same commit."""
    groups: list[BlameGroup] = []
    for bl in sorted(lines, key=lambda x: x.final_line):
        if (
            groups
            and groups[-1].commit_hash == bl.commit_hash
            and groups[-1].end_line == bl.final_line - 1
        ):
            groups[-1].end_line = bl.final_line
            groups[-1].sample_lines.append(bl.content)
        else:
            groups.append(
                BlameGroup(
                    commit_hash=bl.commit_hash,
                    start_line=bl.final_line,
                    end_line=bl.final_line,
                    author=bl.author,
                    author_time=bl.author_time,
                    summary=bl.summary,
                    boundary=bl.boundary,
                    is_uncommitted=bl.is_uncommitted,
                    sample_lines=[bl.content],
                )
            )
    return groups


_COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*|#)")


def _is_comment_line(text: str) -> bool:
    return bool(_COMMENT_LINE_RE.match(text or ""))


def classify_blame_commit_change(
    diff_text: str | None, sample_lines: list[str]
) -> str:
    """Classify how the blamed commit's Diff relates to the selected sample lines.

    Returns one of: ``added`` | ``modified`` | ``moved`` | ``comment_only`` |
    ``context_only`` | ``unknown`` (PROJECT_SPEC v2.4 §6.2).

    Only return ``added`` / ``modified`` when Diff lines confirm it — never
    invent ``modified`` from blame alone.
    """
    norm_samples = [s.strip() for s in (sample_lines or []) if s.strip()]
    if not norm_samples:
        return "unknown"
    if not diff_text:
        return "unknown"

    added: list[str] = []
    removed: list[str] = []
    for raw in diff_text.splitlines():
        if raw.startswith("+++") or raw.startswith("---"):
            continue
        if raw.startswith("+"):
            added.append(raw[1:].strip())
        elif raw.startswith("-"):
            removed.append(raw[1:].strip())

    if all(_is_comment_line(s) for s in norm_samples):
        if any(s in added for s in norm_samples):
            return "comment_only"

    hit_added = any(s in added for s in norm_samples)
    hit_removed_same = any(s in removed for s in norm_samples)

    if hit_added and hit_removed_same:
        return "moved"
    if hit_added and removed:
        return "modified"
    if hit_added:
        return "added"
    return "context_only"


_HUNK_RANGE_RE = re.compile(
    r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@"
)


@dataclass
class DiffHunk:
    """One unified-diff hunk overlapping a selection line range."""

    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    raw_lines: list[str] = field(default_factory=list)

    @property
    def old_end(self) -> int:
        return self.old_start + max(self.old_count, 1) - 1 if self.old_count else self.old_start

    @property
    def new_end(self) -> int:
        return self.new_start + max(self.new_count, 1) - 1 if self.new_count else self.new_start

    def overlaps_new_range(self, start: int, end: int) -> bool:
        return not (self.new_end < start or self.new_start > end)

    def before_lines(self) -> list[str]:
        out: list[str] = []
        for line in self.raw_lines:
            if line.startswith("---") or line.startswith("+++"):
                continue
            if line.startswith("-"):
                out.append(line[1:])
            elif line.startswith("\\"):
                continue
            elif not line.startswith("+"):
                # context (leading space or empty)
                out.append(line[1:] if line.startswith(" ") else line)
        return out

    def after_lines(self) -> list[str]:
        out: list[str] = []
        for line in self.raw_lines:
            if line.startswith("---") or line.startswith("+++"):
                continue
            if line.startswith("+"):
                out.append(line[1:])
            elif line.startswith("\\"):
                continue
            elif not line.startswith("-"):
                out.append(line[1:] if line.startswith(" ") else line)
        return out

    def unified_text(self) -> str:
        body = "\n".join(self.raw_lines)
        return f"{self.header}\n{body}".rstrip() + "\n"


def parse_diff_hunks(diff_text: str | None) -> list[DiffHunk]:
    """Parse unified Diff into hunks (file headers ignored)."""
    if not diff_text:
        return []
    hunks: list[DiffHunk] = []
    current: DiffHunk | None = None
    for raw in diff_text.splitlines():
        if raw.startswith("diff ") or raw.startswith("index "):
            current = None
            continue
        if raw.startswith("---") or raw.startswith("+++"):
            continue
        m = _HUNK_RANGE_RE.match(raw)
        if m:
            old_start = int(m.group(1))
            old_count = int(m.group(2) or "1")
            new_start = int(m.group(3))
            new_count = int(m.group(4) or "1")
            current = DiffHunk(
                header=raw,
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )
            hunks.append(current)
            continue
        if current is not None:
            current.raw_lines.append(raw)
    return hunks


def extract_overlapping_hunks(
    diff_text: str | None,
    *,
    start_line: int,
    end_line: int,
) -> list[DiffHunk]:
    """Return hunks whose new-side line range overlaps the selection."""
    if start_line < 1 or end_line < start_line:
        return []
    return [
        h
        for h in parse_diff_hunks(diff_text)
        if h.overlaps_new_range(start_line, end_line)
    ]


def classify_change_kind_from_hunks(
    hunks: list[DiffHunk],
    sample_lines: list[str] | None = None,
) -> str:
    """Prefer hunk structure for added/modified; fall back to sample match."""
    if not hunks:
        return "unknown"
    has_plus = any(
        ln.startswith("+") and not ln.startswith("+++")
        for h in hunks
        for ln in h.raw_lines
    )
    has_minus = any(
        ln.startswith("-") and not ln.startswith("---")
        for h in hunks
        for ln in h.raw_lines
    )
    if has_plus and has_minus:
        return "modified"
    if has_plus and not has_minus:
        return "added"
    if has_minus and not has_plus:
        return "deleted"
    # Context-only hunk overlap — try sample text match on full unified text.
    unified = "\n".join(h.unified_text() for h in hunks)
    return classify_blame_commit_change(unified, sample_lines or [])


def git_show_commit_diff(repo_path: str, commit_hash: str, rel_path: str) -> str | None:
    return fetch_commit_file_diff(repo_path, commit_hash, rel_path)


def blame_commit_metadata(repo_path: str, commit_hash: str) -> dict:
    return get_commit_metadata(repo_path, commit_hash)


_LOG_L_COMMIT_RE = re.compile(r"^([0-9a-f]{7,40})$")


def git_log_line_history(
    repo_path: str,
    rel_path: str,
    start_line: int,
    end_line: int,
    *,
    revision: str = "HEAD",
    max_commits: int = 15,
) -> list[LineHistoryEntry] | None:
    """Return past changes to the given line range, or ``None`` on failure.

    ``None`` signals the caller to show the conservative "line history 확인
    제한" message (§6.3) instead of guessing.
    """
    args = [
        "log",
        "--no-color",
        "--date=iso-strict",
        f"-L{start_line},{end_line}:{rel_path}",
        revision,
    ]
    try:
        result = _run(args, repo_path, _LOG_L_TIMEOUT)
    except SelectionGitError:
        return None
    if result.returncode != 0:
        logger.info(
            "git log -L failed rel_path=%s stderr=%s",
            rel_path,
            (result.stderr or "").strip()[:300],
        )
        return None
    entries = _parse_log_l_output(result.stdout, max_commits=max_commits)
    return entries


def _parse_log_l_output(output: str, *, max_commits: int) -> list[LineHistoryEntry]:
    entries: list[LineHistoryEntry] = []
    blocks = re.split(r"(?m)^commit ", output)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        lines = block.splitlines()
        if not lines:
            continue
        commit_hash = lines[0].split()[0] if lines[0].split() else None
        if not commit_hash or not _LOG_L_COMMIT_RE.match(commit_hash):
            continue
        date = None
        subject = None
        seen_date = False
        for line in lines[1:]:
            if line.startswith("Author:") or line.startswith("Merge:"):
                continue
            if line.startswith("Date:"):
                date = line.split("Date:", 1)[1].strip()[:10]
                seen_date = True
                continue
            if line.startswith("diff") or line.startswith("@@"):
                break
            stripped = line.strip()
            if seen_date and stripped and subject is None:
                subject = stripped
                break
        entries.append(LineHistoryEntry(commit_hash=commit_hash, date=date, subject=subject))
        if len(entries) >= max_commits:
            break
    return entries
