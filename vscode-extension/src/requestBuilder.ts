/**
 * Pure, VS Code-API-free helpers for STEP 9-2 (VS Code Extension MVP).
 *
 * Kept separate from extension.ts so the request-body construction and
 * result-markdown selection logic can be unit tested with plain `node:test`
 * (no @vscode/test-electron harness needed for this MVP). No Backend logic
 * is duplicated here — this only shapes the same request/response contract
 * that `POST /api/trace/report` (PROJECT_SPEC v2.3) already accepts/returns.
 */

import { basenameFromPath } from "./editorContext";
import { augmentQueryWithSymbol } from "./symbolExtractor";

export interface AnalyzeRequestBody {
  equipment_id: number;
  query: string;
  file_path: string;
  selected_code: string;
  use_ollama: boolean;
  source_mode?: string;
  detected_symbol?: string;
}

export interface BuildRequestBodyParams {
  equipmentId: number;
  query: string;
  filePath: string;
  selectedCode: string;
  useOllama: boolean;
  maxSelectedCodeChars: number;
}

export interface BuildAnalyzeRequestParams extends BuildRequestBodyParams {
  detectedSymbol?: string;
  sourceMode?: string;
}

export interface ExtensionDebugInfo {
  source_mode: string;
  detected_symbol?: string;
  selected_text_chars: number;
  selected_code_sent_chars: number;
  query_sent: string;
  file_path_basename?: string;
  selected_text_preview?: string;
}

export interface AnalyzeRequestResult {
  body: AnalyzeRequestBody;
  truncated: boolean;
  debug: ExtensionDebugInfo;
}

export interface ResultDocumentParams {
  response: unknown;
  detectedSymbol?: string;
  filePath?: string;
  debug?: ExtensionDebugInfo;
  queriedAt?: Date;
  /** When false (default), Extension debug is omitted from the Markdown body. */
  showDebug?: boolean;
}

export interface TruncateResult {
  code: string;
  truncated: boolean;
}

const PREVIEW_MAX_CHARS = 100;

/** Bound selected code before it ever leaves the editor (never send a full file). */
export function truncateSelectedCode(code: string, maxChars: number): TruncateResult {
  if (!code || code.length <= maxChars) {
    return { code: code ?? "", truncated: false };
  }
  return { code: code.slice(0, maxChars), truncated: true };
}

/** Shapes the exact JSON body POSTed to `POST /api/trace/report`. */
export function buildRequestBody(
  params: BuildRequestBodyParams
): { body: AnalyzeRequestBody; truncated: boolean } {
  const { code, truncated } = truncateSelectedCode(
    params.selectedCode,
    params.maxSelectedCodeChars
  );
  return {
    body: {
      equipment_id: params.equipmentId,
      query: params.query,
      file_path: params.filePath,
      selected_code: code,
      use_ollama: params.useOllama,
    },
    truncated,
  };
}

/**
 * Builds the Backend request with symbol-augmented query and non-empty
 * selected_code whenever a symbol or selection text is available.
 */
export function buildAnalyzeRequest(params: BuildAnalyzeRequestParams): AnalyzeRequestResult {
  const selectedText = (params.selectedCode ?? "").trim();
  const symbol = params.detectedSymbol?.trim();
  const selectedForBody =
    selectedText || symbol || "";

  const augmentedQuery = augmentQueryWithSymbol(params.query, symbol);
  const sent = truncateSelectedCode(selectedForBody, params.maxSelectedCodeChars);
  const bodyBase = {
    equipment_id: params.equipmentId,
    query: augmentedQuery,
    file_path: params.filePath,
    selected_code: sent.code,
    use_ollama: params.useOllama,
  };
  const body: AnalyzeRequestBody =
    params.sourceMode || symbol
      ? {
          ...bodyBase,
          ...(params.sourceMode ? { source_mode: params.sourceMode } : {}),
          ...(symbol ? { detected_symbol: symbol } : {}),
        }
      : bodyBase;

  const basename = basenameFromPath(params.filePath);
  const debug: ExtensionDebugInfo = {
    source_mode: params.sourceMode ?? "none",
    detected_symbol: symbol || undefined,
    selected_text_chars: selectedText.length,
    selected_code_sent_chars: body.selected_code.length,
    query_sent: body.query,
    file_path_basename: basename,
    selected_text_preview: previewText(selectedText || symbol || "", PREVIEW_MAX_CHARS),
  };

  return { body, truncated: sent.truncated, debug };
}

// ── Selection code request (PROJECT_SPEC v2.4 §5) ─────────────────────────
// Separate mode/schema from the function-history request above — never
// merged into `AnalyzeRequestBody` / `buildAnalyzeRequest`.

export interface SelectionRequestBody {
  equipment_id: number;
  /** Official v2.6: relative path required; repo_id_hint optional */
  repo_id?: number;
  repo_id_hint?: number;
  repo_relative_path?: string;
  /** Deprecated fallback for older contracts / debug */
  file_path?: string;
  client_file_path?: string;
  start_line: number;
  end_line: number;
  selected_code: string;
  enclosing_symbol?: string;
  revision: string;
}

export interface BuildSelectionRequestParams {
  equipmentId: number;
  /** Absolute editor path — debug / deprecated fallback only */
  filePath: string;
  /** Preferred: registered repository id */
  repoId?: number;
  /** Preferred: path relative to that repository root */
  repoRelativePath?: string;
  startLine: number;
  endLine: number;
  selectedCode: string;
  enclosingSymbol?: string;
  maxSelectedCodeChars: number;
  revision?: string;
}

export interface SelectionDebugInfo {
  start_line: number;
  end_line: number;
  enclosing_symbol?: string;
  selected_text_chars: number;
  selected_code_sent_chars: number;
  file_path_basename?: string;
  repo_id?: number;
  repo_relative_path?: string;
}

