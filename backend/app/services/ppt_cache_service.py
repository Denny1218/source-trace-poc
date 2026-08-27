"""PPT cache: SHA-256, hit/miss, DB persistence."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.core.logging import get_logger
from app.core.ppt_parse_config import FILE_HASH_CHUNK_SIZE
from app.db.database import get_connection
from app.services.ppt_parser_service import ParsedPresentation, ParsedSlide, PptParseError, parse_pptx_file

logger = get_logger()


@dataclass
class DocumentCacheRow:
    id: int
    equipment_id: int
    file_path: str
    file_name: str
    file_hash: str
    modified_at: str
    parsed_at: str
    slide_count: int


@dataclass
class SlideCacheRow:
    id: int
    document_cache_id: int
    slide_number: int
    title: str | None
    content: str


@dataclass
class CachedDocument:
    document: DocumentCacheRow
    slides: list[SlideCacheRow]
    cache_hit: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compute_file_hash(file_path: Path, chunk_size: int = FILE_HASH_CHUNK_SIZE) -> str:
    """SHA-256 hash in lowercase hex, read in chunks (default 64 KB)."""
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _row_to_document(row: sqlite3.Row) -> DocumentCacheRow:
    return DocumentCacheRow(
        id=row["id"],
        equipment_id=row["equipment_id"],
        file_path=row["file_path"],
        file_name=row["file_name"],
        file_hash=row["file_hash"],
        modified_at=row["modified_at"],
        parsed_at=row["parsed_at"],
        slide_count=row["slide_count"],
    )


def _row_to_slide(row: sqlite3.Row) -> SlideCacheRow:
    return SlideCacheRow(
        id=row["id"],
        document_cache_id=row["document_cache_id"],
        slide_number=row["slide_number"],
        title=row["title"],
        content=row["content"],
    )


def get_document_cache(equipment_id: int, file_path: str) -> DocumentCacheRow | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM document_cache
            WHERE equipment_id = ? AND file_path = ?
            """,
            (equipment_id, file_path),
        ).fetchone()
        return _row_to_document(row) if row else None
    finally:
        conn.close()


def get_document_cache_by_id(document_cache_id: int) -> DocumentCacheRow | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM document_cache WHERE id = ?",
            (document_cache_id,),
        ).fetchone()
        return _row_to_document(row) if row else None
    finally:
        conn.close()


def list_document_cache_by_equipment(equipment_id: int) -> list[DocumentCacheRow]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM document_cache
            WHERE equipment_id = ?
            ORDER BY parsed_at DESC
            """,
            (equipment_id,),
        ).fetchall()
        return [_row_to_document(row) for row in rows]
    finally:
        conn.close()


@dataclass
class EquipmentCachedSlide:
    slide: SlideCacheRow
    file_path: str
    file_name: str


def list_cached_slides_for_equipment(equipment_id: int) -> list[EquipmentCachedSlide]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT sc.id, sc.document_cache_id, sc.slide_number, sc.title, sc.content,
                   dc.file_path, dc.file_name
            FROM slide_cache sc
            INNER JOIN document_cache dc ON dc.id = sc.document_cache_id
            WHERE dc.equipment_id = ?
            ORDER BY dc.file_name COLLATE NOCASE, sc.slide_number ASC
            """,
            (equipment_id,),
        ).fetchall()
        result: list[EquipmentCachedSlide] = []
        for row in rows:
            slide = SlideCacheRow(
                id=row["id"],
                document_cache_id=row["document_cache_id"],
                slide_number=row["slide_number"],
                title=row["title"],
                content=row["content"],
            )
            result.append(
                EquipmentCachedSlide(
                    slide=slide,
                    file_path=row["file_path"],
                    file_name=row["file_name"],
                )
            )
        return result
    finally:
        conn.close()


