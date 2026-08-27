"""Incremental schema migrations (preserves existing DB data)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.core.logging import get_logger

logger = get_logger()

GIT_REPOSITORY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS git_repository (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    repository_url TEXT,
    local_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    UNIQUE (equipment_id, name)
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def _migrate_git_repositories(conn: sqlite3.Connection) -> None:
    conn.execute(GIT_REPOSITORY_TABLE_SQL)

    rows = conn.execute(
        """
        SELECT id, name, git_path FROM equipment
        WHERE git_path IS NOT NULL AND TRIM(git_path) != ''
        """
    ).fetchall()

    now = _now_iso()
    for row in rows:
        existing = conn.execute(
            "SELECT id FROM git_repository WHERE equipment_id = ? LIMIT 1",
            (row["id"],),
        ).fetchone()
        if existing:
            continue
        repo_name = row["name"] or f"repo_{row['id']}"
        conn.execute(
            """
            INSERT INTO git_repository
                (equipment_id, name, source_type, repository_url, local_path, status, created_at, updated_at)
            VALUES (?, ?, 'local', NULL, ?, 'ready', ?, ?)
            """,
            (row["id"], repo_name, row["git_path"], now, now),
        )
        logger.info(
            "Migrated equipment git_path to git_repository equipment_id=%s name=%s",
            row["id"],
            repo_name,
        )


def _default_repository_id(conn: sqlite3.Connection, equipment_id: int) -> int | None:
    row = conn.execute(
        """
        SELECT id FROM git_repository
        WHERE equipment_id = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (equipment_id,),
    ).fetchone()
    return row["id"] if row else None


def _migrate_git_commit_repository_id(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "git_commit"):
        return

    if _column_exists(conn, "git_commit", "repository_id"):
        # Already on new schema
        if not _column_exists(conn, "git_commit", "equipment_id"):
            return
        # Has both columns - equipment_id is deprecated legacy
        return

    logger.info("Migrating git_commit to repository_id schema")

    _migrate_git_repositories(conn)

    conn.execute(
        """
        CREATE TABLE git_commit_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repository_id INTEGER NOT NULL,
            commit_hash TEXT NOT NULL,
            commit_date TEXT NOT NULL,
            author TEXT NOT NULL,
            message TEXT NOT NULL,
            parent_hash TEXT,
            FOREIGN KEY (repository_id) REFERENCES git_repository(id) ON DELETE CASCADE,
            UNIQUE (repository_id, commit_hash)
        )
        """
    )

    old_commits = conn.execute("SELECT * FROM git_commit").fetchall()
    for commit in old_commits:
        repo_id = _default_repository_id(conn, commit["equipment_id"])
        if repo_id is None:
            logger.warning(
                "Skip git_commit migration - no repository equipment_id=%s hash=%s",
                commit["equipment_id"],
                commit["commit_hash"],
            )
            continue
        conn.execute(
            """
            INSERT OR IGNORE INTO git_commit_new
                (id, repository_id, commit_hash, commit_date, author, message, parent_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                commit["id"],
                repo_id,
                commit["commit_hash"],
                commit["commit_date"],
                commit["author"],
                commit["message"],
                commit["parent_hash"],
            ),
        )

    conn.execute("DROP TABLE git_commit")
    conn.execute("ALTER TABLE git_commit_new RENAME TO git_commit")
    logger.info("git_commit migration completed rows=%s", len(old_commits))


def run_schema_migrations(conn: sqlite3.Connection) -> None:
    _migrate_git_repositories(conn)
    _migrate_git_commit_repository_id(conn)
    _migrate_yona_url_columns(conn)


def _migrate_yona_url_columns(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "git_repository"):
        return

    if not _column_exists(conn, "git_repository", "canonical_repository_url"):
        conn.execute(
            "ALTER TABLE git_repository ADD COLUMN canonical_repository_url TEXT"
        )
    if not _column_exists(conn, "git_repository", "yona_username"):
        conn.execute("ALTER TABLE git_repository ADD COLUMN yona_username TEXT")

    from app.services.git_url_utils import parse_repository_url

    rows = conn.execute(
        """
        SELECT id, repository_url, source_type, canonical_repository_url
        FROM git_repository
        WHERE source_type = 'remote' AND repository_url IS NOT NULL
        """
    ).fetchall()

    for row in rows:
        if row["canonical_repository_url"]:
            continue
        try:
            parsed = parse_repository_url(row["repository_url"])
        except ValueError:
            logger.warning(
                "Skip Yona URL migration repository_id=%s invalid_url",
                row["id"],
            )
            continue
        conn.execute(
            """
            UPDATE git_repository
            SET canonical_repository_url = ?,
                yona_username = ?,
                repository_url = ?
            WHERE id = ?
            """,
            (
                parsed.canonical_url,
                None,
                parsed.canonical_url,
                row["id"],
            ),
        )

    _normalize_repository_urls_to_canonical(conn)


def _normalize_repository_urls_to_canonical(conn: sqlite3.Connection) -> None:
    """Ensure repository_url stores canonical URL only; clear legacy yona_username."""
    if not _table_exists(conn, "git_repository"):
        return

    from app.services.git_url_utils import parse_repository_url

    rows = conn.execute(
        """
        SELECT id, repository_url, source_type, canonical_repository_url, yona_username
        FROM git_repository
        WHERE source_type = 'remote' AND repository_url IS NOT NULL
        """
    ).fetchall()

    for row in rows:
        canonical = row["canonical_repository_url"]
        if not canonical:
            try:
                canonical = parse_repository_url(row["repository_url"]).canonical_url
            except ValueError:
                continue
        if (
            row["repository_url"] == canonical
            and row["canonical_repository_url"] == canonical
            and row["yona_username"] is None
        ):
            continue
        conn.execute(
            """
            UPDATE git_repository
            SET canonical_repository_url = ?,
                yona_username = NULL,
                repository_url = ?
            WHERE id = ?
            """,
            (canonical, canonical, row["id"]),
        )
