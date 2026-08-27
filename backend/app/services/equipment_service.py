import sqlite3
import time
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.db.database import get_connection
from app.schemas.equipment import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.services.path_validation_service import validate_document_path_basic

logger = get_logger()

DUPLICATE_NAME_MESSAGE = "이미 등록된 장비명입니다."
DEPRECATED_GIT_PATH = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _row_to_response(row: sqlite3.Row) -> EquipmentResponse:
    return EquipmentResponse(
        id=row["id"],
        name=row["name"],
        document_path=row["document_path"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_equipment() -> list[EquipmentResponse]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM equipment ORDER BY name COLLATE NOCASE"
        ).fetchall()
        return [_row_to_response(row) for row in rows]
    finally:
        conn.close()


def get_equipment(equipment_id: int) -> EquipmentResponse | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM equipment WHERE id = ?", (equipment_id,)
        ).fetchone()
        if row is None:
            return None
        return _row_to_response(row)
    finally:
        conn.close()


def _validate_document_path(document_path: str) -> None:
    """Fast UNC validation on save (no recursive PPTX scan)."""
    started = time.perf_counter()
    doc_ok, doc_msg = validate_document_path_basic(document_path)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("Equipment document_path basic validation elapsed_ms=%.1f", elapsed_ms)
    if not doc_ok:
        raise ValueError(doc_msg)


def create_equipment(data: EquipmentCreate) -> EquipmentResponse:
    flow_started = time.perf_counter()
    _validate_document_path(data.document_path)
    now = _now_iso()

    conn = get_connection()
    try:
        insert_started = time.perf_counter()
        cursor = conn.execute(
            """
            INSERT INTO equipment (name, git_path, document_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.name.strip(),
                DEPRECATED_GIT_PATH,
                data.document_path.strip(),
                now,
                now,
            ),
        )
        conn.commit()
        equipment_id = cursor.lastrowid
        insert_ms = (time.perf_counter() - insert_started) * 1000
        logger.info(
            "Equipment create db_insert equipment_id=%s elapsed_ms=%.1f",
            equipment_id,
            insert_ms,
        )
        total_ms = (time.perf_counter() - flow_started) * 1000
        logger.info(
            "Equipment create flow complete equipment_id=%s total_elapsed_ms=%.1f",
            equipment_id,
            total_ms,
        )
        logger.info("Equipment added id=%s name=%s", equipment_id, data.name)
        return get_equipment(equipment_id)  # type: ignore[return-value]
    except sqlite3.IntegrityError as exc:
        logger.warning("Equipment add failed duplicate name=%s", data.name)
        raise DuplicateNameError(DUPLICATE_NAME_MESSAGE) from exc
    finally:
        conn.close()


def update_equipment(equipment_id: int, data: EquipmentUpdate) -> EquipmentResponse | None:
    existing = get_equipment(equipment_id)
    if existing is None:
        return None

    _validate_document_path(data.document_path)
    now = _now_iso()

    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE equipment
            SET name = ?, document_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (data.name.strip(), data.document_path.strip(), now, equipment_id),
        )
        conn.commit()
        logger.info("Equipment updated id=%s name=%s", equipment_id, data.name)
        return get_equipment(equipment_id)
    except sqlite3.IntegrityError as exc:
        logger.warning("Equipment update failed duplicate name=%s", data.name)
        raise DuplicateNameError(DUPLICATE_NAME_MESSAGE) from exc
    finally:
        conn.close()


def delete_equipment(equipment_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM equipment WHERE id = ?", (equipment_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info("Equipment deleted id=%s", equipment_id)
            return True
        return False
    finally:
        conn.close()


class DuplicateNameError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
