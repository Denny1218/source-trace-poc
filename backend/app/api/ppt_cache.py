from fastapi import APIRouter, HTTPException

from app.schemas.ppt_cache import (
    DocumentCacheDetail,
    DocumentCacheListResponse,
    DocumentCacheSummary,
    SlideCacheItem,
)
from app.services.equipment_service import get_equipment
from app.services.ppt_cache_service import (
    delete_document_cache,
    get_document_cache_by_id,
    get_slides_for_document,
    list_document_cache_by_equipment,
)

router = APIRouter(prefix="/api", tags=["ppt-cache"])


@router.get(
    "/equipment/{equipment_id}/ppt-cache",
    response_model=DocumentCacheListResponse,
)
def list_ppt_cache(equipment_id: int) -> DocumentCacheListResponse:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")

    docs = list_document_cache_by_equipment(equipment_id)
    return DocumentCacheListResponse(
        equipment_id=equipment_id,
        documents=[
            DocumentCacheSummary(
                id=d.id,
                equipment_id=d.equipment_id,
                file_path=d.file_path,
                file_name=d.file_name,
                file_hash=d.file_hash,
                modified_at=d.modified_at,
                parsed_at=d.parsed_at,
                slide_count=d.slide_count,
            )
            for d in docs
        ],
    )


@router.get("/ppt-cache/{document_cache_id}", response_model=DocumentCacheDetail)
def get_ppt_cache_detail(document_cache_id: int) -> DocumentCacheDetail:
    doc = get_document_cache_by_id(document_cache_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="PPT Cache를 찾을 수 없습니다.")

    slides = get_slides_for_document(document_cache_id)
    return DocumentCacheDetail(
        id=doc.id,
        equipment_id=doc.equipment_id,
        file_path=doc.file_path,
        file_name=doc.file_name,
        file_hash=doc.file_hash,
        modified_at=doc.modified_at,
        parsed_at=doc.parsed_at,
        slide_count=doc.slide_count,
        slides=[
            SlideCacheItem(
                id=s.id,
                slide_number=s.slide_number,
                title=s.title,
                content=s.content,
            )
            for s in slides
        ],
    )


@router.delete("/ppt-cache/{document_cache_id}", status_code=204)
def remove_ppt_cache(document_cache_id: int) -> None:
    doc = get_document_cache_by_id(document_cache_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="PPT Cache를 찾을 수 없습니다.")
    delete_document_cache(document_cache_id)
