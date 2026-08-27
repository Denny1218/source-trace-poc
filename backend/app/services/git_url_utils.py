"""Git repository URL parsing, masking, and Git access URL building (Yona)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

YONA_DEFAULT_USERNAME_MISSING_MESSAGE = (
    "Yona 기본 계정이 설정되지 않았습니다. 서버 설정을 확인해 주세요."
)
YONA_AUTH_FAILURE_MESSAGE = (
    "Yona 기본 계정 인증이 설정되지 않았거나 인증에 실패했습니다."
)


@dataclass(frozen=True)
class ParsedRepositoryUrl:
    """Result of parsing a user-supplied Git repository URL."""

    canonical_url: str
    yona_username: str | None
    display_url: str
    had_password: bool


def _build_netloc(hostname: str, port: int | None, username: str | None = None) -> str:
    host = hostname or ""
    port_part = f":{port}" if port else ""
    if username:
        return f"{username}@{host}{port_part}"
    return f"{host}{port_part}"


def parse_repository_url(url: str) -> ParsedRepositoryUrl:
    """Parse URL with urllib; separate canonical repo URL and username context."""
    raw = url.strip()
    parsed = urlparse(raw)

    if not parsed.scheme or not parsed.hostname:
        raise ValueError("유효한 Git Repository URL이 아닙니다.")

    username = parsed.username
    had_password = parsed.password is not None and parsed.password != ""

    canonical_netloc = _build_netloc(parsed.hostname, parsed.port)
    canonical_url = urlunparse(
        (
            parsed.scheme,
            canonical_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )

    display_netloc = _build_netloc(parsed.hostname, parsed.port, username)
    display_url = urlunparse(
        (
            parsed.scheme,
            display_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )

    return ParsedRepositoryUrl(
        canonical_url=canonical_url,
        yona_username=username,
        display_url=display_url,
        had_password=had_password,
    )


def require_yona_default_username() -> str:
    """Return YONA_DEFAULT_USERNAME or raise with a user-facing message."""
    from app.core.config import YONA_DEFAULT_USERNAME

    username = (YONA_DEFAULT_USERNAME or "").strip()
    if not username:
        raise ValueError(YONA_DEFAULT_USERNAME_MISSING_MESSAGE)
    return username


def build_git_access_url(
    canonical_url: str,
    yona_username: str | None = None,
    default_username: str | None = None,
    *,
    server_username: str | None = None,
) -> str:
    """Build URL for git ls-remote/clone/fetch using YONA_DEFAULT_USERNAME only.

    User-supplied URL username (yona_username) is ignored for Git access.
    """
    _ = yona_username, default_username, server_username  # ignored — server default only
    access_user = require_yona_default_username()

    parsed = urlparse(canonical_url)
    if not parsed.hostname:
        return canonical_url

    netloc = _build_netloc(parsed.hostname, parsed.port, access_user)
    return urlunparse(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )


def mask_repository_url(url: str | None) -> str | None:
    """Return canonical repository URL without userinfo for API/UI display."""
    if not url:
        return url
    try:
        return parse_repository_url(url).canonical_url
    except ValueError:
        parsed = urlparse(url)
        if not parsed.hostname:
            return url
        netloc = _build_netloc(parsed.hostname, parsed.port)
        return urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )


def git_access_username_for_log(url: str | None) -> str:
    if not url:
        return "(none)"
    try:
        username = urlparse(url).username
    except Exception:
        return "(unknown)"
    return username or "(none)"


def safe_url_for_log(url: str | None) -> str:
    canonical = mask_repository_url(url)
    return canonical or "(none)"


def git_subprocess_env() -> dict[str, str]:
    """Non-interactive Git environment (no credential prompt hang)."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_git_command(
    args: list[str],
    *,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    """Run a Git subprocess with GIT_TERMINAL_PROMPT=0."""
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=git_subprocess_env(),
    )
