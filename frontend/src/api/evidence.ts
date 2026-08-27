/** STEP 7 Evidence API client — ops validation only (no STEP 8). */

import type { ChangeItemCandidate, SourceFunctionItem } from "./pptCache";

export interface EvidenceRequest {
  equipment_id: number;
  query: string;
  file_path?: string;
  selected_code?: string;
}

export interface QueryMatchReasonItem {
  keyword: string;
  field: string;
  value: string;
  score: number;
  strength?: string;
}

export interface GitCandidate {
  repository_id: number;
  repository_name: string;
  commit_id: number;
  commit_hash: string;
  commit_date: string;
  message: string;
  file_path: string;
  score: number;
  match_reasons: string[];
  query_match_reasons?: QueryMatchReasonItem[];
  query_relevance_score?: number;
  query_relevance_level?: string;
}

export interface MatchReasonItem {
  type: string;
  score: number;
  git_value?: string | null;
  change_item_value?: string | null;
  distance_days?: number | null;
  match_level?: string | null;
}

export interface EvidenceLinkItem {
  git_commit_id: number;
  git_repository_id: number;
  git_commit_hash: string;
  git_file_path: string;
  change_item_cache_id: number;
  document_cache_id: number;
  link_score: number;
  match_reasons: MatchReasonItem[];
  diff_excerpt?: string | null;
  query_relevance_score?: number;
  query_relevance_level?: string;
  query_match_reasons?: QueryMatchReasonItem[];
  final_rank_score?: number;
}

export interface EvidenceDebugInfo {
  change_item_link_candidate_count: number;
  fallback_documents_parsed: number;
  change_item_total: number;
  equipment_filter_excluded?: number;
  equipment_filter_reason?: string;
  query_relevance_excluded_links?: number;
  query_keywords?: string[];
  weak_query_terms?: string[];
  request_functions?: string[];
  request_files?: string[];
  path_scopes?: string[];
}

export interface EvidenceResponse {
  equipment_id: number;
  query: string;
  query_keywords?: string[];
  weak_query_terms?: string[];
  request_functions?: string[];
  request_files?: string[];
  path_scopes?: string[];
  git_candidates: GitCandidate[];
  change_item_candidates: ChangeItemCandidate[];
  evidence_links: EvidenceLinkItem[];
  debug: EvidenceDebugInfo;
}

export type { SourceFunctionItem };

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg: string }) => d.msg).join(", ");
    }
  } catch {
    /* ignore */
  }
  return `요청 실패 (${response.status})`;
}

export async function fetchEvidence(request: EvidenceRequest): Promise<EvidenceResponse> {
  const response = await fetch(`${API_BASE}/api/trace/evidence`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
