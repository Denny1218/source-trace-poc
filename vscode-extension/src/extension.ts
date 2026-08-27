import * as vscode from "vscode";
import { resolveEditorContext } from "./editorContext";
import { resolveEquipmentId, verifyEquipment, verifyErrorMessage } from "./equipmentVerifier";
import {
  extractLifecycleSummary,
  extractSelectionSummary,
  ProgressLogger,
  toDisplayPath,
} from "./progressLog";
import {
  buildAnalyzeRequest,
  buildResultDocumentText,
  buildSelectionRequest,
  type ExtensionDebugInfo,
} from "./requestBuilder";
import {
  resolveRepoRelativePathForFile,
  RepoPathResolveError,
} from "./repoPathResolver";
import { ApiUrls, resolveServerUrl, sanitizeUrl } from "./serverConfig";
import { getRecentSelectionFallback, registerSelectionTracker } from "./selectionTracker";
import { findEnclosingFunctionSymbol } from "./symbolExtractor";
import {
  runChangeDevice,
  runCheckServer,
  runSetupWizard,
  runViewSettings,
} from "./setupWizard";

const DEFAULT_QUERY = "선택한 코드가 왜 변경됐는지 알려줘";
const REQUEST_TIMEOUT_MS = 180_000;
const C_WORD_PATTERN = /[A-Za-z_][A-Za-z0-9_]*/;

const outputChannel = vscode.window.createOutputChannel("Source Trace");

export function activate(context: vscode.ExtensionContext): void {
  registerSelectionTracker(context);

  context.subscriptions.push(
    // PROJECT_SPEC v2.4 §4 — 함수 전체 이력 조회와 선택 코드 변경 근거 조회는
    // 별도 명령·API·서비스로 분리한다. `sourceTrace.analyzeSelection`은 이전
    // 버전 호환용으로만 등록하며 contributes.commands / menus 에는 노출하지 않는다.
    vscode.commands.registerCommand("sourceTrace.analyzeFunctionHistory", analyzeFunctionHistory),
    vscode.commands.registerCommand("sourceTrace.analyzeSelection", analyzeFunctionHistory),
    vscode.commands.registerCommand("sourceTrace.analyzeSelectedCode", analyzeSelectedCode),
    vscode.commands.registerCommand("sourceTrace.setup", () => runSetupWizard(outputChannel)),
    vscode.commands.registerCommand("sourceTrace.changeDevice", () => runChangeDevice(outputChannel)),
    vscode.commands.registerCommand("sourceTrace.checkServer", () => runCheckServer(outputChannel)),
    vscode.commands.registerCommand("sourceTrace.viewSettings", () => runViewSettings(outputChannel)),
    outputChannel
  );
}

export function deactivate(): void {
  // No background timers/state to tear down.
}

