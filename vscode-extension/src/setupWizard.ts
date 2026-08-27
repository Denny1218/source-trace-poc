/**
 * Source Trace setup wizard commands:
 *
 *   sourceTrace.setup        — 서버 및 장비 설정 (full wizard: URL InputBox 포함)
 *   sourceTrace.changeDevice — 장비 변경 (저장된 서버 URL 유지, InputBox 없음)
 *   sourceTrace.checkServer  — 서버 연결 확인
 *   sourceTrace.viewSettings — 현재 설정 보기
 *
 * 저장 정책 (변경하지 않음):
 *   - sourceTrace.serverUrl → User/Global
 *   - sourceTrace.equipmentId → Workspace (없으면 Global fallback)
 */

import * as vscode from "vscode";
import {
  ApiUrls,
  normalizeServerUrl,
  resolveServerUrl,
  sanitizeUrl,
} from "./serverConfig";
import {
  changeDeviceSteps,
  resolveSettingsWritePlan,
  setupWizardSteps,
  type SettingsWriteTarget,
} from "./setupWizardPolicy";

// Re-export policy helpers so existing imports from setupWizard keep working.
export {
  changeDeviceSteps,
  resolveSettingsWritePlan,
  setupWizardSteps,
};
export type { SettingsWritePlan, SettingsWriteTarget, WizardStep } from "./setupWizardPolicy";

// ── Data types ────────────────────────────────────────────────────────────

export interface EquipmentSummary {
  id: number;
  name: string;
  documentPath?: string;
  repositoryCount?: number;
  hasDocuments?: boolean;
}

export interface ServerCheckResult {
  ok: boolean;
  serverUrl?: string;
  latencyMs?: number;
  detail?: string;
}

// ── Pure helpers (testable without VS Code) ───────────────────────────────

const CONNECT_TIMEOUT_MS = 8_000;
const LIST_TIMEOUT_MS = 10_000;

/** Fetches /api/health and returns {ok, latencyMs} */
export async function checkServerHealth(serverUrl: string): Promise<ServerCheckResult> {
  const url = ApiUrls.health(serverUrl);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), CONNECT_TIMEOUT_MS);
  const t0 = Date.now();
  try {
    const res = await fetch(url, { signal: controller.signal, headers: { Accept: "application/json" } });
    const latencyMs = Date.now() - t0;
    if (!res.ok) {
      return { ok: false, serverUrl, detail: `HTTP ${res.status}` };
    }
    // Verify it looks like Source Trace (health returns JSON)
    try {
      await res.json();
    } catch {
      return { ok: false, serverUrl, detail: "Source Trace 서버 응답이 아닙니다." };
    }
    return { ok: true, serverUrl, latencyMs };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    const lower = msg.toLowerCase();
    if (lower.includes("abort") || lower.includes("timeout")) {
      return { ok: false, serverUrl, detail: "연결 시간 초과" };
    }
    return { ok: false, serverUrl, detail: "연결 실패" };
  } finally {
    clearTimeout(timer);
  }
}

/** Fetches GET /api/equipment list */
export async function fetchEquipmentList(serverUrl: string): Promise<EquipmentSummary[]> {
  const url = ApiUrls.equipmentList(serverUrl);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LIST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      throw new Error(`장비 목록 조회 실패 (HTTP ${res.status})`);
    }
    const data = (await res.json()) as Array<Record<string, unknown>>;
    return data.map((e) => ({
      id: Number(e.id),
      name: String(e.name ?? ""),
      documentPath: typeof e.document_path === "string" ? e.document_path : undefined,
      hasDocuments: typeof e.document_path === "string" && e.document_path.trim().length > 0,
    }));
  } finally {
    clearTimeout(timer);
  }
}

/** Fetches GET /api/equipment/{id}/repositories and returns count */
export async function fetchRepositoryCount(serverUrl: string, equipmentId: number): Promise<number> {
  const url = ApiUrls.equipmentRepositories(serverUrl, equipmentId);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LIST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      return 0;
    }
    const data = (await res.json()) as unknown[];
    return Array.isArray(data) ? data.length : 0;
  } catch {
    return 0;
  } finally {
    clearTimeout(timer);
  }
}

