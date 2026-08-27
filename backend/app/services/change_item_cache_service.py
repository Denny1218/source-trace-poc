"""Structured change-item cache (STEP 6)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pptx import Presentation

from app.core.logging import get_logger
from app.db.database import get_connection
from app.services.change_item_parser_service import (
    PARSER_VERSION,
    ChangeItem,
    parse_change_items_from_presentation,
)
from app.services.ppt_cache_service import (
    DocumentCacheRow,
    get_document_cache_by_id,
    get_slides_for_document,
)

logger = get_logger()


@dataclass
class ChangeItemCacheRow:
    id: int
    document_cache_id: int
    slide_no: int
    item_no: str | None
    change_title: str | None
    csr_no: str | None
    business_background: str | None
    current_status: str | None
    as_is: str | None
    to_be: str | None
    source_functions_json: str
    test_cases_json: str
    applicable_scopes_json: str
    raw_text: str
    parser_version: int
    created_at: str
    file_path: str | None = None
    file_name: str | None = None
    equipment_id: int | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_change_item(row: sqlite3.Row) -> ChangeItemCacheRow:
    return ChangeItemCacheRow(
        id=row["id"],
        document_cache_id=row["document_cache_id"],
        slide_no=row["slide_no"],
        item_no=row["item_no"],
        change_title=row["change_title"],
        csr_no=row["csr_no"],
        business_background=row["business_background"],
        current_status=row["current_status"],
        as_is=row["as_is"],
        to_be=row["to_be"],
        source_functions_json=row["source_functions_json"],
        test_cases_json=row["test_cases_json"],
        applicable_scopes_json=row["applicable_scopes_json"],
        raw_text=row["raw_text"],
        parser_version=row["parser_version"],
        created_at=row["created_at"],
        file_path=row["file_path"] if "file_path" in row.keys() else None,
        file_name=row["file_name"] if "file_name" in row.keys() else None,
        equipment_id=(
            int(row["equipment_id"])
            if "equipment_id" in row.keys() and row["equipment_id"] is not None
            else None
        ),
    )


def delete_change_items_for_document(document_cache_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM change_item_cache WHERE document_cache_id = ?",
            (document_cache_id,),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_change_items(
    conn: sqlite3.Connection,
    document_cache_id: int,
    items: list[ChangeItem],
) -> None:
    now = _now_iso()
    for item in items:
        conn.execute(
            """
            INSERT INTO change_item_cache
                (document_cache_id, slide_no, item_no, change_title, csr_no,
                 business_background, current_status, as_is, to_be,
                 source_functions_json, test_cases_json, applicable_scopes_json,
                 raw_text, parser_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_cache_id,
                item.slide_no,
                item.item_no,
                item.change_title,
                item.csr_no,
                item.business_background,
                item.current_status,
                item.as_is,
                item.to_be,
                json.dumps([sf.to_dict() for sf in item.source_functions], ensure_ascii=False),
                json.dumps(item.test_cases, ensure_ascii=False),
                json.dumps(item.applicable_scopes, ensure_ascii=False),
                item.raw_text,
                PARSER_VERSION,
                now,
            ),
        )


def store_change_items(document_cache_id: int, items: list[ChangeItem]) -> int:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        conn.execute(
            "DELETE FROM change_item_cache WHERE document_cache_id = ?",
            (document_cache_id,),
        )
        if items:
            _insert_change_items(conn, document_cache_id, items)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    logger.info(
        "Change item cache stored document_cache_id=%s count=%s parser_version=%s",
        document_cache_id,
        len(items),
        PARSER_VERSION,
    )
    return len(items)


def _needs_structure_parse(document_cache_id: int) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt,
                   COALESCE(MAX(parser_version), 0) AS max_version
            FROM change_item_cache
            WHERE document_cache_id = ?
            """,
            (document_cache_id,),
        ).fetchone()
        if row["cnt"] == 0:
            return True
        return int(row["max_version"]) < PARSER_VERSION
    finally:
        conn.close()


def parse_and_store_change_items(
    document: DocumentCacheRow,
    *,
    file_path: str | None = None,
) -> list[ChangeItem]:
    path = file_path or document.file_path
    if not path or not Path(path).is_file():
        logger.warning(
            "Change item parse skipped missing file document_cache_id=%s",
            document.id,
        )
        return []

    try:
        presentation = Presentation(path)
        items = parse_change_items_from_presentation(presentation)
    except Exception as exc:
        # Graceful degradation — matches ppt_parser_service.parse_pptx_file's
        # policy: a single PPT parse failure must not crash the whole
        # request. Existing cached change items (if any) are left untouched
        # rather than wiped on a transient read failure.
        logger.warning(
            "Change item parse failed document_cache_id=%s exception_type=%s",
            document.id,
            type(exc).__name__,
        )
        return []

    store_change_items(document.id, items)
    return items


def ensure_change_items_for_document(
    document_cache_id: int,
    *,
    file_path: str | None = None,
) -> list[ChangeItemCacheRow]:
    if not _needs_structure_parse(document_cache_id):
        return list_change_items_for_document(document_cache_id)

    document = get_document_cache_by_id(document_cache_id)
    if document is None:
        return []

    slides = get_slides_for_document(document_cache_id)
    if not slides:
        return []

    resolved_path = file_path or document.file_path
    if resolved_path and Path(resolved_path).is_file():
        parse_and_store_change_items(document, file_path=resolved_path)
        return list_change_items_for_document(document_cache_id)

    logger.info(
        "Change item lazy parse skipped no file access document_cache_id=%s",
        document_cache_id,
    )
    return list_change_items_for_document(document_cache_id)


def list_change_items_for_document(document_cache_id: int) -> list[ChangeItemCacheRow]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT cic.*, dc.file_path, dc.file_name, dc.equipment_id
            FROM change_item_cache cic
            INNER JOIN document_cache dc ON dc.id = cic.document_cache_id
            WHERE cic.document_cache_id = ?
            ORDER BY cic.slide_no
            """,
            (document_cache_id,),
        ).fetchall()
        return [_row_to_change_item(row) for row in rows]
    finally:
        conn.close()


def list_change_items_for_equipment(equipment_id: int) -> list[ChangeItemCacheRow]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT cic.*, dc.file_path, dc.file_name, dc.equipment_id
            FROM change_item_cache cic
            INNER JOIN document_cache dc ON dc.id = cic.document_cache_id
            WHERE dc.equipment_id = ?
            ORDER BY dc.file_name COLLATE NOCASE, cic.slide_no
            """,
            (equipment_id,),
        ).fetchall()
        return [_row_to_change_item(row) for row in rows]
    finally:
        conn.close()


def get_change_item_by_id(change_item_id: int) -> ChangeItemCacheRow | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT cic.*, dc.file_path, dc.file_name, dc.equipment_id
            FROM change_item_cache cic
            INNER JOIN document_cache dc ON dc.id = cic.document_cache_id
            WHERE cic.id = ?
            """,
            (change_item_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_change_item(row)
    finally:
        conn.close()