/** `Source Trace: 함수 변경 이력 조회` — 함수/Symbol 전체 Git·공식 문서 이력. */
async function analyzeFunctionHistory(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("분석할 소스 파일을 먼저 열어주세요.");
    return;
  }

  // ── 1. Capture editor state BEFORE any await (context menu / InputBox can clear selection) ──
  const document = editor.document;
  const filePath = document.fileName;
  const selection = editor.selection;
  const immediateSelectionText = document.getText(selection);
  const position = editor.selection.active;
  const currentLineText = document.lineAt(position.line).text;
  const cursorRange = document.getWordRangeAtPosition(position, C_WORD_PATTERN);
  const cursorWord = cursorRange ? document.getText(cursorRange) : undefined;
  const recentSelectionText = getRecentSelectionFallback(document.uri.toString());

  const resolved = resolveEditorContext({
    immediateSelectionText,
    recentSelectionText,
    cursorWord,
    currentLineText,
  });

  if (!resolved) {
    vscode.window.showWarningMessage("분석할 함수명 위에 커서를 두거나 코드 일부를 선택해주세요.");
    return;
  }

  const config = vscode.workspace.getConfiguration("sourceTrace");
  const rawEquipmentId = config.get<number>("equipmentId");
  const useOllama = config.get<boolean>("useOllama", false);
  const maxSelectedCodeChars = config.get<number>("maxSelectedCodeChars", 4000);
  const showDebug = config.get<boolean>("showDebug", false);
  const diagnosticLogging = config.get<boolean>("diagnosticLogging", false);
  const serverCfg = resolveServerUrl(
    config.get<string>("serverUrl"),
    config.get<string>("backendUrl")
  );
  if (!serverCfg) {
    const choice = await vscode.window.showErrorMessage(
      "Source Trace 서버 또는 장비가 설정되지 않았습니다.",
      "설정 시작",
      "취소"
    );
    if (choice === "설정 시작") {
      await runSetupWizard(outputChannel);
    }
    return;
  }

  const { serverUrl } = serverCfg;
  const analyzeUrl = ApiUrls.analyzeTrace(serverUrl);
  const equipmentId = resolveEquipmentId(rawEquipmentId);
  if (equipmentId === null) {
    const choice = await vscode.window.showErrorMessage(
      "Source Trace 장비가 설정되지 않았습니다.",
      "설정 시작",
      "취소"
    );
    if (choice === "설정 시작") {
      await runSetupWizard(outputChannel);
    }
    return;
  }

  const query = await vscode.window.showInputBox({
    title: "장비 변경 이력 조회",
    prompt: "선택한 코드에 대해 무엇을 알고 싶은가요?",
    value: DEFAULT_QUERY,
    ignoreFocusOut: true,
  });
  if (query === undefined) {
    return;
  }

  const userQuery = query.trim() || DEFAULT_QUERY;
  const progress = new ProgressLogger(outputChannel);

  progress.step("verify", "장비 확인 중");
  const verifyResult = await verifyEquipment(serverUrl, equipmentId);
  if (!verifyResult.ok) {
    const msg = verifyErrorMessage(verifyResult);
    progress.fail("장비 확인", msg.split("\n")[0]);
    vscode.window.showErrorMessage(msg);
    return;
  }

  // Prefer repo-relative path (same as selection) so Backend display paths match.
  let filePathForRequest = filePath;
  try {
    const pathInfo = await resolveRepoRelativePathForFile(filePath);
    filePathForRequest = pathInfo.repoRelativePath;
    if (diagnosticLogging) {
      progress.diagnostic([
        `repo_relative_path=${pathInfo.repoRelativePath}`,
        `git_root=${pathInfo.gitRoot}`,
      ]);
    }
  } catch {
    // Soft fallback: absolute / workspace path — Backend normalize still runs.
  }

  const equipment = verifyResult.equipment!;
  const { url: safeServerUrl } = sanitizeUrl(serverUrl);
  const requestKind = resolved.detectedSymbol ? "함수 변경 이력 조회" : "코드 변경 이력 조회";
  progress.begin({
    requestKind,
    userQuestion: userQuery,
    symbol: resolved.detectedSymbol,
    file: filePathForRequest,
    equipment: {
      id: equipment.id,
      name: equipment.name,
      serverUrl: safeServerUrl,
    },
  });
  progress.step("prepare", "요청 준비 완료");

  const { body, truncated, debug } = buildAnalyzeRequest({
    equipmentId,
    query: userQuery,
    filePath: filePathForRequest,
    selectedCode: resolved.selectedText,
    detectedSymbol: resolved.detectedSymbol,
    sourceMode: resolved.sourceMode,
    useOllama,
    maxSelectedCodeChars,
  });

  if (diagnosticLogging) {
    progress.diagnostic([
      `selection_mode=${debug.source_mode}`,
      `symbol=${debug.detected_symbol ?? "(none)"}`,
      `file_abs=${filePath}`,
      `file_display=${toDisplayPath(filePath)}`,
      `selected_code_sent_chars=${debug.selected_code_sent_chars}`,
      `recent_fallback=${resolved.sourceMode === "recent_selection_fallback"}`,
    ]);
  }

  if (truncated) {
    vscode.window.showInformationMessage(
      `선택한 코드가 ${maxSelectedCodeChars}자를 초과해 앞부분만 전송됩니다 (전체 파일 전송 방지).`
    );
  }

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: useOllama
        ? "장비 변경 이력 조회 중... (AI 보조 설명 생성 포함, 다소 지연될 수 있습니다)"
        : "장비 변경 이력 조회 중...",
      cancellable: false,
    },
    async () => {
      try {
        progress.step("send", "서버 요청 전송");
        progress.step("wait", "분석 중");
        const response = await postAnalyze(analyzeUrl, body);
        progress.step("receive", "분석 결과 수신");
        progress.stats(extractLifecycleSummary(response), readOverallConfidence(response));
        progress.step("document", "결과 문서 생성");
        await showResultDocument(response, {
          detectedSymbol: resolved.detectedSymbol,
          filePath,
          debug,
          showDebug,
        });
        progress.step("open", "결과 탭 열기");
        progress.complete();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        const stage = message.toLowerCase().includes("abort")
          ? "백엔드 응답 대기"
          : "백엔드 분석 요청";
        progress.fail(stage, userFacingErrorMessage(err, useOllama));
        handleError(err, useOllama);
      }
    }
  );
}

