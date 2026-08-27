export interface DocumentCacheSummary {
  id: number;
  equipment_id: number;
  file_path: string;
  file_name: string;
  file_hash: string;
  modified_at: string;
  parsed_at: string;
  slide_count: number;
}

export interface SlideCacheItem {
  id: number;
  slide_number: number;
  title: string | null;
  content: string;
}

export interface DocumentCacheDetail extends DocumentCacheSummary {
  slides: SlideCacheItem[];
}

export interface PptAnalysisRequest {
  equipment_id: number;
  keywords: string[];
  date_from?: string;
  date_to?: string;
}

export interface SlideCandidateItem {
  document_cache_id: number;
  slide_cache_id: number;
  file_path: string;
  file_name: string;
  slide_number: number;
  title: string | null;
  content?: string | null;
  matched_keywords: string[];
  candidate_score: number;
  from_cache_search?: boolean;
}

export interface SourceFunctionItem {
  file_path: string | null;
  functions: string[];
  raw_text: string;
}

export interface ChangeItemCandidate {
  change_item_cache_id: number;
  document_cache_id: number;
  slide_no: number;
  file_path: string;
  file_name: string;
  item_no: string | null;
  change_title: string | null;
  csr_no: string | null;
  business_background: string | null;
  current_status: string | null;
  as_is: string | null;
  to_be: string | null;
  source_functions: SourceFunctionItem[];
  test_cases: string[];
  applicable_scopes: string[];
  matched_keywords: string[];
  candidate_score: number;
  from_cache_search?: boolean;
  from_fallback?: boolean;
  query_match_reasons?: Array<{
    keyword: string;
    field: string;
    value: string;
    score: number;
    strength?: string;
  }>;
  query_relevance_score?: number;
  query_relevance_level?: string;
}

export interface PptAnalysisResponse {
  equipment_id: number;
  ppt_candidate_count: number;
  processed_documents: number;
  cache_hits: number;
  cache_misses: number;
  parse_failures: number;
  documents: Array<{
    document_cache_id: number;
    file_path: string;
    file_name: string;
    slide_count: number;
    cache_hit: boolean;
  }>;
  slide_candidates: SlideCandidateItem[];
  change_item_candidates: ChangeItemCandidate[];
  fallback_documents_parsed: number;
  change_item_total: number;
  equipment_filter_excluded?: number;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* ignore */
  }
  return `요청 실패 (${response.status})`;
}

export async function fetchPptCacheList(equipmentId: number): Promise<DocumentCacheSummary[]> {
  const response = await fetch(`${API_BASE}/api/equipment/${equipmentId}/ppt-cache`);
  if (!response.ok) throw new Error(await parseError(response));
  const data = await response.json();
  return data.documents;
}

export async function fetchPptCacheDetail(documentCacheId: number): Promise<DocumentCacheDetail> {
  const response = await fetch(`${API_BASE}/api/ppt-cache/${documentCacheId}`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function deletePptCache(documentCacheId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/ppt-cache/${documentCacheId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function runPptAnalysis(body: PptAnalysisRequest): Promise<PptAnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/trace/ppt-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
