/**
 * Pure setup/change-device policy helpers — no vscode import.
 * Used by setupWizard.ts and unit tests.
 */

/** Settings write target — mirrors vscode.ConfigurationTarget for tests. */
export type SettingsWriteTarget = "Global" | "Workspace";

export interface SettingsWritePlan {
  serverUrlTarget: SettingsWriteTarget;
  equipmentIdTarget: SettingsWriteTarget;
}

/** Ordered steps for each command — used by unit tests to assert flow separation. */
export type WizardStep =
  | "server_input"
  | "health"
  | "equipment_list"
  | "equipment_pick"
  | "save_server_url"
  | "save_equipment_id";

/**
 * Storage targets for a successful setup / change-device save.
 * serverUrl is always Global; equipmentId is Workspace when a folder is open.
 */
export function resolveSettingsWritePlan(hasWorkspace: boolean): SettingsWritePlan {
  return {
    serverUrlTarget: "Global",
    equipmentIdTarget: hasWorkspace ? "Workspace" : "Global",
  };
}

/** Steps performed by `Source Trace: 서버 및 장비 설정`. */
export function setupWizardSteps(): WizardStep[] {
  return [
    "server_input",
    "health",
    "equipment_list",
    "equipment_pick",
    "save_server_url",
    "save_equipment_id",
  ];
}

/**
 * Steps performed by `Source Trace: 장비 변경`.
 * Must NOT include `server_input` or `save_server_url`.
 */
export function changeDeviceSteps(): WizardStep[] {
  return ["health", "equipment_list", "equipment_pick", "save_equipment_id"];
}
