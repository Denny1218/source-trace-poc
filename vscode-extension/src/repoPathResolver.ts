/**
 * PROJECT_SPEC v2.5.1 — map the active editor file to equipment repo_id +
 * repo_relative_path so Backend can resolve against its own clone root.
 *
 * Absolute Remote-SSH / Workspace paths must never be the primary identity key.
 */

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";

import { ApiUrls } from "./serverConfig";

const execFileAsync = promisify(execFile);
const GIT_TIMEOUT_MS = 8000;
const LIST_TIMEOUT_MS = 10000;

export interface EquipmentRepoInfo {
  id: number;
  name: string;
  source_type?: string;
  repository_url?: string | null;
  canonical_repository_url?: string | null;
  local_path?: string;
  status?: string;
}

export interface RepoPathResolution {
  repoId: number;
  repoRelativePath: string;
  gitRoot: string;
  matchMethod: string;
  remoteUrl?: string;
}

export class RepoPathResolveError extends Error {
  constructor(
    message: string,
    public readonly hintLines: string[] = []
  ) {
    super(message);
    this.name = "RepoPathResolveError";
  }
}

/** Session cache: reuse repo_id after a successful function-history or selection match. */
const lastResolvedByKey = new Map<string, { repoId: number; method: string }>();

function cacheKey(serverUrl: string, equipmentId: number, gitRoot: string): string {
  return `${serverUrl.trim()}|${equipmentId}|${posix(gitRoot).toLowerCase()}`;
}

export function rememberResolvedRepo(params: {
  serverUrl: string;
  equipmentId: number;
  gitRoot: string;
  repoId: number;
  method?: string;
}): void {
  lastResolvedByKey.set(cacheKey(params.serverUrl, params.equipmentId, params.gitRoot), {
    repoId: params.repoId,
    method: params.method || "cached",
  });
}

export function clearResolvedRepoCache(): void {
  lastResolvedByKey.clear();
}

function posix(p: string): string {
  return (p || "").replace(/\\/g, "/");
}

/**
 * Canonical identity for remote URL matching.
 * Absorbs SCP-style SSH, ssh://, http(s), trailing .git, credentials, and case.
 *
 * Examples that must equal:
 *   git@host:path/repo.git
 *   ssh://git@host/path/repo.git
 *   https://host/path/repo
 *   https://host/path/repo.git
 */
