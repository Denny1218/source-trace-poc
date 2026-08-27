export type TabWorkStatus = "idle" | "running" | "success" | "error";

export interface TabWorkCallbacks {
  onWorkStatusChange?: (status: TabWorkStatus, message?: string) => void;
}
