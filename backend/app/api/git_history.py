from fastapi import APIRouter, HTTPException, Query

from app.schemas.git_history import (
    CommitDetailResponse,
    CommitListResponse,
    CommitSearchParams,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.services.equipment_service import get_equipment
from app.services.git_history_service import get_commit_detail, search_commits
from app.services.git_service import GitSyncError, sync_equipment_git

from app.schemas.git_history import GitSyncResponse

equipment_router = APIRouter(prefix="/api/equipment", tags=["git-history"])
git_router = APIRouter(prefix="/api/git", tags=["git-history"])


@equipment_router.post("/{equipment_id}/sync/git", response_model=GitSyncResponse)
def sync_git_history(equipment_id: int) -> GitSyncResponse:
    if get_equipment(equipment_id) is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")

    try:
        result = sync_equipment_git(equipment_id)
    except GitSyncError as exc:
        if exc.message == "장비를 찾을 수 없습니다.":
            raise HTTPException(status_code=404, detail=exc.message) from exc
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return GitSyncResponse(
        equipment_id=result.equipment_id,
        scanned_commits=result.scanned_commits,
        new_commits=result.new_commits,
        skipped_commits=result.skipped_commits,
        new_changes=result.new_changes,
        status=result.status,
    )


@equipment_router.get("/{equipment_id}/git/commits", response_model=CommitListResponse)
def list_equipment_commits(
    equipment_id: int,
    repository_id: int | None = Query(None),
    q: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    file_path: str | None = Query(None),
    author: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> CommitListResponse:
    if get_equipment(equipment_id) is None:
        raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다.")

    params = CommitSearchParams(
        equipment_id=equipment_id,
        repository_id=repository_id,
        q=q.strip() if q else None,
        date_from=date_from,
        date_to=date_to,
        file_path=file_path.strip() if file_path else None,
        author=author.strip() if author else None,
        page=page,
        page_size=page_size,
    )
    return search_commits(params)


@git_router.get("/commits/{commit_id}", response_model=CommitDetailResponse)
def get_commit_by_id(commit_id: int) -> CommitDetailResponse:
    detail = get_commit_detail(commit_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Commit을 찾을 수 없습니다.")
    return detail
