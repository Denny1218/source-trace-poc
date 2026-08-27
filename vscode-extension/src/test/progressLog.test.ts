import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  extractLifecycleSummary,
  extractSelectionSummary,
  ProgressLogger,
  toDisplayPath,
} from "../progressLog";
import { buildResultDocumentText } from "../requestBuilder";

describe("progressLog", () => {
  it("extracts lifecycle_summary from debug payload", () => {
    const summary = extractLifecycleSummary({
      debug: {
        lifecycle_summary: {
          total_candidates: 7,
          creation_count: 1,
          core_followup_count: 2,
          overall_confidence: "보통",
        },
      },
    });
    assert.equal(summary?.total_candidates, 7);
    assert.equal(summary?.creation_count, 1);
    assert.equal(summary?.overall_confidence, "보통");
  });

  it("begin/stats omit internal debug fields", () => {
    const lines: string[] = [];
    const logger = new ProgressLogger({ appendLine: (v) => lines.push(v) });
    logger.begin({
      requestKind: "함수 변경 이력 조회",
      userQuestion: "이 함수 변경이력 알려줘",
      symbol: "demo_fn",
      file: "C:/ws/Card/mif_post/src/a.c",
      equipment: { id: 3, name: "휴대용정산기", serverUrl: "http://127.0.0.1:8010" },
    });
    logger.stats(
      {
        displayed_git_count: 6,
        related_document_count: 2,
        direct_confirmed_count: 6,
        ppt_official_doc_count: 2,
        ppt_commit_direct_doc_count: 1,
        ppt_stage_link_doc_count: 0,
        ppt_related_ref_doc_count: 1,
      },
      "높음"
    );
    const text = lines.join("\n");
    assert.match(text, /요청: 함수 변경 이력 조회/);
    assert.match(text, /사용자 질문: 이 함수 변경이력 알려줘/);
    assert.match(text, /Git 이력: 6건/);
    assert.match(text, /관련 문서: 2건/);
    assert.doesNotMatch(text, /관련 공식 문서/);
    assert.doesNotMatch(text, /Commit 직접 연결 문서/);
    assert.doesNotMatch(text, /단계 연결 문서/);
    assert.doesNotMatch(text, /관련 참고 문서/);
    assert.doesNotMatch(text, /분석 신뢰도/);
    assert.doesNotMatch(text, /공식 변경내역서:/);
    assert.doesNotMatch(text, /공식 적용/);
    assert.doesNotMatch(text, /source_mode=/);
    assert.doesNotMatch(text, /query_sent=/);
    assert.doesNotMatch(text, /immediate_selection_chars=/);
  });

  it("toDisplayPath prefers workspace-relative path", () => {
    const rel = toDisplayPath("C:/ws/Card/a.c", ["C:/ws"]);
    assert.equal(rel.replace(/\\/g, "/"), "Card/a.c");
  });

  it("begin() shows the Output channel automatically (Continue 제거 회귀 방지)", () => {
    let shown: boolean | undefined;
    let preserveFocusArg: boolean | undefined;
    const logger = new ProgressLogger({
      appendLine: () => undefined,
      show: (preserveFocus?: boolean) => {
        shown = true;
        preserveFocusArg = preserveFocus;
      },
    });
    logger.begin({ requestKind: "함수 변경 이력 조회" });
    assert.equal(shown, true);
    assert.equal(preserveFocusArg, true);
  });

  it("begin() does not throw when the channel has no show() (test doubles)", () => {
    const logger = new ProgressLogger({ appendLine: () => undefined });
    assert.doesNotThrow(() => logger.begin({ requestKind: "함수 변경 이력 조회" }));
  });

  it("selectionStats logs primary commit, line history, and document counts", () => {
    const lines: string[] = [];
    const logger = new ProgressLogger({ appendLine: (v) => lines.push(v) });
    logger.selectionStats({
      blameGroupCount: 1,
      primaryCommitShortHash: "abc1234",
      lineHistoryAvailable: true,
      lineHistoryCount: 3,
      documentLinkCount: 0,
    });
    const text = lines.join("\n");
    assert.match(text, /현재 라인 Commit: abc1234/);
    assert.match(text, /line history 조회 완료 \(3건\)/);
    assert.match(text, /관련 문서: 0건/);
  });

  it("selectionStats reports line history tracking limitation when unavailable", () => {
    const lines: string[] = [];
    const logger = new ProgressLogger({ appendLine: (v) => lines.push(v) });
    logger.selectionStats({
      blameGroupCount: 1,
      primaryCommitShortHash: "abc1234",
      lineHistoryAvailable: false,
      documentLinkCount: 0,
    });
    const text = lines.join("\n");
    assert.match(text, /line history 확인 제한/);
  });

  it("selectionStats never prints selected code text or raw diff", () => {
    const lines: string[] = [];
    const logger = new ProgressLogger({ appendLine: (v) => lines.push(v) });
    logger.selectionStats({
      blameGroupCount: 1,
      primaryCommitShortHash: "abc1234",
      lineHistoryAvailable: true,
      lineHistoryCount: 1,
      documentLinkCount: 1,
    });
    const text = lines.join("\n");
    assert.doesNotMatch(text, /diff/i);
    assert.doesNotMatch(text, /selected_code/i);
  });

  it("extractSelectionSummary reads blame/document/line-history counts from a selection response", () => {
    const summary = extractSelectionSummary({
      blame_rows: [{ short_hash: "abc1234", is_uncommitted: false }],
      line_history: [{ commit_hash: "abc1234def" }, { commit_hash: "0001111222" }],
      line_history_available: true,
      document_links: [],
    });
    assert.equal(summary?.blameGroupCount, 1);
    assert.equal(summary?.primaryCommitShortHash, "abc1234");
    assert.equal(summary?.lineHistoryAvailable, true);
    assert.equal(summary?.lineHistoryCount, 2);
    assert.equal(summary?.documentLinkCount, 0);
  });

  it("extractSelectionSummary omits primary commit when the top line is uncommitted", () => {
    const summary = extractSelectionSummary({
      blame_rows: [{ short_hash: "abc1234", is_uncommitted: true }],
      line_history_available: false,
      document_links: [],
    });
    assert.equal(summary?.primaryCommitShortHash, undefined);
    assert.equal(summary?.lineHistoryAvailable, false);
  });
});

describe("buildResultDocumentText lifecycle body", () => {
  it("does not duplicate title when server body already has heading", () => {
    const text = buildResultDocumentText({
      response: { content: "# test_fn 변경 이력\n\n## 한눈에 보기\n\n---\n조회: 2026-08-03 15:45" },
      detectedSymbol: "test_fn",
      queriedAt: new Date("2026-07-29T16:52:00"),
    });
    assert.ok(text.startsWith("# test_fn 변경 이력"));
    assert.equal((text.match(/# test_fn 변경 이력/g) ?? []).length, 1);
    assert.match(text, /조회: 2026-08-03 15:45/);
    assert.doesNotMatch(text, /조회 시각:/);
  });
});
