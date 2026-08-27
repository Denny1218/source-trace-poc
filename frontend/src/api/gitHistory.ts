export interface CommitListItem {
  id: number;
  commit_hash: string;
  commit_date: string;
  author: string;
  message: string;
  repository_id: number;
  repository_name: string;
  changed_file_count: number;
  additions: number;
  deletions: number;
}

export interface CommitListResponse {
  items: CommitListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface CommitChange {
  id: number;
  file_path: string;
  change_type: string;
  additions: number | null;
  deletions: number | null;
  diff: string | null;
}

export interface CommitDetail {
  id: number;
  equipment_id: number;
  commit_hash: string;
  commit_date: string;
  author: string;
  message: string;
  parent_hash: string | null;
  changes: CommitChange[];
}

export interface CommitSearchParams {
  q?: string;
  date_from?: string;
  date_to?: string;
  file_path?: string;
  author?: string;
  repository_id?: number;
  page?: number;
  page_size?: number;
}

export interface GitSyncResult {
  equipment_id: number;
  scanned_commits: number;
  new_commits: number;
  skipped_commits: number;
  new_changes: number;
  status: string;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* ignore */
  }
  return `요청 실패 (${response.status})`;
}

function buildQuery(params: CommitSearchParams): string {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.date_from) qs.set("date_from", params.date_from);
  if (params.date_to) qs.set("date_to", params.date_to);
  if (params.file_path) qs.set("file_path", params.file_path);
  if (params.author) qs.set("author", params.author);
  if (params.repository_id) qs.set("repository_id", String(params.repository_id));
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export async function fetchCommitList(
  equipmentId: number,
  params: CommitSearchParams = {},
): Promise<CommitListResponse> {
  const response = await fetch(
    `${API_BASE}/api/equipment/${equipmentId}/git/commits${buildQuery(params)}`,
  );
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function fetchCommitDetail(commitId: number): Promise<CommitDetail> {
  const response = await fetch(`${API_BASE}/api/git/commits/${commitId}`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function syncGitHistory(equipmentId: number): Promise<GitSyncResult> {
  const response = await fetch(`${API_BASE}/api/equipment/${equipmentId}/sync/git`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export { fetchEquipmentList, type Equipment } from "./equipment";
