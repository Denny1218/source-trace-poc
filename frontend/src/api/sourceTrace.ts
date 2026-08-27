import type { GitRepository } from "./repositories";

export interface TraceReportRequest {
  equipment_id: number;
  query: string;
  file_path?: string;
  selected_code?: string;
  use_ollama?: boolean;
  detected_symbol?: string;
  source_mode?: string;
}

export interface TraceReportResponse {
  name: string;
  description: string;
  content: string;
  answer: string;
  confidence: string;
  evidence_summary: string;
  evidence_answer: string;
  evidence_reason?: string | null;
  ai_answer?: string | null;
  ai_used: boolean;
  use_ollama: boolean;
  answer_status: string;
  debug: Record<string, unknown>;
}

export interface TraceSelectionRequest {
  equipment_id: number;
  repo_relative_path: string;
  repo_id_hint?: number;
  start_line: number;
  end_line: number;
  selected_code: string;
  enclosing_symbol?: string;
  revision: string;
}

export interface TraceSelectionResponse {
  name: string;
  description: string;
  content: string;
  analysis_mode: string;
  answer_status: string;
  equipment_id?: number | null;
  file_path?: string | null;
  start_line?: number | null;
  end_line?: number | null;
  enclosing_symbol?: string | null;
  debug: Record<string, unknown>;
}

export interface SourceTraceReportForm {
  equipmentId: number;
  filePath: string;
  functionName: string;
}

export interface SourceTraceSelectionForm {
  equipmentId: number;
  repositoryId?: number;
  filePath: string;
  startLine: number;
  endLine: number;
  selectedCode: string;
  enclosingSymbol: string;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const DEFAULT_FUNCTION_HISTORY_QUERY = "선택한 코드가 왜 변경됐는지 알려줘";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { msg?: string }) => d.msg || "").filter(Boolean).join(", ");
    }
  } catch {
    /* ignore */
  }
  return `요청 실패 (${response.status})`;
}

function normalizeRelativePath(path: string): string {
  return path.trim().replace(/\\/g, "/").replace(/^\/+/, "");
}

export function buildTraceReportRequest(form: SourceTraceReportForm): TraceReportRequest {
  const functionName = form.functionName.trim();
  const filePath = normalizeRelativePath(form.filePath);
  return {
    equipment_id: form.equipmentId,
    query: DEFAULT_FUNCTION_HISTORY_QUERY,
    selected_code: functionName,
    detected_symbol: functionName,
    source_mode: "cursor_word",
    use_ollama: false,
    ...(filePath ? { file_path: filePath } : {}),
  };
}

export function buildTraceSelectionRequest(
  form: SourceTraceSelectionForm,
): TraceSelectionRequest {
  const filePath = normalizeRelativePath(form.filePath);
  const symbol = form.enclosingSymbol.trim();
  return {
    equipment_id: form.equipmentId,
    repo_relative_path: filePath,
    start_line: form.startLine,
    end_line: form.endLine,
    selected_code: form.selectedCode.trim(),
    revision: "HEAD",
    ...(symbol ? { enclosing_symbol: symbol } : {}),
    ...(form.repositoryId ? { repo_id_hint: form.repositoryId } : {}),
  };
}

export function getRepositorySelectionState(repositories: GitRepository[]): {
  hasSingleRepository: boolean;
  requiresExplicitChoice: boolean;
} {
  return {
    hasSingleRepository: repositories.length === 1,
    requiresExplicitChoice: repositories.length > 1,
  };
}

export function mapSourceTraceErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : "요청 처리 중 오류가 발생했습니다.";
  const normalized = message.toLowerCase();
  if (
    normalized.includes("failed to fetch") ||
    normalized.includes("networkerror") ||
    normalized.includes("load failed")
  ) {
    return "서버에 연결할 수 없습니다.";
  }
  if (
    message.includes("repo_relative_path") ||
    message.includes("Repository를 특정할 수 없습니다") ||
    message.includes("repository")
  ) {
    return "Repository를 특정할 수 없습니다.";
  }
  return message;
}

export async function fetchTraceReport(
  request: TraceReportRequest,
): Promise<TraceReportResponse> {
  const response = await fetch(`${API_BASE}/api/trace/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function fetchTraceSelection(
  request: TraceSelectionRequest,
): Promise<TraceSelectionResponse> {
  const response = await fetch(`${API_BASE}/api/trace/selection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
