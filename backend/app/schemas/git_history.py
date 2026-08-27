import math
from dataclasses import dataclass

from pydantic import BaseModel, Field


class GitSyncResponse(BaseModel):
    equipment_id: int
    scanned_commits: int
    new_commits: int
    skipped_commits: int
    new_changes: int
    status: str


class CommitListItem(BaseModel):
    id: int
    commit_hash: str
    commit_date: str
    author: str
    message: str
    repository_id: int
    repository_name: str
    changed_file_count: int
    additions: int
    deletions: int


class CommitListResponse(BaseModel):
    items: list[CommitListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class CommitChangeDetail(BaseModel):
    id: int
    file_path: str
    change_type: str
    additions: int | None
    deletions: int | None
    diff: str | None


class CommitDetailResponse(BaseModel):
    id: int
    equipment_id: int
    repository_id: int
    repository_name: str
    commit_hash: str
    commit_date: str
    author: str
    message: str
    parent_hash: str | None
    changes: list[CommitChangeDetail]


@dataclass
class CommitSearchParams:
    equipment_id: int
    repository_id: int | None = None
    q: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    file_path: str | None = None
    author: str | None = None
    page: int = 1
    page_size: int = 50


MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50


def normalize_page_size(page_size: int) -> int:
    if page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def normalize_page(page: int) -> int:
    return max(page, 1)


def calc_total_pages(total: int, page_size: int) -> int:
    if total == 0:
        return 0
    return math.ceil(total / page_size)
