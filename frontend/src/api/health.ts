export interface HealthStatus {
  status: string;
  database: string;
  git: string;
  ollama: string;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function fetchHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE}/api/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}
