export type SourceType = "remote" | "local";
export type RepositoryStatus = "pending" | "preparing" | "ready" | "error";

export interface GitRepository {
  id: number;
  equipment_id: number;
  name: string;
  source_type: SourceType;
  repository_url: string | null;
  canonical_repository_url: string | null;
  yona_username: string | null;
  local_path: string;
  status: RepositoryStatus;
  created_at: string;
  updated_at: string;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  yona_username?: string | null;
  canonical_repository_url?: string | null;
}

export interface GitRepositoryCreate {
  name: string;
  source_type: SourceType;
  repository_url?: string;
  local_path?: string;
}

export interface GitRepositoryUpdate {
  name: string;
  repository_url?: string;
  local_path?: string;
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

export async function fetchRepositories(equipmentId: number): Promise<GitRepository[]> {
  const response = await fetch(`${API_BASE}/api/equipment/${equipmentId}/repositories`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function createRepository(
  equipmentId: number,
  data: GitRepositoryCreate,
): Promise<GitRepository> {
  const response = await fetch(`${API_BASE}/api/equipment/${equipmentId}/repositories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function prepareRepository(repositoryId: number): Promise<GitRepository> {
  const response = await fetch(`${API_BASE}/api/repositories/${repositoryId}/prepare`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function updateRepository(
  repositoryId: number,
  data: GitRepositoryUpdate,
): Promise<GitRepository> {
  const response = await fetch(`${API_BASE}/api/repositories/${repositoryId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function deleteRepository(repositoryId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/repositories/${repositoryId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function validateRemoteUrl(repositoryUrl: string): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE}/api/repositories/validate/remote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repository_url: repositoryUrl }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function validateLocalPath(localPath: string): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE}/api/repositories/validate/local`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ local_path: localPath }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function syncRepository(repositoryId: number): Promise<{
  new_commits: number;
  new_changes: number;
}> {
  const response = await fetch(`${API_BASE}/api/repositories/${repositoryId}/sync`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
