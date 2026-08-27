from typing import Literal

from pydantic import BaseModel, Field, model_validator

SourceType = Literal["remote", "local"]
RepositoryStatus = Literal["pending", "preparing", "ready", "error"]


class GitRepositoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: SourceType


class GitRepositoryCreate(GitRepositoryBase):
    repository_url: str | None = None
    local_path: str | None = None

    @model_validator(mode="after")
    def validate_source_fields(self) -> "GitRepositoryCreate":
        if self.source_type == "remote":
            if not self.repository_url or not self.repository_url.strip():
                raise ValueError("Remote Repository URL을 입력하세요.")
        elif self.source_type == "local":
            if not self.local_path or not self.local_path.strip():
                raise ValueError("Local Repository 경로를 입력하세요.")
        return self


class GitRepositoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    repository_url: str | None = None
    local_path: str | None = None


class GitRepositoryResponse(BaseModel):
    id: int
    equipment_id: int
    name: str
    source_type: SourceType
    repository_url: str | None
    canonical_repository_url: str | None = None
    yona_username: str | None = None
    local_path: str
    status: RepositoryStatus
    created_at: str
    updated_at: str


class RepositoryValidateResponse(BaseModel):
    valid: bool
    message: str
    yona_username: str | None = None
    canonical_repository_url: str | None = None


class RemoteUrlValidateRequest(BaseModel):
    repository_url: str = Field(..., min_length=1)


class LocalPathValidateRequest(BaseModel):
    local_path: str = Field(..., min_length=1)


class RepositorySyncResponse(BaseModel):
    repository_id: int
    equipment_id: int
    scanned_commits: int
    new_commits: int
    skipped_commits: int
    new_changes: int
    status: str = "completed"
