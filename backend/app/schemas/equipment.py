from pydantic import BaseModel, Field


class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    document_path: str = Field(..., min_length=1)


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(EquipmentBase):
    pass


class EquipmentResponse(EquipmentBase):
    id: int
    created_at: str
    updated_at: str


class PathValidateRequest(BaseModel):
    path: str = Field(..., min_length=1)


class GitPathValidateResponse(BaseModel):
    valid: bool
    message: str


class DocumentPathValidateResponse(BaseModel):
    valid: bool
    message: str
    pptx_count: int = 0
    recursive: bool = True
