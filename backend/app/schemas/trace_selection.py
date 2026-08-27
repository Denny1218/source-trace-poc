"""PROJECT_SPEC v2.6 — 선택 코드 변경 근거 조회 요청/응답 스키마.

함수/Symbol 전체 이력 조회(``ExtensionTraceRequest`` / ``/api/trace/report``)와
분리된 별도 계약이다. 선택 코드 조회는 항상 ``analysis_mode="selection"`` 이며
1차 근거는 git blame·Diff·line history이다.

파일 식별 (v2.6):
  ``equipment_id`` + ``repo_relative_path`` 필수,
  ``repo_id_hint`` / ``repo_id`` 선택.
Backend 공통 ``resolve_equipment_repository`` 가 Repo를 결정한다.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator


MAX_SELECTION_LINE_SPAN = 400


class SelectionTraceRequest(BaseModel):
    equipment_id: int | None = None
    # Official contract (PROJECT_SPEC v2.6)
    repo_relative_path: str | None = None
    repo_id_hint: int | None = None
    # Alias for repo_id_hint (older Extension 0.4.x)
    repo_id: int | None = None
    # Deprecated: absolute / workspace path from older VSIX (fallback only)
    file_path: str | None = None
    # Optional debug aid — never used as the primary identity key
    client_file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    selected_code: str | None = None
    enclosing_symbol: str | None = None
    revision: str = "HEAD"

    @field_validator("revision")
    @classmethod
    def _default_revision(cls, v: str | None) -> str:
        v = (v or "").strip()
        return v or "HEAD"

    @field_validator("repo_relative_path", "file_path", "client_file_path")
    @classmethod
    def _strip_paths(cls, v: str | None) -> str | None:
        if v is None:
            return None
        text = str(v).strip()
        return text or None

    @model_validator(mode="after")
    def _sync_repo_hint(self) -> SelectionTraceRequest:
        if self.repo_id_hint is None and self.repo_id is not None:
            self.repo_id_hint = self.repo_id
        return self


class SelectionBlameRow(BaseModel):
    commit_hash: str
    short_hash: str
    start_line: int
    end_line: int
    author: str | None = None
    author_date: str | None = None
    commit_message: str | None = None
    is_uncommitted: bool = False
    is_boundary: bool = False
    change_kind: str = "unknown"
    # Minimal overlapping Diff hunk(s) for user display (not full-file Diff).
    before_code: str | None = None
    after_code: str | None = None
    diff_hunk: str | None = None


class SelectionLineHistoryRow(BaseModel):
    commit_hash: str
    short_hash: str
    date: str | None = None
    subject: str | None = None


class SelectionDocumentLink(BaseModel):
    document_name: str | None = None
    slide_number: int | None = None
    change_title: str | None = None
    csr_no: str | None = None
    versions: list[str] = Field(default_factory=list)
    link_reason: str | None = None


class SelectionTraceResponse(BaseModel):
    name: str = "선택 코드 변경 근거"
    description: str = ""
    content: str
    analysis_mode: str = "selection"
    answer_status: str = "ok"
    equipment_id: int | None = None
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    enclosing_symbol: str | None = None
    blame_rows: list[SelectionBlameRow] = Field(default_factory=list)
    line_history: list[SelectionLineHistoryRow] = Field(default_factory=list)
    line_history_available: bool = False
    document_links: list[SelectionDocumentLink] = Field(default_factory=list)
    debug: dict = Field(default_factory=dict)
