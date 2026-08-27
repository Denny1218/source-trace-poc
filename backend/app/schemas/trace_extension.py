"""POC v2.3: Source Trace VS Code Extension request/response schema.

Reuses STEP 7/8 Evidence Grounded Answer (``build_evidence`` + ``analyze_evidence``)
untouched — this endpoint only reshapes the STEP 8 result into the Extension's
official Markdown answer. No Evidence/Link Score/Query Relevance/Parser/Cache/DB
Schema change here.

This is the sole official Backend contract for the Extension's direct-query
feature (PROJECT_SPEC v2.3 §"Continue 연동 제거" — Continue integration has been
removed from the project; the previous ``/api/continue/trace`` adapter payload
shape (``fullInput`` / ``options`` / ``workspacePath``) is not supported here).
"""

from pydantic import BaseModel, Field

from app.schemas.trace import EvidenceLinkItem


class ExtensionTraceRequest(BaseModel):
    equipment_id: int | None = None
    query: str | None = None
    file_path: str | None = None
    selected_code: str | None = None
    use_ollama: bool | None = None
    # VS Code Extension optional hints.
    source_mode: str | None = None
    detected_symbol: str | None = None


class ExtensionEvidenceRefItem(BaseModel):
    type: str  # git | document
    commit: str | None = None
    file: str | None = None
    slide: int | None = None


class ExtensionTraceResponse(BaseModel):
    name: str
    description: str
    content: str  # Markdown answer shown to the user in the result document

    # Convenience fields for direct API testing / a future custom UI.
    answer: str
    confidence: str  # high | medium | low — Evidence rule-based (STEP 8 unchanged)
    evidence_summary: str
    evidence_answer: str
    evidence_reason: str | None = None
    ai_answer: str | None = None
    ai_used: bool = False
    use_ollama: bool = True
    answer_status: str = "ok"
    citations: list[ExtensionEvidenceRefItem] = Field(default_factory=list)
    evidence_links: list[EvidenceLinkItem] = Field(default_factory=list)
    debug: dict = Field(default_factory=dict)