/** Builds a Quick Pick label line and detail line for an equipment entry. */
export function equipmentQuickPickItem(
  e: EquipmentSummary
): { label: string; detail: string; description: string } {
  const parts: string[] = [`ID ${e.id}`];
  if (e.repositoryCount !== undefined) {
    parts.push(`Git 저장소 ${e.repositoryCount}개`);
  }
  if (e.hasDocuments === true) {
    parts.push("변경내역서 등록됨");
  } else if (e.hasDocuments === false) {
    parts.push("변경내역서 미등록");
  }
  return {
    label: e.name,
    detail: parts.join(" · "),
    description: `(ID ${e.id})`,
  };
}

// ── VS Code command implementations ──────────────────────────────────────

function getConfig() {
  return vscode.workspace.getConfiguration("sourceTrace");
}

function hasWorkspaceFolders(): boolean {
  return (
    vscode.workspace.workspaceFolders !== undefined &&
    vscode.workspace.workspaceFolders.length > 0
  );
}

function toConfigurationTarget(target: SettingsWriteTarget): vscode.ConfigurationTarget {
  return target === "Workspace"
    ? vscode.ConfigurationTarget.Workspace
    : vscode.ConfigurationTarget.Global;
}

/** Persist serverUrl to Global only. */
async function saveServerUrl(serverUrl: string): Promise<void> {
  const plan = resolveSettingsWritePlan(hasWorkspaceFolders());
  await getConfig().update(
    "serverUrl",
    serverUrl,
    toConfigurationTarget(plan.serverUrlTarget)
  );
}

/**
 * Persist equipmentId to Workspace (or Global when no workspace folder).
 * Does not touch serverUrl — other workspaces' equipmentId stay unchanged.
 */
async function saveEquipmentId(equipmentId: number): Promise<void> {
  const plan = resolveSettingsWritePlan(hasWorkspaceFolders());
  await getConfig().update(
    "equipmentId",
    equipmentId,
    toConfigurationTarget(plan.equipmentIdTarget)
  );
}

/**
 * Shared: health already OK → list equipment → QuickPick → return selection.
 * Does not show a server URL InputBox and does not write settings.
 */
async function pickEquipmentOnServer(
  serverUrl: string
): Promise<{ equipment: EquipmentSummary; withCounts: EquipmentSummary[] } | null> {
  let equipmentList: EquipmentSummary[];
  try {
    equipmentList = await fetchEquipmentList(serverUrl);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(
      `장비 목록 조회에 실패했습니다.\n` +
        `주소: ${serverUrl}\n` +
        `원인: ${msg.slice(0, 200)}`
    );
    return null;
  }

  if (equipmentList.length === 0) {
    vscode.window.showWarningMessage(
      "서버에 등록된 장비가 없습니다.\n" +
        "먼저 Source Trace 관리 화면에서 장비를 등록하세요."
    );
    return null;
  }

  const withCounts = await Promise.all(
    equipmentList.map(async (e) => {
      const repoCount = await fetchRepositoryCount(serverUrl, e.id);
      return { ...e, repositoryCount: repoCount };
    })
  );

  const items = withCounts.map((e) => ({
    ...equipmentQuickPickItem(e),
    _id: e.id,
    _name: e.name,
  }));

  const picked = await vscode.window.showQuickPick(items, {
    title: "Source Trace 장비 선택",
    placeHolder: "분석할 장비를 선택하세요",
    matchOnDetail: true,
    ignoreFocusOut: true,
  });
  if (!picked) {
    return null;
  }

  const equipment = withCounts.find((e) => e.id === picked._id) ?? {
    id: picked._id,
    name: picked._name,
  };
  return { equipment, withCounts };
}

function hostPortOf(serverUrl: string): string {
  const { url: displayUrl } = sanitizeUrl(serverUrl);
  try {
    const u = new URL(displayUrl);
    return u.hostname + (u.port ? `:${u.port}` : "");
  } catch {
    return displayUrl;
  }
}

function logSetupResult(
  outputChannel: vscode.OutputChannel | undefined,
  params: {
    title: string;
    serverUrl: string;
    health: ServerCheckResult;
    equipment: EquipmentSummary;
    withCounts: EquipmentSummary[];
  }
): void {
  if (!outputChannel) {
    return;
  }
  const { url: safeUrl } = sanitizeUrl(params.serverUrl);
  const ts = formatTime(new Date());
  outputChannel.appendLine("--------------------------------------------------");
  outputChannel.appendLine(`[${ts}] ${params.title}`);
  outputChannel.appendLine(
    `서버 연결: 성공${
      params.health.latencyMs !== undefined ? ` (${params.health.latencyMs}ms)` : ""
    }`
  );
  outputChannel.appendLine(`서버: ${safeUrl}`);
  outputChannel.appendLine(`선택 장비: ${params.equipment.name}`);
  outputChannel.appendLine(`장비 ID: ${params.equipment.id}`);
  const repos = params.withCounts.find((e) => e.id === params.equipment.id)?.repositoryCount;
  if (repos !== undefined) {
    outputChannel.appendLine(`Git 저장소: ${repos}개`);
  }
  const hasDoc = params.withCounts.find((e) => e.id === params.equipment.id)?.hasDocuments;
  outputChannel.appendLine(`변경내역서: ${hasDoc ? "등록됨" : "미등록"}`);
  outputChannel.appendLine("--------------------------------------------------");
}