/**
 * `Source Trace: 선택 코드 변경 근거 조회` — 실제 선택한 한 줄·코드 블록의
 * git blame/line history 근거만 조회한다 (PROJECT_SPEC v2.4 §4~§8).
 * 함수 전체 이력 조회와 명령·API·서비스가 완전히 분리되어 있으며, 선택이
 * 없으면 실행하지 않고 코드 선택을 안내한다.
 */
async function analyzeSelectedCode(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("분석할 소스 파일을 먼저 열어주세요.");
    return;
  }

  const document = editor.document;
  const selection = editor.selection;
  const selectedText = document.getText(selection);
  if (!selectedText || !selectedText.trim()) {
    vscode.window.showWarningMessage(
      "변경 근거를 조회할 코드를 먼저 선택해 주세요 (한 줄 또는 여러 줄 블록)."
    );
    return;
  }

  const filePath = document.fileName;
  const startLine = selection.start.line + 1;
  const endLine = selection.end.line + 1;
  const documentLines = document.getText().split(/\r?\n/);
  const enclosingSymbol = findEnclosingFunctionSymbol(documentLines, selection.start.line);

  const config = vscode.workspace.getConfiguration("sourceTrace");
  const rawEquipmentId = config.get<number>("equipmentId");
  const maxSelectedCodeChars = config.get<number>("maxSelectedCodeChars", 4000);
  const diagnosticLogging = config.get<boolean>("diagnosticLogging", false);
  const serverCfg = resolveServerUrl(
    config.get<string>("serverUrl"),
    config.get<string>("backendUrl")
  );
  if (!serverCfg) {
    const choice = await vscode.window.showErrorMessage(
      "Source Trace 서버 또는 장비가 설정되지 않았습니다.",
      "설정 시작",
      "취소"
    );
    if (choice === "설정 시작") {
      await runSetupWizard(outputChannel);
    }
    return;
  }

  const { serverUrl } = serverCfg;
  const selectionUrl = ApiUrls.analyzeSelection(serverUrl);
  const equipmentId = resolveEquipmentId(rawEquipmentId);
  if (equipmentId === null) {
    const choice = await vscode.window.showErrorMessage(
      "Source Trace 장비가 설정되지 않았습니다.",
      "설정 시작",
      "취소"
    );
    if (choice === "설정 시작") {
      await runSetupWizard(outputChannel);
    }
    return;
  }

  const progress = new ProgressLogger(outputChannel);

  progress.step("verify", "장비 확인 중");
  const verifyResult = await verifyEquipment(serverUrl, equipmentId);
  if (!verifyResult.ok) {
    const msg = verifyErrorMessage(verifyResult);
    progress.fail("장비 확인", msg.split("\n")[0]);
    vscode.window.showErrorMessage(msg);
    return;
  }

  const equipment = verifyResult.equipment!;
  const { url: safeServerUrl } = sanitizeUrl(serverUrl);
  progress.begin({
    requestKind: "선택 코드 변경 근거",
    symbol: enclosingSymbol,
    file: filePath,
    equipment: {
      id: equipment.id,
      name: equipment.name,
      serverUrl: safeServerUrl,
    },
  });
  progress.step(
    "range",
    `범위: ${startLine === endLine ? `${startLine}행` : `${startLine}-${endLine}행`}`
  );

  // PROJECT_SPEC v2.6 — do not gate on Extension remote URL/name matching.
  // Send repo-relative path; Backend common resolver decides the Repo.
  let repoIdHint: number | undefined;
  let repoRelativePath: string | undefined;
  try {
    const pathInfo = await resolveRepoRelativePathForFile(filePath);
    repoRelativePath = pathInfo.repoRelativePath;
    if (diagnosticLogging) {
      progress.diagnostic([
        `repo_relative_path=${pathInfo.repoRelativePath}`,
        `git_root=${pathInfo.gitRoot}`,
        `remote_url=${pathInfo.remoteUrl ?? "(none)"}`,
      ]);
    }
  } catch (err) {
    const msg =
      err instanceof RepoPathResolveError
        ? err.message
        : err instanceof Error
          ? err.message
          : String(err);
    progress.fail("요청 준비", msg.split("\n")[0], [
      "현재 파일이 Git Repository 안에 있는지 확인하세요.",
    ]);
    vscode.window.showErrorMessage(msg);
    return;
  }

  const { body, truncated, debug } = buildSelectionRequest({
    equipmentId,
    filePath,
    repoId: repoIdHint,
    repoRelativePath,
    startLine,
    endLine,
    selectedCode: selectedText,
    enclosingSymbol,
    maxSelectedCodeChars,
  });

  if (diagnosticLogging) {
    progress.diagnostic([
      `range=${debug.start_line}-${debug.end_line}`,
      `symbol=${debug.enclosing_symbol ?? "(none)"}`,
      `file_abs=${filePath}`,
      `file_display=${toDisplayPath(filePath)}`,
      `repo_id_hint=${debug.repo_id ?? "(none)"}`,
      `repo_relative_path=${debug.repo_relative_path ?? "(none)"}`,
      `selected_code_sent_chars=${debug.selected_code_sent_chars}`,
    ]);
  }

  if (truncated) {
    vscode.window.showInformationMessage(
      `선택한 코드가 ${maxSelectedCodeChars}자를 초과해 앞부분만 전송됩니다.`
    );
  }

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "선택 코드 변경 근거 조회 중... (git blame/line history)",
      cancellable: false,
    },
    async () => {
      try {
        progress.step("send", "서버 요청 전송");
        progress.step("repo", "Repository 확인");
        progress.step("blame", "Git blame 조회");
        const response = await postAnalyze(selectionUrl, body);
        progress.step("history", "변경 Diff 확인");
        progress.selectionStats(extractSelectionSummary(response));
        progress.step("document", "결과 문서 생성");
        await showResultDocument(response, {
          detectedSymbol: enclosingSymbol,
          filePath,
          debug: undefined,
          showDebug: false,
        });
        progress.step("open", "결과 탭 열기");
        progress.complete();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        const lower = message.toLowerCase();
        let stage = "백엔드 분석 요청";
        let hints: string[] | undefined;
        if (lower.includes("abort")) {
          stage = "백엔드 응답 대기";
        } else if (
          message.includes("여러 장비 Repository") ||
          message.includes("AMBIGUOUS") ||
          message.includes("하나를 결정할 수 없")
        ) {
          stage = "Repository 확인";
          hints = [
            "동일 상대경로가 여러 Repo에 있습니다. 장비 Repo 등록을 확인하세요.",
          ];
        } else if (
          message.includes("Repository") ||
          message.includes("repo_relative") ||
          message.includes("Git Repository")
        ) {
          stage = "Repository 확인";
        }
        progress.fail(stage, userFacingErrorMessage(err, false), hints);
        handleError(err, false);
      }
    }
  );
}

