"""Git Commit 목록 검색 및 상세 조회."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.database import get_connection
from app.schemas.git_history import (
    CommitChangeDetail,
    CommitDetailResponse,
    CommitListItem,
    CommitListResponse,
    CommitSearchParams,
    calc_total_pages,
    normalize_page,
    normalize_page_size,
)

logger = get_logger()


def _build_where_clause(params: CommitSearchParams) -> tuple[str, list]:
    conditions = ["gr.equipment_id = ?"]
    values: list = [params.equipment_id]

    if params.repository_id is not None:
        conditions.append("gc.repository_id = ?")
        values.append(params.repository_id)

    if params.q:
        like = f"%{params.q}%"
        conditions.append(
            """(
                gc.message LIKE ?
                OR gc.commit_hash LIKE ?
                OR gc.author LIKE ?
                OR EXISTS (
                    SELECT 1 FROM git_change gch_q
                    WHERE gch_q.commit_id = gc.id
                    AND (gch_q.file_path LIKE ? OR gch_q.diff LIKE ?)
                )
            )"""
        )
        values.extend([like, like, like, like, like])

    if params.date_from:
        conditions.append("gc.commit_date >= ?")
        values.append(params.date_from)

    if params.date_to:
        conditions.append("gc.commit_date <= ?")
        values.append(params.date_to)

    if params.author:
        conditions.append("gc.author LIKE ?")
        values.append(f"%{params.author}%")

    if params.file_path:
        conditions.append(
            """EXISTS (
                SELECT 1 FROM git_change gch_fp
                WHERE gch_fp.commit_id = gc.id
                AND gch_fp.file_path LIKE ?
            )"""
        )
        values.append(f"%{params.file_path}%")

    return " AND ".join(conditions), values


def _has_search_filters(params: CommitSearchParams) -> bool:
    return any(
        [
            params.q,
            params.date_from,
            params.date_to,
            params.file_path,
            params.author,
            params.repository_id is not None,
        ]
    )


def search_commits(params: CommitSearchParams) -> CommitListResponse:
    page = normalize_page(params.page)
    page_size = normalize_page_size(params.page_size)
    offset = (page - 1) * page_size

    where_sql, where_values = _build_where_clause(params)

    conn = get_connection()
    try:
        count_sql = f"""
            SELECT COUNT(*) AS cnt FROM (
                SELECT gc.id
                FROM git_commit gc
                JOIN git_repository gr ON gr.id = gc.repository_id
                WHERE {where_sql}
                GROUP BY gc.id
            )
        """
        total = conn.execute(count_sql, where_values).fetchone()["cnt"]

        list_sql = f"""
            SELECT
                gc.id,
                gc.commit_hash,
                gc.commit_date,
                gc.author,
                gc.message,
                gc.repository_id,
                gr.name AS repository_name,
                COUNT(gch.id) AS changed_file_count,
                COALESCE(SUM(gch.additions), 0) AS additions,
                COALESCE(SUM(gch.deletions), 0) AS deletions
            FROM git_commit gc
            JOIN git_repository gr ON gr.id = gc.repository_id
            LEFT JOIN git_change gch ON gch.commit_id = gc.id
            WHERE {where_sql}
            GROUP BY gc.id
            ORDER BY gc.commit_date DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(
            list_sql, [*where_values, page_size, offset]
        ).fetchall()
    finally:
        conn.close()

    items = [
        CommitListItem(
            id=row["id"],
            commit_hash=row["commit_hash"],
            commit_date=row["commit_date"],
            author=row["author"],
            message=row["message"],
            repository_id=row["repository_id"],
            repository_name=row["repository_name"],
            changed_file_count=row["changed_file_count"],
            additions=row["additions"],
            deletions=row["deletions"],
        )
        for row in rows
    ]

    logger.info(
        "Git history search equipment_id=%s repository_id=%s has_filters=%s result_count=%s",
        params.equipment_id,
        params.repository_id,
        _has_search_filters(params),
        total,
    )

    return CommitListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=calc_total_pages(total, page_size),
    )


def get_commit_detail(commit_id: int) -> CommitDetailResponse | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT gc.*, gr.equipment_id, gr.name AS repository_name
            FROM git_commit gc
            JOIN git_repository gr ON gr.id = gc.repository_id
            WHERE gc.id = ?
            """,
            (commit_id,),
        ).fetchone()
        if row is None:
            return None

        changes = conn.execute(
            """
            SELECT id, file_path, change_type, additions, deletions, diff
            FROM git_change
            WHERE commit_id = ?
            ORDER BY file_path
            """,
            (commit_id,),
        ).fetchall()
    finally:
        conn.close()

    logger.info("Commit detail read commit_id=%s", commit_id)

    return CommitDetailResponse(
        id=row["id"],
        equipment_id=row["equipment_id"],
        repository_id=row["repository_id"],
        repository_name=row["repository_name"],
        commit_hash=row["commit_hash"],
        commit_date=row["commit_date"],
        author=row["author"],
        message=row["message"],
        parent_hash=row["parent_hash"],
        changes=[
            CommitChangeDetail(
                id=c["id"],
                file_path=c["file_path"],
                change_type=c["change_type"],
                additions=c["additions"],
                deletions=c["deletions"],
                diff=c["diff"],
            )
            for c in changes
        ],
    )
