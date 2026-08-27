/**
 * Server URL normalization and API endpoint helpers.
 *
 * Introduces `sourceTrace.serverUrl` (e.g. "http://192.168.155.89:8010").
 * Provides backward-compat migration from legacy `sourceTrace.backendUrl`
 * (a full Backend API URL saved by older Extension versions).
 *
 * All API paths are composed here — callers must never hard-code them.
 */

export interface ServerConfig {
  /** Normalized server origin, e.g. "http://192.168.155.89:8010" — no trailing slash */
  serverUrl: string;
  /** True when serverUrl was derived from the legacy backendUrl setting */
  migratedFromLegacy?: boolean;
}

// ── URL normalisation ──────────────────────────────────────────────────────

/**
 * Strips credentials (user:password@) from a URL string before any use.
 * Returns the sanitized string and a flag if credentials were present.
 */
export function sanitizeUrl(raw: string): { url: string; hadCredentials: boolean } {
  try {
    const u = new URL(raw);
    const hadCredentials = !!(u.username || u.password);
    u.username = "";
    u.password = "";
    return { url: u.toString().replace(/\/$/, ""), hadCredentials };
  } catch {
    return { url: raw.replace(/\/$/, ""), hadCredentials: false };
  }
}

/**
 * Validates and normalizes a server URL string typed by the user.
 *
 * Accepts:
 *   - "192.168.1.1:8010"          → prefixes "http://"
 *   - "http://server:8010/"       → strips trailing slash
 *   - "http://server:8010/api/..."→ strips any path
 *   - "https://server"            → kept as-is
 *
 * Returns { ok: true, url } or { ok: false, error }.
 */
export function normalizeServerUrl(
  input: string
): { ok: true; url: string } | { ok: false; error: string } {
  let s = input.trim();
  if (!s) {
    return { ok: false, error: "서버 주소를 입력해 주세요." };
  }

  // Strip credentials immediately
  const { url: sanitized, hadCredentials } = sanitizeUrl(s);
  if (hadCredentials) {
    return {
      ok: false,
      error:
        "서버 주소에 사용자명/비밀번호를 포함하지 마세요. 인증이 필요한 경우 관리자에게 문의하세요.",
    };
  }
  s = sanitized;

  // Auto-prefix scheme if missing
  if (!/^https?:\/\//i.test(s)) {
    s = "http://" + s;
  }

  let u: URL;
  try {
    u = new URL(s);
  } catch {
    return { ok: false, error: `올바르지 않은 URL 형식입니다: "${input}"` };
  }

  if (!u.hostname) {
    return { ok: false, error: `호스트명을 확인해 주세요: "${input}"` };
  }

  // Keep only origin (scheme + host + port), discard any path the user typed
  const origin = u.origin; // e.g. "http://192.168.155.89:8010"
  return { ok: true, url: origin };
}

/**
 * Extracts the server origin from a legacy backendUrl like
 * "http://server:8010/api/trace/report".
 * Returns null if extraction fails.
 */
export function extractOriginFromBackendUrl(backendUrl: string): string | null {
  try {
    const u = new URL(backendUrl);
    return u.origin;
  } catch {
    // e.g. relative path stored — try stripping at first /api/
    const idx = backendUrl.indexOf("/api/");
    if (idx > 0) {
      return backendUrl.slice(0, idx);
    }
    return null;
  }
}

// ── API endpoint builders ──────────────────────────────────────────────────

/** All API paths defined in one place. */
const PATHS = {
  health: "/api/health",
  equipmentList: "/api/equipment",
  equipmentById: (id: number) => `/api/equipment/${id}`,
  traceReport: "/api/trace/report",
  // PROJECT_SPEC v2.4 §5 — 함수 전체 이력 조회(traceReport)와 분리된 선택
  // 코드 변경 근거 조회 전용 엔드포인트.
  traceSelection: "/api/trace/selection",
  equipmentRepositories: (id: number) => `/api/equipment/${id}/repositories`,
} as const;

export function buildApiUrl(serverUrl: string, path: string): string {
  // Use URL constructor to avoid double-slash issues
  const base = serverUrl.replace(/\/$/, "");
  return base + path;
}

export const ApiUrls = {
  health: (serverUrl: string) => buildApiUrl(serverUrl, PATHS.health),
  equipmentList: (serverUrl: string) => buildApiUrl(serverUrl, PATHS.equipmentList),
  equipmentById: (serverUrl: string, id: number) =>
    buildApiUrl(serverUrl, PATHS.equipmentById(id)),
  analyzeTrace: (serverUrl: string) => buildApiUrl(serverUrl, PATHS.traceReport),
  analyzeSelection: (serverUrl: string) => buildApiUrl(serverUrl, PATHS.traceSelection),
  equipmentRepositories: (serverUrl: string, id: number) =>
    buildApiUrl(serverUrl, PATHS.equipmentRepositories(id)),
};

// ── Settings resolution ────────────────────────────────────────────────────

/**
 * Reads serverUrl from settings, falling back to backendUrl migration.
 *
 * Priority:
 *  1. sourceTrace.serverUrl  (new)
 *  2. sourceTrace.backendUrl → extract origin  (legacy compat)
 *  3. null
 */
export function resolveServerUrl(
  serverUrlSetting: string | null | undefined,
  backendUrlSetting: string | null | undefined
): ServerConfig | null {
  // 1. New setting
  if (serverUrlSetting && serverUrlSetting.trim()) {
    const result = normalizeServerUrl(serverUrlSetting.trim());
    if (result.ok) {
      return { serverUrl: result.url };
    }
    // Invalid but present — return null so caller can show error
    return null;
  }

  // 2. Legacy backendUrl migration
  if (backendUrlSetting && backendUrlSetting.trim()) {
    const origin = extractOriginFromBackendUrl(backendUrlSetting.trim());
    if (origin) {
      return { serverUrl: origin, migratedFromLegacy: true };
    }
  }

  return null;
}
