/**
 * Brand / Extension icon packaging checks (PROJECT_SPEC v2.6).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import * as path from "node:path";

const EXT_ROOT = path.resolve(__dirname, "..", "..");
const PKG = JSON.parse(
  fs.readFileSync(path.join(EXT_ROOT, "package.json"), "utf8")
) as { icon?: string; version: string };

test("package.json icon points to an existing asset file", () => {
  assert.ok(PKG.icon, "package.json must declare icon");
  const iconPath = path.join(EXT_ROOT, PKG.icon!);
  assert.ok(fs.existsSync(iconPath), `missing icon file: ${PKG.icon}`);
  assert.ok(fs.statSync(iconPath).size > 0, "icon file is empty");
});

test("extension icon asset is the ATEC Mobility wordmark file", () => {
  assert.equal(PKG.icon, "assets/extension_icon_256.png");
  assert.ok(fs.existsSync(path.join(EXT_ROOT, "assets", "extension_icon_256.png")));
});
