export interface Equipment {
  id: number;
  name: string;
  document_path: string;
  created_at: string;
  updated_at: string;
}

export interface EquipmentInput {
  name: string;
  document_path: string;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  pptx_count?: number;
  recursive?: boolean;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function parseError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d: { msg: string }) => d.msg).join(", ");
  } catch {
    /* ignore */
  }
  return `요청 실패 (${response.status})`;
}

export async function fetchEquipmentList(): Promise<Equipment[]> {
  const response = await fetch(`${API_BASE}/api/equipment`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function fetchEquipment(id: number): Promise<Equipment> {
  const response = await fetch(`${API_BASE}/api/equipment/${id}`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function createEquipment(data: EquipmentInput): Promise<Equipment> {
  const response = await fetch(`${API_BASE}/api/equipment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function updateEquipment(id: number, data: EquipmentInput): Promise<Equipment> {
  const response = await fetch(`${API_BASE}/api/equipment/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

export async function deleteEquipment(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/api/equipment/${id}`, { method: "DELETE" });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function validateDocumentPath(path: string): Promise<ValidationResult> {
  const response = await fetch(`${API_BASE}/api/equipment/validate/document`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
