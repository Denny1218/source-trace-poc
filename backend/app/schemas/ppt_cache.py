from pydantic import BaseModel


class DocumentCacheSummary(BaseModel):
    id: int
    equipment_id: int
    file_path: str
    file_name: str
    file_hash: str
    modified_at: str
    parsed_at: str
    slide_count: int


class SlideCacheItem(BaseModel):
    id: int
    slide_number: int
    title: str | None
    content: str


class DocumentCacheDetail(BaseModel):
    id: int
    equipment_id: int
    file_path: str
    file_name: str
    file_hash: str
    modified_at: str
    parsed_at: str
    slide_count: int
    slides: list[SlideCacheItem]


class DocumentCacheListResponse(BaseModel):
    equipment_id: int
    documents: list[DocumentCacheSummary]