export interface SelectionRequestResult {
  body: SelectionRequestBody;
  truncated: boolean;
  debug: SelectionDebugInfo;
}

export function buildSelectionRequest(
  params: BuildSelectionRequestParams
): SelectionRequestResult {
  const raw = params.selectedCode ?? "";
  const sent = truncateSelectedCode(raw, params.maxSelectedCodeChars);
  const symbol = params.enclosingSymbol?.trim();
  const repoId = params.repoId;
  const repoRelativePath = (params.repoRelativePath || "").trim() || undefined;
  const body: SelectionRequestBody = {
    equipment_id: params.equipmentId,
    start_line: params.startLine,
    end_line: params.endLine,
    selected_code: sent.code,
    revision: params.revision?.trim() || "HEAD",
    ...(symbol ? { enclosing_symbol: symbol } : {}),
  };
  if (repoRelativePath) {
    body.repo_relative_path = repoRelativePath.replace(/\\/g, "/");
    if (repoId != null && repoId > 0) {
      body.repo_id = repoId;
      body.repo_id_hint = repoId;
    }
    if (params.filePath?.trim()) {
      body.client_file_path = params.filePath;
    }
  } else if (params.filePath?.trim()) {
    // Deprecated fallback for callers that have not resolved a relative path.
    body.file_path = params.filePath;
  }
  const debug: SelectionDebugInfo = {
    start_line: params.startLine,
    end_line: params.endLine,
    enclosing_symbol: symbol || undefined,
    selected_text_chars: raw.length,
    selected_code_sent_chars: sent.code.length,
    file_path_basename: basenameFromPath(
      repoRelativePath || params.filePath || ""
    ),
    repo_id: repoId,
    repo_relative_path: body.repo_relative_path,
  };
  return { body, truncated: sent.truncated, debug };
}

function previewText(text: string, maxChars: number): string | undefined {
  const t = text.trim();
  if (!t) {
    return undefined;
  }
  if (t.length <= maxChars) {
    return t;
  }
  return t.slice(0, maxChars) + "…";
}

export function formatQueriedAt(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/** Dynamic document title: symbol > file basename > generic. */
export function buildResultTitle(
  detectedSymbol?: string,
  filePath?: string
): string {
  const symbol = (detectedSymbol ?? "").trim();
  if (symbol) {
    return `# ${symbol} 변경 이력 분석 결과`;
  }
  const base = basenameFromPath(filePath);
  if (base) {
    return `# ${base} 변경 이력 분석 결과`;
  }
  return "# 장비 변경 이력 분석 결과";
}

export function formatDebugSection(debug: ExtensionDebugInfo | undefined): string {
  if (!debug) {
    return "";
  }
  const parts = [
    `source_mode=\`${debug.source_mode}\``,
    debug.detected_symbol ? `symbol=\`${debug.detected_symbol}\`` : undefined,
    `selected_text=${debug.selected_text_chars} chars`,
    `selected_code_sent=${debug.selected_code_sent_chars} chars`,
    `query=\`${truncateForInline(debug.query_sent, 80)}\``,
    debug.file_path_basename ? `file=\`${debug.file_path_basename}\`` : undefined,
    debug.selected_text_preview
      ? `preview=\`${truncateForInline(debug.selected_text_preview, PREVIEW_MAX_CHARS)}\``
      : undefined,
  ].filter(Boolean);

  return (
    `\n\n<details>\n<summary>Extension debug</summary>\n\n` +
    `> ${parts.join(" · ")}\n\n` +
    `</details>\n`
  );
}

function truncateForInline(text: string, max: number): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) {
    return t;
  }
  return t.slice(0, max) + "…";
}

/**
 * Server Evidence summary is always the primary result (STEP 8/9 policy) —
 * `content`/`answer` already embed it ahead of any AI 보조 설명 section, so
 * picking the first available field never promotes an Ollama-only answer
 * above the server Evidence summary.
 */
export function pickResultMarkdown(response: unknown): string {
  if (response && typeof response === "object") {
    const obj = response as Record<string, unknown>;
    for (const key of ["content", "answer", "evidence_answer"]) {
      const value = obj[key];
      if (typeof value === "string" && value.trim().length > 0) {
        return value;
      }
    }
  }
  return "```json\n" + JSON.stringify(response, null, 2) + "\n```";
}

/** Full Markdown document — unique title + timestamp; debug only when showDebug. */
export function buildResultDocumentText(params: ResultDocumentParams): string {
  const queriedAt = formatQueriedAt(params.queriedAt ?? new Date());
  const showDebug = params.showDebug === true;
  const debugBlock = showDebug ? formatDebugSection(params.debug) : "";
  const body = pickResultMarkdown(params.response).trim();
  // Backend lifecycle markdown already ends with `조회: YYYY-MM-DD HH:MM`.
  // Do not append a second, synonymous "조회 시각" footer.
  const hasBackendQueryFooter = /(?:^|\n)조회:\s*\d{4}-\d{2}-\d{2}/.test(body);
  if (body.startsWith("# ")) {
    if (hasBackendQueryFooter) {
      return `${body}${debugBlock}\n`;
    }
    return `${body}\n\n---\n조회: ${queriedAt}${debugBlock}\n`;
  }
  const title = buildResultTitle(params.detectedSymbol, params.filePath);
  return `${title}\n\n---\n조회: ${queriedAt}\n\n${body}${debugBlock}\n`;
}

/** @deprecated Use buildResultDocumentText(params) — kept for backward-compat in tests. */
export function buildResultDocumentTextLegacy(response: unknown): string {
  return buildResultDocumentText({ response });
}