def get_slides_for_document(document_cache_id: int) -> list[SlideCacheRow]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM slide_cache
            WHERE document_cache_id = ?
            ORDER BY slide_number ASC
            """,
            (document_cache_id,),
        ).fetchall()
        return [_row_to_slide(row) for row in rows]
    finally:
        conn.close()


def delete_document_cache(document_cache_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM document_cache WHERE id = ?", (document_cache_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def _insert_new_cache(
    conn: sqlite3.Connection,
    equipment_id: int,
    file_path: str,
    file_name: str,
    file_hash: str,
    modified_at: str,
    parsed: ParsedPresentation,
) -> DocumentCacheRow:
    parsed_at = _now_iso()
    cursor = conn.execute(
        """
        INSERT INTO document_cache
            (equipment_id, file_path, file_name, file_hash, modified_at, parsed_at, slide_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment_id,
            file_path,
            file_name,
            file_hash,
            modified_at,
            parsed_at,
            parsed.slide_count,
        ),
    )
    doc_id = cursor.lastrowid
    for slide in parsed.slides:
        conn.execute(
            """
            INSERT INTO slide_cache (document_cache_id, slide_number, title, content)
            VALUES (?, ?, ?, ?)
            """,
            (doc_id, slide.slide_number, slide.title, slide.content),
        )
    conn.commit()
    row = conn.execute("SELECT * FROM document_cache WHERE id = ?", (doc_id,)).fetchone()
    return _row_to_document(row)


def _replace_cache(
    conn: sqlite3.Connection,
    document_cache_id: int,
    file_hash: str,
    modified_at: str,
    parsed: ParsedPresentation,
) -> DocumentCacheRow:
    parsed_at = _now_iso()
    conn.execute("BEGIN")
    try:
        conn.execute(
            "DELETE FROM slide_cache WHERE document_cache_id = ?",
            (document_cache_id,),
        )
        for slide in parsed.slides:
            conn.execute(
                """
                INSERT INTO slide_cache (document_cache_id, slide_number, title, content)
                VALUES (?, ?, ?, ?)
                """,
                (document_cache_id, slide.slide_number, slide.title, slide.content),
            )
        conn.execute(
            """
            UPDATE document_cache
            SET file_hash = ?, modified_at = ?, parsed_at = ?, slide_count = ?
            WHERE id = ?
            """,
            (file_hash, modified_at, parsed_at, parsed.slide_count, document_cache_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    row = conn.execute(
        "SELECT * FROM document_cache WHERE id = ?",
        (document_cache_id,),
    ).fetchone()
    logger.info("PPT cache updated document_cache_id=%s", document_cache_id)
    return _row_to_document(row)


def _load_cached_document(doc: DocumentCacheRow) -> CachedDocument:
    slides = get_slides_for_document(doc.id)
    return CachedDocument(document=doc, slides=slides, cache_hit=True)


def get_or_parse_document(
    equipment_id: int,
    file_path: str,
    *,
    parse_fn=parse_pptx_file,
) -> tuple[CachedDocument | None, bool, bool]:
    """
    Returns (cached_document, cache_hit, parse_failed).

    cache_hit=True means no new parsing was performed.
    parse_failed=True means parse was attempted and failed (existing cache kept if any).
    """
    path = Path(file_path)
    if not path.is_file():
        return None, False, True

    file_name = path.name
    try:
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat()
        file_hash = compute_file_hash(path)
    except OSError:
        return None, False, True

    existing = get_document_cache(equipment_id, str(path.resolve()))

    if existing is not None and existing.file_hash == file_hash:
        logger.info(
            "PPT cache hit document_cache_id=%s file_name=%s",
            existing.id,
            file_name,
        )
        return _load_cached_document(existing), True, False

    if existing is not None:
        logger.info("PPT cache miss file_name=%s reason=hash_changed", file_name)
    else:
        logger.info("PPT cache miss file_name=%s reason=no_cache", file_name)

    logger.info("PPT parse started file_name=%s", file_name)
    try:
        parsed = parse_fn(str(path))
    except PptParseError as exc:
        logger.warning(
            "PPT parse failed file_path=%s exception_type=%s",
            file_path,
            type(exc).__name__,
        )
        if existing is not None:
            return _load_cached_document(existing), True, True
        return None, False, True
    except Exception as exc:
        logger.warning(
            "PPT parse failed file_path=%s exception_type=%s",
            file_path,
            type(exc).__name__,
        )
        if existing is not None:
            return _load_cached_document(existing), True, True
        return None, False, True

    logger.info(
        "PPT parse completed file_name=%s slide_count=%s",
        file_name,
        parsed.slide_count,
    )

    conn = get_connection()
    try:
        if existing is None:
            doc = _insert_new_cache(
                conn,
                equipment_id,
                str(path.resolve()),
                file_name,
                file_hash,
                modified_at,
                parsed,
            )
        else:
            doc = _replace_cache(conn, existing.id, file_hash, modified_at, parsed)
    finally:
        conn.close()

    return _load_cached_document(doc), False, False
