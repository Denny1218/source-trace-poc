import * as path from "path";

export interface LifecycleSummary {
  total_candidates?: number;
  direct_confirmed_count?: number;
  displayed_git_count?: number;
  subsequent_change_count?: number;
  related_document_count?: number;
  creation_count?: number;
  core_followup_count?: number;
  other_count?: number;
  maintenance_count?: number;
  unconfirmed_count?: number;
  excluded_count?: number;
  ppt_direct_count?: number;
  ppt_feature_release_count?: number;
  ppt_dev_reference_count?: number;
  ppt_maintenance_count?: number;
  ppt_official_doc_count?: number;
  ppt_commit_direct_doc_count?: number;
  ppt_stage_link_doc_count?: number;
  ppt_related_ref_doc_count?: number;
  ppt_indirect_count?: number;
  git_only_count?: number;
  overall_confidence?: string;
}

export interface BeginContext {
  requestKind?: string;
  userQuestion?: string;
  symbol?: string;
  file?: string;
  equipment?: { id: number; name: string; serverUrl?: string };
}

export interface SelectionSummary {
  blameGroupCount?: number;
  primaryCommitShortHash?: string;
  lineHistoryAvailable?: boolean;
  lineHistoryCount?: number;
  documentLinkCount?: number;
}

type AppendLineChannel = { appendLine(value: string): void; show?(preserveFocus?: boolean): void };

export class ProgressLogger {
  private readonly startMs: number;
  private lastMs: number;
  private lastStage = "";

  constructor(private readonly channel: AppendLineChannel) {
    this.startMs = Date.now();
    this.lastMs = this.startMs;
  }

  begin(ctx: BeginContext): void {
    // Continue 연동 제거 이후에도 일반 Source Trace Output은 항상 자동으로
    // 표시되어야 한다 (PROJECT_SPEC v2.4 §12) — 사용자가 Output 드롭다운에서
    // 수동으로 채널을 선택하지 않아도 매 조회 시작 시 패널이 노출된다.
    this.channel.show?.(true);
    const ts = formatTime(new Date());
    this.channel.appendLine("--------------------------------------------------");
    this.channel.appendLine(`[${ts}] Source Trace 분석 시작`);
    if (ctx.equipment?.serverUrl) {
      this.channel.appendLine(`서버: ${ctx.equipment.serverUrl}`);
    }
    if (ctx.equipment) {
      this.channel.appendLine(`장비: ${ctx.equipment.name}`);
    }
    this.channel.appendLine(`요청: ${ctx.requestKind ?? "변경 이력 조회"}`);
    if (ctx.userQuestion) {
      this.channel.appendLine(`사용자 질문: ${ctx.userQuestion}`);
    }
    if (ctx.symbol) {
      this.channel.appendLine(`함수: ${ctx.symbol}`);
    }
    if (ctx.file) {
      this.channel.appendLine(`파일: ${toDisplayPath(ctx.file)}`);
    }
    this.channel.appendLine("--------------------------------------------------");
  }

  step(stage: string, message?: string): void {
    if (stage === this.lastStage) {
      return;
    }
    this.lastStage = stage;
    const now = Date.now();
    const ts = formatTime(new Date());
    const suffix = message ?? stage;
    this.channel.appendLine(`[${ts}] ${suffix}`);
    this.lastMs = now;
  }

  stats(summary: LifecycleSummary | undefined, overallConfidence?: string): void {
    if (!summary && !overallConfidence) {
      return;
    }
    const ts = formatTime(new Date());
    const gitCount =
      summary?.displayed_git_count ??
      summary?.direct_confirmed_count ??
      summary?.total_candidates ??
      undefined;
    if (gitCount !== undefined) {
      this.channel.appendLine(`[${ts}] Git 이력: ${gitCount}건`);
    }
    const docs =
      summary?.related_document_count ?? summary?.ppt_official_doc_count;
    if (docs !== undefined) {
      this.channel.appendLine(`[${ts}] 관련 문서: ${docs}건`);
    }
  }