export function canonicalizeRemoteUrl(url: string): string {
  let u = (url || "").trim();
  if (!u) {
    return "";
  }

  // SCP-style: git@host:path/to/repo.git
  const scp = /^([^@/\s]+)@([^:/\s]+):(.+)$/.exec(u);
  if (scp && !u.includes("://")) {
    const host = scp[2];
    let repoPath = scp[3].replace(/^\/+/, "");
    if (repoPath.toLowerCase().endsWith(".git")) {
      repoPath = repoPath.slice(0, -4);
    }
    return `${host.toLowerCase()}/${repoPath.replace(/\/+$/, "").toLowerCase()}`;
  }

  // ssh://user@host[:port]/path
  let normalized = u;
  if (/^ssh:\/\//i.test(normalized)) {
    normalized = normalized.replace(/^ssh:\/\//i, "https://");
  }

  try {
    // Force a parseable absolute URL when scheme is missing after rewrite.
    const parsed = new URL(normalized);
    let host = parsed.hostname.toLowerCase();
    if (parsed.port) {
      host = `${host}:${parsed.port}`;
    }
    let p = decodeURIComponent(parsed.pathname || "").replace(/^\/+/, "");
    if (p.toLowerCase().endsWith(".git")) {
      p = p.slice(0, -4);
    }
    p = p.replace(/\/+$/, "").toLowerCase();
    return p ? `${host}/${p}` : host;
  } catch {
    // Fall back: strip credentials / .git / trailing slash
    let fallback = u.toLowerCase();
    fallback = fallback.replace(/^[a-z][a-z0-9+.-]*:\/\//, "");
    fallback = fallback.replace(/^[^/@]+@/, "");
    if (fallback.endsWith(".git")) {
      fallback = fallback.slice(0, -4);
    }
    return fallback.replace(/\/+$/, "");
  }
}

/** @deprecated use canonicalizeRemoteUrl — kept for callers/tests */
export function normalizeUrl(url: string): string {
  return canonicalizeRemoteUrl(url);
}

function basenamePosix(p: string): string {
  const parts = posix(p).split("/").filter(Boolean);
  return parts.length ? parts[parts.length - 1] : "";
}

async function runGit(
  args: string[],
  cwd: string
): Promise<{ stdout: string; ok: boolean }> {
  try {
    const { stdout } = await execFileAsync("git", args, {
      cwd,
      timeout: GIT_TIMEOUT_MS,
      windowsHide: true,
      encoding: "utf8",
    });
    return { stdout: String(stdout || "").trim(), ok: true };
  } catch {
    return { stdout: "", ok: false };
  }
}

/** Resolve git work tree root for a file (VS Code absolute path). */
export async function resolveGitRoot(filePath: string): Promise<string | null> {
  const dir = path.dirname(filePath);
  const { stdout, ok } = await runGit(["rev-parse", "--show-toplevel"], dir);
  if (!ok || !stdout) {
    return null;
  }
  return posix(stdout);
}

export async function resolveGitRemoteUrl(gitRoot: string): Promise<string | null> {
  const { stdout, ok } = await runGit(["remote", "get-url", "origin"], gitRoot);
  if (!ok || !stdout) {
    return null;
  }
  return stdout.trim();
}

/** Compute repo-relative path from git root + absolute file path. */
export function toRepoRelativePath(gitRoot: string, filePath: string): string {
  const root = posix(gitRoot).replace(/\/+$/, "");
  const file = posix(filePath);
  const rootCmp = process.platform === "win32" ? root.toLowerCase() : root;
  const fileCmp = process.platform === "win32" ? file.toLowerCase() : file;
  if (fileCmp === rootCmp) {
    throw new RepoPathResolveError("파일 경로가 Repository 루트입니다.");
  }
  if (!fileCmp.startsWith(rootCmp + "/")) {
    throw new RepoPathResolveError(
      "선택한 파일이 Git Repository 루트 밖에 있습니다."
    );
  }
  const rel = file.slice(root.length).replace(/^\/+/, "");
  if (!rel || rel.split("/").includes("..")) {
    throw new RepoPathResolveError("유효하지 않은 Repository 상대경로입니다.");
  }
  return rel;
}

export async function fetchEquipmentRepositories(
  serverUrl: string,
  equipmentId: number
): Promise<EquipmentRepoInfo[]> {
  const url = ApiUrls.equipmentRepositories(serverUrl, equipmentId);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), LIST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      throw new RepoPathResolveError(
        `장비 Repository 목록 조회 실패 (HTTP ${res.status})`,
        ["서버 실행 상태와 API 주소를 확인하세요."]
      );
    }
    const data = (await res.json()) as Array<Record<string, unknown>>;
    if (!Array.isArray(data)) {
      return [];
    }
    return data.map((r) => ({
      id: Number(r.id),
      name: String(r.name ?? ""),
      source_type: typeof r.source_type === "string" ? r.source_type : undefined,
      repository_url:
        typeof r.repository_url === "string" ? r.repository_url : null,
      canonical_repository_url:
        typeof r.canonical_repository_url === "string"
          ? r.canonical_repository_url
          : null,
      local_path: typeof r.local_path === "string" ? r.local_path : undefined,
      status: typeof r.status === "string" ? r.status : undefined,
    }));
  } finally {
    clearTimeout(timer);
  }
}

function repoUrlCandidates(r: EquipmentRepoInfo): string[] {
  return [r.canonical_repository_url, r.repository_url].filter(Boolean) as string[];
}

/**
 * Match local Git root to a registered equipment repository.
 * Never guesses from relative path alone when multiple repos exist.
 *
 * Priority (PROJECT_SPEC v2.5.1):
 * 1. already confirmed repo_id (caller / cache)
 * 2. canonical remote URL
 * 3. cached identity from prior function/selection lookup
 * 4. repo name / git root folder name
 * 5. single ready-repo fallback
 */
