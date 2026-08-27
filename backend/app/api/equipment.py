from fastapi import APIRouter, HTTPException

from app.schemas.equipment import (
    DocumentPathValidateResponse,
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
    GitPathValidateResponse,
    PathValidateRequest,
)
from app.services.equipment_service import (
    DuplicateNameError,
    create_equipment,
    delete_equipment,
    get_equipment,
    list_equipment,
    update_equipment,
)
from app.services.path_validation_service import validate_document_path, validate_local_git_path

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.post("/validate/git", response_model=GitPathValidateResponse)
def validate_git(data: PathValidateRequest) -> GitPathValidateResponse:
    valid, message = validate_local_git_path(data.path.strip())
    return GitPathValidateResponse(valid=valid, message=message)


@router.post("/validate/document", response_model=DocumentPathValidateResponse)
def validate_document(data: PathValidateRequest) -> DocumentPathValidateResponse:
    valid, message, pptx_count = validate_document_path(data.path.strip())
    return DocumentPathValidateResponse(
        valid=valid,
        message=message,
        pptx_count=pptx_count,
        recursive=True,
    )


@router.get("", response_model=list[EquipmentResponse])
def get_equipment_list() -> list[EquipmentResponse]:
    return list_equipment()


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(equipment_id: int) -> EquipmentResponse:
    equipment = get_equipment(equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    return equipment


@router.post("", response_model=EquipmentResponse, status_code=201)
def post_equipment(data: EquipmentCreate) -> EquipmentResponse:
    try:
        return create_equipment(data)
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{equipment_id}", response_model=EquipmentResponse)
def put_equipment(equipment_id: int, data: EquipmentUpdate) -> EquipmentResponse:
    try:
        equipment = update_equipment(equipment_id, data)
    except DuplicateNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if equipment is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    return equipment


@router.delete("/{equipment_id}", status_code=204)
def remove_equipment(equipment_id: int) -> None:
    deleted = delete_equipment(equipment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