/**
 * Core wizard: prompts for server URL, validates, lists equipment, lets user
 * pick one, then saves (serverUrl Global + equipmentId Workspace/Global).
 */
export async function runSetupWizard(
  outputChannel?: vscode.OutputChannel
): Promise<boolean> {
  const config = getConfig();
  const existingServerUrl = config.get<string>("serverUrl") ?? "";
  const legacyBackendUrl = config.get<string>("backendUrl") ?? "";

  // Step 1 — Server URL input (setup only)
  const currentServerUrl = resolveServerUrl(existingServerUrl, legacyBackendUrl)?.serverUrl ?? "";
  const rawInput = await vscode.window.showInputBox({
    title: "Source Trace 서버 주소",
    prompt: "Source Trace 서버의 주소와 포트를 입력하세요. 예: http://192.168.155.89:8010",
    value: currentServerUrl || "http://",
    ignoreFocusOut: true,
    validateInput: (v) => {
      const r = normalizeServerUrl(v);
      return r.ok ? null : r.error;
    },
  });
  if (!rawInput) {
    return false;
  }

  const normalResult = normalizeServerUrl(rawInput);
  if (!normalResult.ok) {
    vscode.window.showErrorMessage(normalResult.error);
    return false;
  }
  const serverUrl = normalResult.url;

  // Step 2 — Connection test
  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: "서버 연결 확인 중..." },
    async () => {
      // visual feedback only; actual check below
    }
  );

  const healthResult = await checkServerHealth(serverUrl);
  if (!healthResult.ok) {
    const msg =
      `Source Trace 서버에 연결할 수 없습니다.\n` +
      `주소: ${serverUrl}\n` +
      `원인: ${healthResult.detail ?? "연결 실패"}\n` +
      `서버 실행 상태와 IP·포트를 확인해 주세요.`;
    vscode.window.showErrorMessage(msg);
    return false;
  }

  // Steps 3–4 — equipment list + QuickPick (shared helper)
  const picked = await pickEquipmentOnServer(serverUrl);
  if (!picked) {
    return false;
  }

  // Step 5 — Save (serverUrl Global + equipmentId Workspace/Global)
  await saveServerUrl(serverUrl);
  await saveEquipmentId(picked.equipment.id);

  logSetupResult(outputChannel, {
    title: "Source Trace 설정",
    serverUrl,
    health: healthResult,
    equipment: picked.equipment,
    withCounts: picked.withCounts,
  });

  vscode.window.showInformationMessage(
    `Source Trace 설정 완료\n서버: ${hostPortOf(serverUrl)}\n장비: ${picked.equipment.name} (ID ${picked.equipment.id})`
  );

  return true;
}

/**
 * `sourceTrace.changeDevice` — keep saved server URL; re-pick equipment only.
 * Does NOT show a server URL InputBox and does NOT call runSetupWizard().
 */
export async function runChangeDevice(outputChannel?: vscode.OutputChannel): Promise<void> {
  const config = getConfig();
  const serverUrl = resolveServerUrl(
    config.get<string>("serverUrl"),
    config.get<string>("backendUrl")
  )?.serverUrl;

  if (!serverUrl) {
    const choice = await vscode.window.showErrorMessage(
      "서버 주소가 설정되지 않았습니다. 먼저 서버 및 장비 설정을 실행하세요.",
      "설정 시작",
      "취소"
    );
    if (choice === "설정 시작") {
      await runSetupWizard(outputChannel);
    }
    return;
  }

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: "서버 연결 확인 중..." },
    async () => {
      // visual feedback only
    }
  );

  const healthResult = await checkServerHealth(serverUrl);
  if (!healthResult.ok) {
    const msg =
      `Source Trace 서버에 연결할 수 없습니다.\n` +
      `주소: ${serverUrl}\n` +
      `원인: ${healthResult.detail ?? "연결 실패"}\n` +
      `서버 실행 상태와 IP·포트를 확인해 주세요.`;
    vscode.window.showErrorMessage(msg);
    return;
  }

  const picked = await pickEquipmentOnServer(serverUrl);
  if (!picked) {
    return;
  }

  // Only equipmentId — current Workspace (or Global fallback). Other workspaces untouched.
  await saveEquipmentId(picked.equipment.id);

  logSetupResult(outputChannel, {
    title: "Source Trace 장비 변경",
    serverUrl,
    health: healthResult,
    equipment: picked.equipment,
    withCounts: picked.withCounts,
  });

  vscode.window.showInformationMessage(
    `장비 변경 완료\n서버: ${hostPortOf(serverUrl)}\n장비: ${picked.equipment.name} (ID ${picked.equipment.id})`
  );
}