export function matchEquipmentRepository(
  repos: EquipmentRepoInfo[],
  opts: {
    gitRoot: string;
    remoteUrl: string | null;
    preferredRepoId?: number | null;
    cachedRepoId?: number | null;
  }
): { repo: EquipmentRepoInfo; method: string } {
  const gitRoot = opts.gitRoot;
  const remoteUrl = opts.remoteUrl;
  const ready = repos.filter((r) => !r.status || r.status === "ready");
  const pool = ready.length ? ready : repos;
  if (!pool.length) {
    throw new RepoPathResolveError(
      "장비에 등록된 Git Repository가 없습니다.",
      [
        "현재 Git remote URL",
        "장비에 등록된 Repo URL/이름",
        "현재 파일이 속한 Git root",
      ]
    );
  }

  if (opts.preferredRepoId != null && Number.isFinite(opts.preferredRepoId)) {
    const preferred = pool.find((r) => r.id === opts.preferredRepoId);
    if (preferred) {
      return { repo: preferred, method: "preferred_repo_id" };
    }
  }

  if (remoteUrl) {
    const want = canonicalizeRemoteUrl(remoteUrl);
    if (want) {
      const byUrl = pool.filter((r) =>
        repoUrlCandidates(r).some((c) => canonicalizeRemoteUrl(c) === want)
      );
      if (byUrl.length === 1) {
        return { repo: byUrl[0], method: "remote_url" };
      }
      if (byUrl.length > 1) {
        throw new RepoPathResolveError(
          "동일 remote URL을 가진 Repository가 여러 개입니다. 장비 설정을 확인해 주세요.",
          [
            "현재 Git remote URL",
            "장비에 등록된 Repo URL/이름",
            "현재 파일이 속한 Git root",
          ]
        );
      }
    }
  }

  if (opts.cachedRepoId != null && Number.isFinite(opts.cachedRepoId)) {
    const cached = pool.find((r) => r.id === opts.cachedRepoId);
    if (cached) {
      return { repo: cached, method: "cached_repo_id" };
    }
  }

  const rootName = basenamePosix(gitRoot).toLowerCase();
  if (rootName) {
    const byName = pool.filter((r) => r.name.trim().toLowerCase() === rootName);
    if (byName.length === 1) {
      return { repo: byName[0], method: "repo_name" };
    }
  }

  if (pool.length === 1) {
    return { repo: pool[0], method: "single_repo" };
  }

  throw new RepoPathResolveError(
    "현재 파일의 Git Repository를 장비 등록 Repo와 매칭하지 못했습니다.",
    [
      "현재 Git remote URL",
      "장비에 등록된 Repo URL/이름",
      "현재 파일이 속한 Git root",
    ]
  );
}

/** Resolve repo-relative path for selection without equipment URL matching.

PROJECT_SPEC v2.6 — Backend common resolver owns repo identity. Extension only
needs a repo-relative path (+ optional soft hint).
*/
export async function resolveRepoRelativePathForFile(
  filePath: string
): Promise<{ gitRoot: string; repoRelativePath: string; remoteUrl?: string }> {
  const gitRoot = await resolveGitRoot(filePath);
  if (!gitRoot) {
    throw new RepoPathResolveError(
      "선택한 파일이 Git Repository 안에 있지 않습니다.",
      ["현재 파일이 속한 Git root"]
    );
  }
  const repoRelativePath = toRepoRelativePath(gitRoot, filePath);
  const remoteUrl = (await resolveGitRemoteUrl(gitRoot)) || undefined;
  return { gitRoot, repoRelativePath, remoteUrl };
}

/** Full resolution used by older callers / diagnostics (optional hint only). */
export async function resolveRepoPathForSelection(params: {
  serverUrl: string;
  equipmentId: number;
  filePath: string;
  preferredRepoId?: number | null;
}): Promise<RepoPathResolution> {
  const { gitRoot, repoRelativePath, remoteUrl } =
    await resolveRepoRelativePathForFile(params.filePath);
  const repos = await fetchEquipmentRepositories(
    params.serverUrl,
    params.equipmentId
  );

  const cached = lastResolvedByKey.get(
    cacheKey(params.serverUrl, params.equipmentId, gitRoot)
  );

  try {
    const { repo, method } = matchEquipmentRepository(repos, {
      gitRoot,
      remoteUrl: remoteUrl || null,
      preferredRepoId: params.preferredRepoId ?? null,
      cachedRepoId: cached?.repoId ?? null,
    });
    rememberResolvedRepo({
      serverUrl: params.serverUrl,
      equipmentId: params.equipmentId,
      gitRoot,
      repoId: repo.id,
      method,
    });
    return {
      repoId: repo.id,
      repoRelativePath,
      gitRoot,
      matchMethod: method,
      remoteUrl,
    };
  } catch (err) {
    // Soft failure: still return path without repoId so Backend can resolve.
    if (err instanceof RepoPathResolveError) {
      return {
        repoId: cached?.repoId ?? -1,
        repoRelativePath,
        gitRoot,
        matchMethod: "path_only_no_match",
        remoteUrl,
      };
    }
    throw err;
  }
}
