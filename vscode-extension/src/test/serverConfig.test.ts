import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ApiUrls,
  buildApiUrl,
  extractOriginFromBackendUrl,
  normalizeServerUrl,
  resolveServerUrl,
  sanitizeUrl,
} from "../serverConfig";

describe("normalizeServerUrl", () => {
  it("accepts plain IP:port and prefixes http://", () => {
    const r = normalizeServerUrl("192.168.155.89:8010");
    assert.ok(r.ok);
    if (r.ok) {
      assert.equal(r.url, "http://192.168.155.89:8010");
    }
  });

  it("strips trailing slash", () => {
    const r = normalizeServerUrl("http://server:8010/");
    assert.ok(r.ok);
    if (r.ok) {
      assert.equal(r.url, "http://server:8010");
    }
  });

  it("strips path the user accidentally typed", () => {
    const r = normalizeServerUrl("http://server:8010/api/trace/report");
    assert.ok(r.ok);
    if (r.ok) {
      assert.equal(r.url, "http://server:8010");
    }
  });

  it("accepts https", () => {
    const r = normalizeServerUrl("https://secure-server:443");
    assert.ok(r.ok);
    if (r.ok) {
      assert.ok(r.url.startsWith("https://"));
    }
  });

  it("rejects empty string", () => {
    const r = normalizeServerUrl("");
    assert.ok(!r.ok);
  });

  it("rejects URL with credentials", () => {
    const r = normalizeServerUrl("http://user:pass@server:8010");
    assert.ok(!r.ok);
    if (!r.ok) {
      assert.ok(r.error.includes("사용자명") || r.error.includes("비밀번호"));
    }
  });

  it("rejects clearly invalid string", () => {
    const r = normalizeServerUrl("not a url at all!!!");
    assert.ok(!r.ok);
  });
});

describe("sanitizeUrl", () => {
  it("removes credentials and returns hadCredentials=true", () => {
    const { url, hadCredentials } = sanitizeUrl("http://admin:secret@server:8010/path");
    assert.ok(!url.includes("admin"));
    assert.ok(!url.includes("secret"));
    assert.equal(hadCredentials, true);
  });

  it("returns hadCredentials=false for clean URL", () => {
    const { hadCredentials } = sanitizeUrl("http://server:8010");
    assert.equal(hadCredentials, false);
  });
});

describe("extractOriginFromBackendUrl", () => {
  it("extracts origin from full legacy backendUrl", () => {
    const origin = extractOriginFromBackendUrl(
      "http://192.168.155.89:8010/api/trace/report"
    );
    assert.equal(origin, "http://192.168.155.89:8010");
  });

  it("extracts origin when path is shorter", () => {
    const origin = extractOriginFromBackendUrl("http://server:8010/api/other");
    assert.equal(origin, "http://server:8010");
  });

  it("returns null for relative path", () => {
    const origin = extractOriginFromBackendUrl("/api/trace/report");
    assert.equal(origin, null);
  });
});

describe("resolveServerUrl", () => {
  it("prefers serverUrl over backendUrl", () => {
    const cfg = resolveServerUrl(
      "http://new-server:9000",
      "http://old-server:8010/api/trace/report"
    );
    assert.ok(cfg);
    assert.equal(cfg!.serverUrl, "http://new-server:9000");
    assert.ok(!cfg!.migratedFromLegacy);
  });

  it("migrates from backendUrl when serverUrl is absent", () => {
    const cfg = resolveServerUrl(null, "http://192.168.155.89:8010/api/trace/report");
    assert.ok(cfg);
    assert.equal(cfg!.serverUrl, "http://192.168.155.89:8010");
    assert.equal(cfg!.migratedFromLegacy, true);
  });

  it("returns null when both are absent", () => {
    const cfg = resolveServerUrl(null, null);
    assert.equal(cfg, null);
  });

  it("returns null when serverUrl is empty string", () => {
    const cfg = resolveServerUrl("", null);
    assert.equal(cfg, null);
  });

  it("returns null when serverUrl has credentials (rejected by normalizer)", () => {
    const cfg = resolveServerUrl("http://user:pass@server:8010", null);
    assert.equal(cfg, null);
  });
});

describe("ApiUrls", () => {
  const base = "http://server:8010";

  it("health URL", () => {
    assert.equal(ApiUrls.health(base), "http://server:8010/api/health");
  });

  it("equipmentList URL", () => {
    assert.equal(ApiUrls.equipmentList(base), "http://server:8010/api/equipment");
  });

  it("equipmentById URL", () => {
    assert.equal(ApiUrls.equipmentById(base, 3), "http://server:8010/api/equipment/3");
  });

  it("analyzeTrace URL", () => {
    assert.equal(
      ApiUrls.analyzeTrace(base),
      "http://server:8010/api/trace/report"
    );
  });

  // PROJECT_SPEC v2.4 §5 — 함수 조회(/api/trace/report)와 분리된 선택 코드 전용 엔드포인트
  it("analyzeSelection URL", () => {
    assert.equal(
      ApiUrls.analyzeSelection(base),
      "http://server:8010/api/trace/selection"
    );
  });

  it("analyzeSelection URL differs from analyzeTrace URL", () => {
    assert.notEqual(ApiUrls.analyzeSelection(base), ApiUrls.analyzeTrace(base));
  });
});

describe("buildApiUrl", () => {
  it("joins base and path without double slash", () => {
    assert.equal(buildApiUrl("http://server:8010", "/api/health"), "http://server:8010/api/health");
  });

  it("handles base with trailing slash", () => {
    assert.equal(buildApiUrl("http://server:8010/", "/api/health"), "http://server:8010/api/health");
  });
});