  /** PROJECT_SPEC v2.6 — 선택 코드 조회 진행 로그. */
  selectionStats(summary: SelectionSummary | undefined): void {
    if (!summary) {
      return;
    }
    const ts = formatTime(new Date());
    if (summary.primaryCommitShortHash) {
      this.channel.appendLine(`[${ts}] 현재 라인 Commit: ${summary.primaryCommitShortHash}`);
    } else if (summary.blameGroupCount === 0) {
      this.channel.appendLine(`[${ts}] 현재 라인 Commit: 확인되지 않음`);
    }
    if (summary.lineHistoryAvailable === false) {
      this.channel.appendLine(`[${ts}] line history 확인 제한 (코드 이동/Git 추적 제한 가능)`);
    } else if (summary.lineHistoryCount !== undefined) {
      this.channel.appendLine(`[${ts}] line history 조회 완료 (${summary.lineHistoryCount}건)`);
    }
    if (summary.documentLinkCount !== undefined) {
      this.channel.appendLine(`[${ts}] 관련 문서: ${summary.documentLinkCount}건`);
    }
  }

  complete(): void {
    const total = ((Date.now() - this.startMs) / 1000).toFixed(1);
    const ts = formatTime(new Date());
    this.channel.appendLine(`[${ts}] 분석 완료 (${total}초)`);
    this.channel.appendLine("--------------------------------------------------");
  }

  fail(stage: string, cause: string, hintLines?: string[]): void {
    const elapsed = ((Date.now() - this.startMs) / 1000).toFixed(1);
    const ts = formatTime(new Date());
    this.channel.appendLine(`[${ts}] 분석 실패`);
    this.channel.appendLine(`실패 단계: ${stage}`);
    this.channel.appendLine(`원인: ${cause}`);
    const hints =
      hintLines && hintLines.length
        ? hintLines
        : ["서버 실행 상태와 API 주소를 확인하세요."];
    if (hints.length === 1) {
      this.channel.appendLine(`확인 사항: ${hints[0]}`);
    } else {
      this.channel.appendLine("확인 사항:");
      for (const h of hints) {
        this.channel.appendLine(`- ${h}`);
      }
    }
    this.channel.appendLine(`경과 시간: ${elapsed}초`);
    this.channel.appendLine("--------------------------------------------------");
  }

  diagnostic(lines: string[]): void {
    if (!lines.length) {
      return;
    }
    this.channel.appendLine("[진단]");
    for (const line of lines) {
      this.channel.appendLine(line);
    }
  }
}

export function extractLifecycleSummary(response: unknown): LifecycleSummary | undefined {
  if (!response || typeof response !== "object") {
    return undefined;
  }
  const debug = (response as Record<string, unknown>).debug;
  if (!debug || typeof debug !== "object") {
    return undefined;
  }
  const summary = (debug as Record<string, unknown>).lifecycle_summary;
  if (!summary || typeof summary !== "object") {
    return undefined;
  }
  return summary as LifecycleSummary;
}

export function extractSelectionSummary(response: unknown): SelectionSummary | undefined {
  if (!response || typeof response !== "object") {
    return undefined;
  }
  const obj = response as Record<string, unknown>;
  const blameRows = Array.isArray(obj.blame_rows) ? obj.blame_rows : [];
  const documentLinks = Array.isArray(obj.document_links) ? obj.document_links : [];
  const first = blameRows[0] as Record<string, unknown> | undefined;
  const primaryHash =
    first && typeof first === "object" && !first.is_uncommitted
      ? (first.short_hash as string | undefined)
      : undefined;
  return {
    blameGroupCount: blameRows.length,
    primaryCommitShortHash: primaryHash,
    lineHistoryAvailable: obj.line_history_available !== false,
    lineHistoryCount: Array.isArray(obj.line_history) ? obj.line_history.length : undefined,
    documentLinkCount: documentLinks.length,
  };
}

export function toDisplayPath(
  filePath: string,
  workspaceRoots?: string[]
): string {
  const roots =
    workspaceRoots ??
    (() => {
      try {
        // Lazy require so Node unit tests do not need the vscode module.
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        const vscode = require("vscode") as typeof import("vscode");
        return (vscode.workspace.workspaceFolders ?? []).map((f) => f.uri.fsPath);
      } catch {
        return [] as string[];
      }
    })();
  for (const root of roots) {
    const rel = path.relative(root, filePath);
    if (rel && !rel.startsWith("..") && !path.isAbsolute(rel)) {
      return rel.replace(/\\/g, "/");
    }
  }
  return filePath.replace(/\\/g, "/");
}

function formatTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