async function postAnalyze(url: string, body: unknown): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const text = await res.text();
    if (!res.ok) {
      throw new Error(`Backend 응답 오류 (HTTP ${res.status}): ${text.slice(0, 300)}`);
    }
    try {
      return JSON.parse(text) as Record<string, unknown>;
    } catch {
      return { content: text };
    }
  } finally {
    clearTimeout(timer);
  }
}

async function showResultDocument(
  response: Record<string, unknown>,
  meta: {
    detectedSymbol?: string;
    filePath: string;
    debug?: ExtensionDebugInfo;
    showDebug: boolean;
  }
): Promise<void> {
  const text = buildResultDocumentText({
    response,
    detectedSymbol: meta.detectedSymbol,
    filePath: meta.filePath,
    debug: meta.debug,
    showDebug: meta.showDebug === true,
    queriedAt: new Date(),
  });

  // New Untitled each query — no auto Preview, no auto-save (user chooses Save As).
  const doc = await vscode.workspace.openTextDocument({
    content: text,
    language: "markdown",
  });
  await vscode.window.showTextDocument(doc, {
    preview: false,
    viewColumn: vscode.ViewColumn.Beside,
  });
}

function handleError(err: unknown, useOllama: boolean): void {
  vscode.window.showErrorMessage(userFacingErrorMessage(err, useOllama));
}

function userFacingErrorMessage(err: unknown, useOllama: boolean): string {
  const message = err instanceof Error ? err.message : String(err);
  const lower = message.toLowerCase();
  if (lower.includes("abort")) {
    const hint = useOllama ? " sourceTrace.useOllama 설정을 false로 낮춰보세요." : "";
    return `서버 응답 시간이 초과되었습니다.${hint}`;
  }
  if (
    lower.includes("econnrefused") ||
    lower.includes("enotfound") ||
    lower.includes("fetch failed") ||
    lower.includes("network")
  ) {
    return "Backend 서버에 연결할 수 없습니다. sourceTrace.serverUrl 설정을 확인하거나 `Source Trace: 서버 연결 확인`을 실행하세요.";
  }
  return `오류가 발생했습니다: ${message}`;
}

function readOverallConfidence(response: Record<string, unknown>): string | undefined {
  const confidence = response.confidence;
  return typeof confidence === "string" ? confidence : undefined;
}
