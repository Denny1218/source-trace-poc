import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, it } from "node:test";
import {
  changeDeviceSteps,
  resolveSettingsWritePlan,
  setupWizardSteps,
} from "../setupWizardPolicy";

describe("setupWizardSteps / changeDeviceSteps flow separation", () => {
  it("setup includes server URL InputBox and saves both serverUrl and equipmentId", () => {
    const steps = setupWizardSteps();
    assert.ok(steps.includes("server_input"));
    assert.ok(steps.includes("health"));
    assert.ok(steps.includes("equipment_list"));
    assert.ok(steps.includes("equipment_pick"));
    assert.ok(steps.includes("save_server_url"));
    assert.ok(steps.includes("save_equipment_id"));
    assert.equal(steps[0], "server_input");
  });

  it("changeDevice does NOT include server URL InputBox or save_server_url", () => {
    const steps = changeDeviceSteps();
    assert.ok(!steps.includes("server_input"));
    assert.ok(!steps.includes("save_server_url"));
    assert.ok(steps.includes("health"));
    assert.ok(steps.includes("equipment_list"));
    assert.ok(steps.includes("equipment_pick"));
    assert.ok(steps.includes("save_equipment_id"));
  });

  it("changeDevice uses existing serverUrl for health and equipment list (documented step order)", () => {
    const steps = changeDeviceSteps();
    assert.deepEqual(steps, [
      "health",
      "equipment_list",
      "equipment_pick",
      "save_equipment_id",
    ]);
  });
});

describe("resolveSettingsWritePlan (storage policy unchanged)", () => {
  it("writes equipmentId to Workspace when a workspace folder is open", () => {
    const plan = resolveSettingsWritePlan(true);
    assert.equal(plan.serverUrlTarget, "Global");
    assert.equal(plan.equipmentIdTarget, "Workspace");
  });

  it("falls back to Global for equipmentId when no workspace folder", () => {
    const plan = resolveSettingsWritePlan(false);
    assert.equal(plan.serverUrlTarget, "Global");
    assert.equal(plan.equipmentIdTarget, "Global");
  });

  it("never stores equipmentId as Global-by-default when workspace exists (other workspace isolation)", () => {
    // Workspace A vs B each have their own .vscode/settings.json —
    // writing to Workspace means changing A cannot overwrite B's equipmentId.
    const planA = resolveSettingsWritePlan(true);
    const planB = resolveSettingsWritePlan(true);
    assert.equal(planA.equipmentIdTarget, "Workspace");
    assert.equal(planB.equipmentIdTarget, "Workspace");
    assert.notEqual(planA.equipmentIdTarget, "Global");
  });
});

describe("runChangeDevice source contract (static)", () => {
  // Compiled tests live in out/test — read the TypeScript source under src/.
  const source = readFileSync(
    join(__dirname, "..", "..", "src", "setupWizard.ts"),
    "utf8"
  );

  /** Extract the runChangeDevice function body (until the next export async function). */
  function changeDeviceBody(): string {
    const start = source.indexOf("export async function runChangeDevice");
    assert.ok(start >= 0, "runChangeDevice must exist");
    const next = source.indexOf("export async function runCheckServer", start + 1);
    assert.ok(next > start);
    return source.slice(start, next);
  }

  it("does not call showInputBox (no server URL prompt)", () => {
    const body = changeDeviceBody();
    assert.doesNotMatch(body, /showInputBox/);
  });

  it("does not call runSetupWizard except when server URL is missing", () => {
    const body = changeDeviceBody();
    // Only allowed inside the !serverUrl branch (설정 시작).
    const calls = body.match(/runSetupWizard\(/g) ?? [];
    assert.equal(calls.length, 1, "exactly one runSetupWizard call (missing-server redirect)");
    assert.match(body, /if\s*\(\s*!serverUrl\s*\)[\s\S]*runSetupWizard/);
  });

  it("calls checkServerHealth and pickEquipmentOnServer; saves equipmentId only", () => {
    const body = changeDeviceBody();
    assert.match(body, /checkServerHealth/);
    assert.match(body, /pickEquipmentOnServer/);
    assert.match(body, /saveEquipmentId/);
    assert.doesNotMatch(body, /saveServerUrl/);
  });
});

describe("runSetupWizard source contract (static)", () => {
  const source = readFileSync(
    join(__dirname, "..", "..", "src", "setupWizard.ts"),
    "utf8"
  );

  function setupBody(): string {
    const start = source.indexOf("export async function runSetupWizard");
    assert.ok(start >= 0);
    const next = source.indexOf("export async function runChangeDevice", start + 1);
    assert.ok(next > start);
    return source.slice(start, next);
  }

  it("calls showInputBox for server URL", () => {
    assert.match(setupBody(), /showInputBox/);
  });

  it("saves both serverUrl and equipmentId", () => {
    const body = setupBody();
    assert.match(body, /saveServerUrl/);
    assert.match(body, /saveEquipmentId/);
  });
});
