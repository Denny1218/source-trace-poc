import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  resolveBackendBase,
  resolveEquipmentId,
  verifyErrorMessage,
} from "../equipmentVerifier";

describe("resolveEquipmentId", () => {
  it("returns null when null", () => {
    assert.equal(resolveEquipmentId(null), null);
  });
  it("returns null when undefined", () => {
    assert.equal(resolveEquipmentId(undefined), null);
  });
  it("returns null when 0", () => {
    assert.equal(resolveEquipmentId(0), null);
  });
  it("returns null when negative", () => {
    assert.equal(resolveEquipmentId(-1), null);
  });
  it("returns null when NaN", () => {
    assert.equal(resolveEquipmentId(NaN), null);
  });
  it("returns integer when valid", () => {
    assert.equal(resolveEquipmentId(2), 2);
  });
  it("returns floored integer for float input", () => {
    assert.equal(resolveEquipmentId(2.9), 2);
  });
  it("does not treat 1 as special default — still valid positive", () => {
    assert.equal(resolveEquipmentId(1), 1);
  });
});

describe("resolveBackendBase", () => {
  it("strips path from full legacy backendUrl", () => {
    assert.equal(
      resolveBackendBase("http://192.168.1.1:8010/api/trace/report"),
      "http://192.168.1.1:8010"
    );
  });
  it("handles plain origin", () => {
    assert.equal(resolveBackendBase("http://server:8010"), "http://server:8010");
  });
  it("handles /api/ path without trace suffix", () => {
    assert.equal(
      resolveBackendBase("http://server:8010/api/other"),
      "http://server:8010"
    );
  });
});

describe("verifyErrorMessage", () => {
  it("not_configured message guides to settings", () => {
    const msg = verifyErrorMessage({ ok: false, reason: "not_configured" });
    assert.ok(msg.includes("sourceTrace.equipmentId"));
  });
  it("not_found message includes the id", () => {
    const msg = verifyErrorMessage({ ok: false, reason: "not_found", id: 99 });
    assert.ok(msg.includes("99"));
  });
  it("connection_error message mentions backendUrl", () => {
    const msg = verifyErrorMessage({
      ok: false,
      reason: "connection_error",
      id: 2,
      detail: "서버에 연결할 수 없습니다",
    });
    assert.ok(msg.includes("backendUrl") || msg.includes("연결할 수 없습니다"));
  });
  it("invalid_id message guides to correct input", () => {
    const msg = verifyErrorMessage({ ok: false, reason: "invalid_id", id: "abc" });
    assert.ok(msg.includes("올바르지 않습니다") || msg.includes("정수"));
  });
});