/** `sourceTrace.checkServer` — quick connectivity test */
export async function runCheckServer(outputChannel?: vscode.OutputChannel): Promise<void> {
  const config = getConfig();
  const serverUrl = resolveServerUrl(
    config.get<string>("serverUrl"),
    config.get<string>("backendUrl")
  )?.serverUrl;

  if (!serverUrl) {
    vscode.window.showWarningMessage(
      "서버 주소가 설정되지 않았습니다. `Source Trace: 서버 및 장비 설정`을 먼저 실행하세요."
    );
    return;
  }

  const result = await checkServerHealth(serverUrl);
  if (result.ok) {
    const msg = `서버 연결 성공: ${serverUrl}${result.latencyMs !== undefined ? ` (${result.latencyMs}ms)` : ""}`;
    vscode.window.showInformationMessage(msg);
    outputChannel?.appendLine(`[${formatTime(new Date())}] ${msg}`);
  } else {
    const msg =
      `Source Trace 서버에 연결할 수 없습니다.\n` +
      `주소: ${serverUrl}\n` +
      `원인: ${result.detail ?? "연결 실패"}\n` +
      `서버 실행 상태와 IP·포트를 확인해 주세요.`;
    vscode.window.showErrorMessage(msg);
    outputChannel?.appendLine(`[${formatTime(new Date())}] 서버 연결 실패: ${result.detail}`);
  }
}

/** `sourceTrace.viewSettings` — display current config in a message + output */
export async function runViewSettings(outputChannel?: vscode.OutputChannel): Promise<void> {
  const config = getConfig();
  const serverCfg = resolveServerUrl(
    config.get<string>("serverUrl"),
    config.get<string>("backendUrl")
  );
  const equipmentId = config.get<number | null>("equipmentId");

  if (!serverCfg) {
    vscode.window.showWarningMessage(
      "서버 주소가 설정되지 않았습니다. `Source Trace: 서버 및 장비 설정`을 실행하세요."
    );
    return;
  }

  const serverUrl = serverCfg.serverUrl;
  const legacyNote = serverCfg.migratedFromLegacy ? " (backendUrl에서 자동 인식)" : "";

  let equipmentName = "(알 수 없음)";
  let repoCount: number | undefined;
  let hasDocuments: boolean | undefined;

  if (equipmentId && equipmentId > 0) {
    try {
      const res = await fetch(ApiUrls.equipmentById(serverUrl, equipmentId), {
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const data = (await res.json()) as Record<string, unknown>;
        equipmentName = String(data.name ?? equipmentName);
        hasDocuments =
          typeof data.document_path === "string" &&
          (data.document_path as string).trim().length > 0;
      }
    } catch {
      /* ignore — offline */
    }
    try {
      repoCount = await fetchRepositoryCount(serverUrl, equipmentId);
    } catch {
      /* ignore */
    }
  }

  const lines = [
    `서버: ${serverUrl}${legacyNote}`,
    `장비명: ${equipmentName}`,
    `장비 ID: ${equipmentId ?? "(미설정)"}`,
    repoCount !== undefined ? `Git 저장소: ${repoCount}개` : null,
    hasDocuments !== undefined ? `변경내역서: ${hasDocuments ? "등록됨" : "미등록"}` : null,
  ].filter(Boolean) as string[];

  const msgBody = lines.join("\n");
  vscode.window.showInformationMessage(`Source Trace 현재 설정\n${msgBody}`);

  if (outputChannel) {
    const ts = formatTime(new Date());
    outputChannel.appendLine(`[${ts}] 현재 설정:`);
    lines.forEach((l) => outputChannel.appendLine(`  ${l}`));
  }
}

// ── Utility ───────────────────────────────────────────────────────────────

function formatTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}
