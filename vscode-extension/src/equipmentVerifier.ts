/**
 * Verifies that the configured equipmentId exists on the server before analysis.
 *
 * Uses the existing GET /api/equipment/:id endpoint (no new API needed).
 * Returns structured result so the caller can decide whether to proceed.
 */

export interface EquipmentInfo {
  id: number;
  name: string;
  documentPath: string;
  repositoryCount?: number;
}

export type EquipmentVerifyResult =
  | { ok: true; equipment: EquipmentInfo }
  | { ok: false; reason: "not_configured" }
  | { ok: false; reason: "invalid_id"; id: unknown }
  | { ok: false; reason: "not_found"; id: number }
  | { ok: false; reason: "server_error"; id: number; statusCode?: number; detail?: string }
  | { ok: false; reason: "connection_error"; id: number; detail?: string };

const VERIFY_TIMEOUT_MS = 10_000;

/**
 * Resolves the configured equipment ID from settings.
 * Returns null if unset, 0, or non-positive.
 */
export function resolveEquipmentId(raw: number | null | undefined): number | null {
  if (raw === null || raw === undefined) {
    return null;
  }
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) {
    return null;
  }
  return Math.floor(n);
}

/**
 * Calls GET <backendBase>/api/equipment/:id and maps the result.
 *
 * backendBase is derived from the configured backendUrl
 * (strip any API path suffix, keep the origin).
 */
export async function verifyEquipment(
  backendUrl: string,
  equipmentId: number
): Promise<EquipmentVerifyResult> {
  const base = resolveBackendBase(backendUrl);
  const url = `${base}/api/equipment/${equipmentId}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), VERIFY_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (res.status === 404) {
      return { ok: false, reason: "not_found", id: equipmentId };
    }
    if (!res.ok) {
      let detail: string | undefined;
      try {
        const body = await res.json() as Record<string, unknown>;
        detail = typeof body?.detail === "string" ? body.detail : String(res.status);
      } catch {
        detail = String(res.status);
      }
      return {
        ok: false,
        reason: "server_error",
        id: equipmentId,
        statusCode: res.status,
        detail,
      };
    }
    const data = (await res.json()) as Record<string, unknown>;
    const equipment: EquipmentInfo = {
      id: Number(data.id ?? equipmentId),
      name: String(data.name ?? ""),
      documentPath: String(data.document_path ?? ""),
    };
    return { ok: true, equipment };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    const lower = msg.toLowerCase();
    if (lower.includes("abort") || lower.includes("timeout")) {
      return {
        ok: false,
        reason: "connection_error",
        id: equipmentId,
        detail: "서버 응답 시간 초과",
      };
    }
    if (
      lower.includes("econnrefused") ||
      lower.includes("enotfound") ||
      lower.includes("fetch failed") ||
      lower.includes("network")
    ) {
      return {
        ok: false,
        reason: "connection_error",
        id: equipmentId,
        detail: "서버에 연결할 수 없습니다",
      };
    }
    return {
      ok: false,
      reason: "connection_error",
      id: equipmentId,
      detail: msg.slice(0, 200),
    };
  } finally {
    clearTimeout(timer);
  }
}

export function verifyErrorMessage(result: EquipmentVerifyResult & { ok: false }): string {
  switch (result.reason) {
    case "not_configured":
      return (
        "Source Trace 장비가 선택되지 않았습니다.\n" +
        "VS Code 설정에서 sourceTrace.equipmentId를 입력해 주세요."
      );
    case "invalid_id":
      return (
        "sourceTrace.equipmentId 값이 올바르지 않습니다.\n" +
        "관리 화면에서 확인한 정수 ID를 입력해 주세요."
      );
    case "not_found":
      return (
        `장비 ID ${result.id}를 서버에서 찾을 수 없습니다.\n` +
        "현재 서버와 장비 ID 설정을 확인해 주세요."
      );
    case "server_error":
      return (
        `서버 응답 오류 (HTTP ${result.statusCode ?? "?"}) — 장비 ID ${result.id}.\n` +
        "서버 로그를 확인해 주세요."
      );
    case "connection_error":
      return (
        `서버에 연결할 수 없습니다. sourceTrace.backendUrl 설정을 확인해 주세요.\n` +
        (result.detail ? `원인: ${result.detail}` : "")
      );
  }
}

/** Derives the backend base URL from the full legacy backendUrl. */
export function resolveBackendBase(backendUrl: string): string {
  try {
    const u = new URL(backendUrl);
    return u.origin;
  } catch {
    const idx = backendUrl.indexOf("/api/");
    if (idx >= 0) {
      return backendUrl.slice(0, idx);
    }
    return backendUrl;
  }
}
