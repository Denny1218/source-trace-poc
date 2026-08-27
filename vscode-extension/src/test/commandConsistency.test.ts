/**
 * Source Trace command contribution consistency (PROJECT_SPEC v2.6 / test26).
 *
 * Invariant:
 * - Every command referenced from contributes.menus exists in contributes.commands
 * - Official contributes.commands are registered in extension.ts
 * - sourceTrace.analyzeSelection must NOT appear in menus (stale menu warning)
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";

const EXT_ROOT = path.resolve(__dirname, "..", "..");
const PKG = JSON.parse(
  fs.readFileSync(path.join(EXT_ROOT, "package.json"), "utf8")
) as {
  contributes: {
    commands: Array<{ command: string }>;
    menus?: Record<string, Array<{ command?: string }>>;
    keybindings?: Array<{ command?: string }>;
  };
};

const EXT_SRC = fs.readFileSync(path.join(EXT_ROOT, "src", "extension.ts"), "utf8");

function registeredCommands(): Set<string> {
  const found = new Set<string>();
  const re = /registerCommand\(\s*["']([^"']+)["']/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(EXT_SRC)) !== null) {
    found.add(m[1]);
  }
  return found;
}

function menuCommands(): Set<string> {
  const found = new Set<string>();
  const menus = PKG.contributes.menus || {};
  for (const entries of Object.values(menus)) {
    for (const entry of entries || []) {
      if (entry.command) {
        found.add(entry.command);
      }
    }
  }
  for (const kb of PKG.contributes.keybindings || []) {
    if (kb.command) {
      found.add(kb.command);
    }
  }
  return found;
}

test("all menu/keybinding commands exist in contributes.commands", () => {
  const declared = new Set(PKG.contributes.commands.map((c) => c.command));
  for (const cmd of menuCommands()) {
    assert.ok(
      declared.has(cmd),
      `menus/keybindings reference '${cmd}' which is missing from contributes.commands`
    );
  }
});

test("official contributes.commands are registered in extension.ts", () => {
  const registered = registeredCommands();
  for (const cmd of PKG.contributes.commands.map((c) => c.command)) {
    assert.ok(registered.has(cmd), `contributes.commands '${cmd}' is not registerCommand'd`);
  }
});

test("sourceTrace.analyzeSelection is not in menus (avoids VS Code 1 message warning)", () => {
  assert.equal(
    menuCommands().has("sourceTrace.analyzeSelection"),
    false,
    "stale menu reference to sourceTrace.analyzeSelection"
  );
  const declared = new Set(PKG.contributes.commands.map((c) => c.command));
  assert.equal(
    declared.has("sourceTrace.analyzeSelection"),
    false,
    "legacy analyzeSelection must not be listed in contributes.commands"
  );
});

test("legacy analyzeSelection remains registered for silent compatibility only", () => {
  assert.ok(
    registeredCommands().has("sourceTrace.analyzeSelection"),
    "compat registerCommand(sourceTrace.analyzeSelection) missing"
  );
});

test("showResultDocument opens new Untitled Markdown without auto Preview", () => {
  const fnStart = EXT_SRC.indexOf("async function showResultDocument");
  assert.ok(fnStart >= 0, "showResultDocument missing");
  const nextFn = EXT_SRC.indexOf("\nfunction handleError", fnStart);
  const body = EXT_SRC.slice(fnStart, nextFn > fnStart ? nextFn : undefined);

  assert.match(body, /openTextDocument\(\{\s*content:\s*text,\s*language:\s*"markdown"/);
  assert.match(body, /showTextDocument/);
  assert.equal(body.includes("showPreview"), false, "must not auto-open Markdown Preview");
  assert.equal(body.includes("showPreviewToSide"), false, "must not auto-open Preview to side");
  assert.equal(body.includes("WorkspaceEdit"), false, "must not overwrite prior Untitled");
  assert.equal(body.includes("ownedMarkdownPreviewTabs"), false, "Preview tab tracking removed");
  assert.equal(/writeFile|saveAs|createFile/i.test(body), false, "must not auto-save result to disk");
});

test("extension has no Markdown Preview automation helpers", () => {
  assert.equal(EXT_SRC.includes("closeOwnedSourceTraceMarkdownPreviews"), false);
  assert.equal(EXT_SRC.includes("claimNewlyOpenedMarkdownPreviewTabs"), false);
  assert.equal(EXT_SRC.includes("listMarkdownPreviewTabs"), false);
  assert.equal(EXT_SRC.includes("resultMarkdownDocument"), false);
});
