from pydantic import BaseModel, Field


class TraceSearchRequest(BaseModel):
    equipment_id: int
    query: str = Field(..., min_length=1)
    file_path: str | None = None
    selected_code: str | None = None


class QueryMatchReasonItem(BaseModel):
    """Why a candidate relates to the user query (not Git↔Change Item link)."""

    keyword: str
    field: str
    value: str
    score: int
    strength: str = "core"  # core | weak


class GitCandidate(BaseModel):
    repository_id: int
    repository_name: str
    commit_id: int
    commit_hash: str
    commit_date: str
    message: str
    file_path: str
    score: int
    match_reasons: list[str]
    # Evidence-only enrichment (STEP 4 search leaves defaults).
    query_match_reasons: list[QueryMatchReasonItem] = Field(default_factory=list)
    query_relevance_score: int = 0
    query_relevance_level: str = "없음"


class SearchContext(BaseModel):
    keywords: list[str]
    date_from: str | None = None
    date_to: str | None = None


class TraceSearchResponse(BaseModel):
    equipment_id: int
    query: str
    git_candidates: list[GitCandidate]
    search_context: SearchContext


class PptCandidateItem(BaseModel):
    file_path: str
    file_name: str
    modified_at: str
    file_size: int
    candidate_score: int
    match_reasons: list[str]


class PptCandidateRequest(BaseModel):
    equipment_id: int
    keywords: list[str]
    date_from: str | None = None
    date_to: str | None = None


class PptCandidateResponse(BaseModel):
    equipment_id: int
    scanned_files: int
    ppt_candidates: list[PptCandidateItem]


class PptAnalysisRequest(BaseModel):
    equipment_id: int
    keywords: list[str]
    date_from: str | None = None
    date_to: str | None = None


class ProcessedDocumentItem(BaseModel):
    document_cache_id: int
    file_path: str
    file_name: str
    slide_count: int
    cache_hit: bool


class SlideCandidateItem(BaseModel):
    document_cache_id: int
    slide_cache_id: int
    file_path: str
    file_name: str
    slide_number: int
    title: str | None
    content: str | None = None
    matched_keywords: list[str]
    candidate_score: int
    from_cache_search: bool = False


class SourceFunctionItem(BaseModel):
    file_path: str | None = None
    functions: list[str] = Field(default_factory=list)
    raw_text: str = ""


class ChangeItemCandidateItem(BaseModel):
    change_item_cache_id: int
    document_cache_id: int
    slide_no: int
    file_path: str
    file_name: str
    item_no: str | None = None
    change_title: str | None = None
    csr_no: str | None = None
    business_background: str | None = None
    current_status: str | None = None
    as_is: str | None = None
    to_be: str | None = None
    source_functions: list[SourceFunctionItem] = Field(default_factory=list)
    test_cases: list[str] = Field(default_factory=list)
    applicable_scopes: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    candidate_score: int
    from_cache_search: bool = False
    from_fallback: bool = False
    # Evidence-only enrichment (PPT analysis leaves defaults).
    query_match_reasons: list[QueryMatchReasonItem] = Field(default_factory=list)
    query_relevance_score: int = 0
    query_relevance_level: str = "없음"


class PptAnalysisResponse(BaseModel):
    equipment_id: int
    ppt_candidate_count: int
    processed_documents: int
    cache_hits: int
    cache_misses: int
    parse_failures: int
    documents: list[ProcessedDocumentItem]
    slide_candidates: list[SlideCandidateItem]
    change_item_candidates: list[ChangeItemCandidateItem] = Field(default_factory=list)
    fallback_documents_parsed: int = 0
    change_item_total: int = 0
    equipment_filter_excluded: int = 0


# --- STEP 7: Evidence Link (Git Candidate <-> Change Item) ---


class EvidenceRequest(BaseModel):
    equipment_id: int
    query: str = Field(..., min_length=1)
    file_path: str | None = None
    selected_code: str | None = None


class MatchReasonItem(BaseModel):
    type: str
    score: int
    git_value: str | None = None
    change_item_value: str | None = None
    distance_days: int | None = None
    match_level: str | None = None


class EvidenceLinkItem(BaseModel):
    """References Git/Change Item by id rather than duplicating full objects —
    join against `git_candidates`/`change_item_candidates` in the same response."""

    git_commit_id: int
    git_repository_id: int
    git_commit_hash: str
    git_file_path: str
    change_item_cache_id: int
    document_cache_id: int
    link_score: int
    match_reasons: list[MatchReasonItem]
    diff_excerpt: str | None = None
    query_relevance_score: int = 0
    query_relevance_level: str = "없음"
    query_match_reasons: list[QueryMatchReasonItem] = Field(default_factory=list)
    final_rank_score: int = 0


class EvidenceDebugInfo(BaseModel):
    change_item_link_candidate_count: int = 0
    fallback_documents_parsed: int = 0
    change_item_total: int = 0
    equipment_filter_excluded: int = 0
    equipment_filter_reason: str = "filename equipment mismatch"
    query_relevance_excluded_links: int = 0
    query_keywords: list[str] = Field(default_factory=list)
    weak_query_terms: list[str] = Field(default_factory=list)
    request_functions: list[str] = Field(default_factory=list)
    request_files: list[str] = Field(default_factory=list)
    path_scopes: list[str] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    equipment_id: int
    query: str
    query_keywords: list[str] = Field(default_factory=list)
    weak_query_terms: list[str] = Field(default_factory=list)
    request_functions: list[str] = Field(default_factory=list)
    request_files: list[str] = Field(default_factory=list)
    path_scopes: list[str] = Field(default_factory=list)
    git_candidates: list[GitCandidate]
    change_item_candidates: list[ChangeItemCandidateItem]
    evidence_links: list[EvidenceLinkItem]
    debug: EvidenceDebugInfo
