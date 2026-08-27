/** STEP 8 Ollama Evidence Grounded Answer API client. */

import type { ChangeItemCandidate } from "./pptCache";
import type { EvidenceDebugInfo, EvidenceLinkItem, GitCandidate } from "./evidence";

export interface AnalysisRequest {
  equipment_id: number;
  query: string;
  file_path?: string;
  selected_code?: string;
  use_ollama?: boolean;
}

export interface EvidenceRefItem {
  type: string; // git | document
  commit?: string | null;
  file?: string | null;
  slide?: number | null;
}

export interface AnalysisResponse {
  equipment_id: number;
  query: string;
  use_ollama?: boolean;
  ai_used?: boolean;
  ai_available: boolean;
  ai_error?: string | null;
  summary?: string | null;
  reason?: string | null;
  confidence: string; // high | medium | low — Evidence rule-based
  inference: boolean;
  answer: string;
  answer_status?: string; // ok | partial | ollama_parse_error | ollama_skipped_by_user | ...
  evidence_summary?: string;
  evidence_answer?: string;
  ai_answer?: string | null;
  evidence: EvidenceRefItem[];
  parse_error: boolean;
  ai_evidence_missing: boolean;
  git_candidates: GitCandidate[];
  change_item_candidates: ChangeItemCandidate[];
  evidence_links: EvidenceLinkItem[];
  debug: EvidenceDebugInfo;
}

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

export async function fetchAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}/api/trace/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
