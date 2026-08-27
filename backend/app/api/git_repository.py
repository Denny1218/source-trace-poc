from fastapi import APIRouter, HTTPException

from app.schemas.git_repository import (
    GitRepositoryCreate,
    GitRepositoryResponse,
    GitRepositoryUpdate,
    LocalPathValidateRequest,
    RemoteUrlValidateRequest,
    RepositorySyncResponse,
    RepositoryValidateResponse,
)
from app.services.equipment_service import get_equipment
from app.services.git_repository_service import (
    DuplicateCanonicalRepositoryError,
    DuplicateRepositoryNameError,
    GitRepositoryError,
    create_repository,
    delete_repository,
    get_repository,
    list_repositories,
    prepare_repository,
    update_repository,
    validate_remote_repository_url,
)
from app.services.path_validation_service import validate_local_git_path
from app.services.git_service import GitSyncError, sync_repository_git

equipment_router = APIRouter(prefix="/api/equipment", tags=["git-repositories"])
repository_router = APIRouter(prefix="/api/repositories", tags=["git-repositories"])


@repository_router.post("/validate/remote", response_model=RepositoryValidateResponse)
def validate_remote(data: RemoteUrlValidateRequest) -> RepositoryValidateResponse:
    valid, message, parsed = validate_remote_repository_url(data.repository_url.strip())
    return RepositoryValidateResponse(
        valid=valid,
        message=message,
        yona_username=parsed.yona_username if parsed else None,
        canonical_repository_url=parsed.canonical_url if parsed else None,
    )


@repository_router.post("/validate/local", response_model=RepositoryValidateResponse)
def validate_local(data: LocalPathValidateRequest) -> RepositoryValidateResponse:
    valid, message = validate_local_git_path(data.local_path.strip())
    return RepositoryValidateResponse(valid=valid, message=message)


@equipment_router.get(
    "/{equipment_id}/repositories", response_model=list[GitRepositoryResponse]
)
def get_equipment_repositories(equipment_id: int) -> list[GitRepositoryResponse]:
    if get_equipment(equipment_id) is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    return list_repositories(equipment_id)


@equipment_router.post(
    "/{equipment_id}/repositories",
    response_model=GitRepositoryResponse,
    status_code=201,
)
def post_repository(
    equipment_id: int, data: GitRepositoryCreate
) -> GitRepositoryResponse:
    if get_equipment(equipment_id) is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")
    try:
        return create_repository(equipment_id, data)
    except DuplicateRepositoryNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except DuplicateCanonicalRepositoryError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except GitRepositoryError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@repository_router.put("/{repository_id}", response_model=GitRepositoryResponse)
def put_repository(
    repository_id: int, data: GitRepositoryUpdate
) -> GitRepositoryResponse:
    try:
        repo = update_repository(repository_id, data)
    except DuplicateRepositoryNameError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except DuplicateCanonicalRepositoryError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except GitRepositoryError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if repo is None:
        raise HTTPException(status_code=404, detail="Repository를 찾을 수 없습니다.")
    return repo


@repository_router.delete("/{repository_id}", status_code=204)
def remove_repository(repository_id: int) -> None:
    deleted = delete_repository(repository_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository를 찾을 수 없습니다.")


@repository_router.get("/{repository_id}", response_model=GitRepositoryResponse)
def get_repository_by_id(repository_id: int) -> GitRepositoryResponse:
    repo = get_repository(repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository를 찾을 수 없습니다.")
    return repo


@repository_router.post("/{repository_id}/prepare", response_model=GitRepositoryResponse)
def post_prepare_repository(repository_id: int) -> GitRepositoryResponse:
    try:
        repo = prepare_repository(repository_id)
    except GitRepositoryError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if repo is None:
        raise HTTPException(status_code=404, detail="Repository를 찾을 수 없습니다.")
    return repo


@repository_router.post("/{repository_id}/sync", response_model=RepositorySyncResponse)
def sync_repository(repository_id: int) -> RepositorySyncResponse:
    repo = get_repository(repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository를 찾을 수 없습니다.")

    try:
        result = sync_repository_git(repository_id)
    except GitSyncError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return RepositorySyncResponse(
        repository_id=repository_id,
        equipment_id=result.equipment_id,
        scanned_commits=result.scanned_commits,
        new_commits=result.new_commits,
        skipped_commits=result.skipped_commits,
        new_changes=result.new_changes,
        status=result.status,
    )
