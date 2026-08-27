"""STEP 8: Ollama Evidence Grounded Answer request/response schemas."""

from pydantic import BaseModel, Field

from app.schemas.trace import (
    ChangeItemCandidateItem,
    EvidenceDebugInfo,
    EvidenceLinkItem,
    GitCandidate,
)


class AnalysisRequest(BaseModel):
    equipment_id: int
    query: str = Field(..., min_length=1)
    file_path: str | None = None
    selected_code: str | None = None
    # false: skip Ollama entirely, return server Evidence-based summary only.
    use_ollama: bool = True


class EvidenceRefItem(BaseModel):
    type: str  # git | document
    commit: str | None = None
    file: str | None = None
    slide: int | None = None


class OllamaTinyTestResponse(BaseModel):
    ok: bool
    model: str
    elapsed_ms: int
    response_preview: str | None = None
    error_type: str | None = None
    base_url: str | None = None
    timeout_seconds: float | None = None


class AnalysisResponse(BaseModel):
    equipment_id: int
    query: str
    use_ollama: bool = True
    ai_used: bool = False
    ai_available: bool
    ai_error: str | None = None
    summary: str | None = None
    reason: str | None = None
    confidence: str = "low"  # high | medium | low — Evidence rule-based
    inference: bool = False
    answer: str
    answer_status: str = "ok"  # ok | partial | ollama_parse_error | ollama_unavailable | ...
    # Server Evidence-only summary/answer — always populated, never replaced
    # by AI text. Display this first; render ai_answer as a separate section.
    evidence_summary: str = ""
    evidence_answer: str = ""
    evidence_reason: str | None = None
    ai_answer: str | None = None
    evidence: list[EvidenceRefItem] = Field(default_factory=list)
    parse_error: bool = False
    ai_evidence_missing: bool = False
    # STEP 7 Evidence — always returned even when AI 분석 unavailable (원칙 13).
    git_candidates: list[GitCandidate] = Field(default_factory=list)
    change_item_candidates: list[ChangeItemCandidateItem] = Field(default_factory=list)
    evidence_links: list[EvidenceLinkItem] = Field(default_factory=list)
    debug: EvidenceDebugInfo
