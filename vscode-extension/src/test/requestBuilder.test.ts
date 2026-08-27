/**
 * Plain `node:test` unit tests for the VS Code-API-free helpers.
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  buildAnalyzeRequest,
  buildRequestBody,
  buildResultDocumentText,
  buildResultTitle,
  buildSelectionRequest,
  pickResultMarkdown,
  truncateSelectedCode,
} from "../requestBuilder";

test("truncateSelectedCode keeps short code untouched", () => {
  const { code, truncated } = truncateSelectedCode("int x = 1;", 4000);
  assert.equal(code, "int x = 1;");
  assert.equal(truncated, false);
});

test("truncateSelectedCode truncates to maxChars and flags it", () => {
  const long = "x".repeat(5000);
  const { code, truncated } = truncateSelectedCode(long, 4000);
  assert.equal(code.length, 4000);
  assert.equal(truncated, true);
});

test("buildRequestBody produces the exact /api/trace/report shape with use_ollama=false", () => {
  const { body, truncated } = buildRequestBody({
    equipmentId: 7,
    query: "선택한 코드가 왜 변경됐는지 알려줘",
    filePath: "/workspace/card/sc_kscc/src/card_sc_tm.c",
    selectedCode: "int test_Alias(void) { return 0; }",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.deepEqual(Object.keys(body).sort(), [
    "equipment_id",
    "file_path",
    "query",
    "selected_code",
    "use_ollama",
  ]);
  assert.equal(body.equipment_id, 7);
  assert.equal(body.use_ollama, false);
  assert.equal(body.file_path, "/workspace/card/sc_kscc/src/card_sc_tm.c");
  assert.equal(body.selected_code.includes("test_Alias"), true);
  assert.equal(body.query, "선택한 코드가 왜 변경됐는지 알려줘");
  assert.equal(truncated, false);
});

test("buildAnalyzeRequest augments query and selected_code for single symbol selection", () => {
  const { body, debug } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "이 함수 언제 추가되었어?",
    filePath: "C:\\workspace\\card_sc_tm.c",
    selectedCode: "test_Alias",
    detectedSymbol: "test_Alias",
    sourceMode: "selection_symbol",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.selected_code, "test_Alias");
  assert.match(body.query, /test_Alias/);
  assert.equal(body.query, "test_Alias 함수 언제 추가되었어?");
  assert.equal(debug.detected_symbol, "test_Alias");
  assert.equal(debug.source_mode, "selection_symbol");
  assert.equal(debug.selected_code_sent_chars, "test_Alias".length);
});

test("buildAnalyzeRequest extracts symbol from void test_Alias() and augments query", () => {
  const { body } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "이 함수 언제 추가되었어?",
    filePath: "a.c",
    selectedCode: "void test_Alias()",
    detectedSymbol: "test_Alias",
    sourceMode: "selection",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.selected_code, "void test_Alias()");
  assert.equal(body.query, "test_Alias 함수 언제 추가되었어?");
});

test("buildAnalyzeRequest handles trans_write_climatecard_data call site", () => {
  const { body } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "이 함수 언제 추가되었어?",
    filePath: "a.c",
    selectedCode: "trans_write_climatecard_data(card_decode_data_ptr, ...)",
    detectedSymbol: "trans_write_climatecard_data",
    sourceMode: "selection",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.match(body.selected_code, /trans_write_climatecard_data/);
  assert.equal(body.query, "trans_write_climatecard_data 함수 언제 추가되었어?");
});

test("buildAnalyzeRequest cursor_word fallback never sends empty selected_code", () => {
  const { body } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "변경 이력",
    filePath: "a.c",
    selectedCode: "test_Alias",
    detectedSymbol: "test_Alias",
    sourceMode: "cursor_word",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.selected_code, "test_Alias");
  assert.notEqual(body.selected_code, "");
});

test("buildRequestBody truncates selected_code at the configured limit", () => {
  const long = "y".repeat(9000);
  const { body, truncated } = buildRequestBody({
    equipmentId: 7,
    query: "질문",
    filePath: "a.c",
    selectedCode: long,
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.selected_code.length, 4000);
  assert.equal(truncated, true);
});

test("buildRequestBody preserves Korean query text and respects useOllama=true when set", () => {
  const { body } = buildRequestBody({
    equipmentId: 7,
    query: "카드 정산 로직이 왜 바뀌었는지 알려줘",
    filePath: "a.c",
    selectedCode: "int x;",
    useOllama: true,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.query, "카드 정산 로직이 왜 바뀌었는지 알려줘");
  assert.equal(body.use_ollama, true);
});

test("pickResultMarkdown prefers content over answer/evidence_answer", () => {
  const md = pickResultMarkdown({
    content: "CONTENT",
    answer: "ANSWER",
    evidence_answer: "EVIDENCE",
  });
  assert.equal(md, "CONTENT");
});

test("pickResultMarkdown falls back to answer when content is missing", () => {
  const md = pickResultMarkdown({ answer: "ANSWER", evidence_answer: "EVIDENCE" });
  assert.equal(md, "ANSWER");
});

test("pickResultMarkdown falls back to evidence_answer when content/answer are missing", () => {
  const md = pickResultMarkdown({ evidence_answer: "EVIDENCE" });
  assert.equal(md, "EVIDENCE");
});

test("pickResultMarkdown falls back to pretty JSON when nothing usable is present", () => {
  const md = pickResultMarkdown({ foo: "bar" });
  assert.equal(md.startsWith("```json"), true);
  assert.equal(md.includes('"foo"'), true);
});

test("buildResultTitle uses detected_symbol when present", () => {
  assert.equal(buildResultTitle("test_Alias", "card_sc_tm.c"), "# test_Alias 변경 이력 분석 결과");
});

test("buildResultTitle uses file basename when symbol missing", () => {
  assert.equal(buildResultTitle(undefined, "C:\\src\\card_sc_tm.c"), "# card_sc_tm.c 변경 이력 분석 결과");
});

test("buildResultTitle falls back to generic heading", () => {
  assert.equal(buildResultTitle(), "# 장비 변경 이력 분석 결과");
});

test("buildResultDocumentText omits Extension debug by default", () => {
  const text = buildResultDocumentText({
    response: { content: "## 본문" },
    detectedSymbol: "test_Alias",
    filePath: "card_sc_tm.c",
    debug: {
      source_mode: "selection_symbol",
      detected_symbol: "test_Alias",
      selected_text_chars: 10,
      selected_code_sent_chars: 10,
      query_sent: "test_Alias 함수 언제 추가되었어?",
      file_path_basename: "card_sc_tm.c",
      selected_text_preview: "test_Alias",
    },
    queriedAt: new Date("2026-07-28T15:41:00"),
  });
  assert.match(text, /^# test_Alias 변경 이력 분석 결과/);
  assert.match(text, /조회: 2026-07-28 15:41/);
  assert.doesNotMatch(text, /Extension debug/);
  assert.doesNotMatch(text, /source_mode=`selection_symbol`/);
  assert.match(text, /## 본문/);
});

test("buildResultDocumentText includes folded debug when showDebug=true", () => {
  const text = buildResultDocumentText({
    response: { content: "## 본문" },
    detectedSymbol: "test_Alias",
    filePath: "card_sc_tm.c",
    showDebug: true,
    debug: {
      source_mode: "selection_symbol",
      detected_symbol: "test_Alias",
      selected_text_chars: 10,
      selected_code_sent_chars: 10,
      query_sent: "test_Alias 함수 언제 추가되었어?",
      file_path_basename: "card_sc_tm.c",
      selected_text_preview: "test_Alias",
    },
    queriedAt: new Date("2026-07-28T15:41:00"),
  });
  assert.match(text, /^# test_Alias 변경 이력 분석 결과/);
  assert.match(text, /조회: 2026-07-28 15:41/);
  assert.match(text, /Extension debug/);
  assert.match(text, /<details>/);
  assert.match(text, /source_mode=`selection_symbol`/);
  assert.match(text, /## 본문/);
  assert.doesNotMatch(text, /^# 장비 변경 이력 분석 결과$/m);
});

test("buildResultDocumentText does not append second query footer when backend already has 조회", () => {
  const text = buildResultDocumentText({
    response: {
      content: "# demo_fn 변경 이력\n\n## 한눈에 보기\n\n---\n조회: 2026-08-05 10:38",
    },
    detectedSymbol: "demo_fn",
    queriedAt: new Date("2026-08-05T10:41:00"),
  });
  assert.match(text, /조회: 2026-08-05 10:38/);
  assert.doesNotMatch(text, /조회 시각:/);
  assert.equal((text.match(/조회:/g) ?? []).length, 1);
});

test("buildResultDocumentText file-based title when no symbol", () => {
  const text = buildResultDocumentText({
    response: { content: "ok" },
    filePath: "/x/card_sc_tm.c",
    queriedAt: new Date("2026-01-01T09:00:00"),
  });
  assert.match(text, /^# card_sc_tm.c 변경 이력 분석 결과/);
});

test("buildAnalyzeRequest sends optional source_mode and detected_symbol", () => {
  const { body } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "이 함수 언제 추가되었어?",
    filePath: "card_sc_tm.c",
    selectedCode: "test_Alias",
    detectedSymbol: "test_Alias",
    sourceMode: "selection_symbol",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.source_mode, "selection_symbol");
  assert.equal(body.detected_symbol, "test_Alias");
  assert.equal(body.selected_code, "test_Alias");
  assert.match(body.query, /test_Alias/);
});

// PROJECT_SPEC v2.6 — POST /api/trace/selection 요청 계약
test("buildSelectionRequest sends repo_relative_path without requiring repo_id", () => {
  const { body } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "/home/op/workspace/Fare/src/fare_calc.c",
    repoRelativePath: "Fare/src/fare_calc.c",
    startLine: 651,
    endLine: 651,
    selectedCode: "if (trans_info_ptr->is_climate_init == CLIMATE_CLEAR_PENALTY)",
    enclosingSymbol: "fare_is_xfer",
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.equipment_id, 1);
  assert.equal(body.repo_relative_path, "Fare/src/fare_calc.c");
  assert.equal("repo_id" in body, false);
  assert.equal(body.client_file_path, "/home/op/workspace/Fare/src/fare_calc.c");
  assert.equal("file_path" in body, false);
});

test("buildSelectionRequest includes optional repo_id_hint when provided", () => {
  const { body } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "/home/op/workspace/Fare/src/fare_calc.c",
    repoId: 2,
    repoRelativePath: "Fare/src/fare_calc.c",
    startLine: 651,
    endLine: 651,
    selectedCode: "if (trans_info_ptr->is_climate_init == CLIMATE_CLEAR_PENALTY)",
    enclosingSymbol: "fare_is_xfer",
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.repo_id, 2);
  assert.equal(body.repo_id_hint, 2);
  assert.equal(body.repo_relative_path, "Fare/src/fare_calc.c");
});

test("buildSelectionRequest falls back to file_path when relative path missing", () => {
  const { body } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "Fare/src/fare_calc.c",
    startLine: 651,
    endLine: 651,
    selectedCode: "if (x)",
    enclosingSymbol: "fare_is_xfer",
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.file_path, "Fare/src/fare_calc.c");
  assert.equal("repo_id" in body, false);
});

test("buildSelectionRequest defaults revision to HEAD when omitted", () => {
  const { body } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "Fare/src/fare_calc.c",
    repoId: 1,
    repoRelativePath: "Fare/src/fare_calc.c",
    startLine: 10,
    endLine: 12,
    selectedCode: "x = 1;",
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.revision, "HEAD");
  assert.equal("enclosing_symbol" in body, false);
});

test("buildSelectionRequest truncates overly long selections and reports it", () => {
  const long = "x".repeat(5000);
  const { body, truncated, debug } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "Fare/src/fare_calc.c",
    repoId: 1,
    repoRelativePath: "Fare/src/fare_calc.c",
    startLine: 1,
    endLine: 200,
    selectedCode: long,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(truncated, true);
  assert.equal(body.selected_code.length, 4000);
  assert.equal(debug.selected_text_chars, 5000);
  assert.equal(debug.selected_code_sent_chars, 4000);
});

test("buildSelectionRequest debug info never carries the raw selected code text", () => {
  const { debug } = buildSelectionRequest({
    equipmentId: 1,
    filePath: "Fare/src/fare_calc.c",
    repoId: 1,
    repoRelativePath: "Fare/src/fare_calc.c",
    startLine: 651,
    endLine: 651,
    selectedCode: "if (trans_info_ptr->is_climate_init == CLIMATE_CLEAR_PENALTY)",
    enclosingSymbol: "fare_is_xfer",
    maxSelectedCodeChars: 4000,
  });
  assert.equal((debug as unknown as Record<string, unknown>).selected_code, undefined);
  assert.equal((debug as unknown as Record<string, unknown>).selected_text, undefined);
});

test("capture-before-input flow: buildAnalyzeRequest uses pre-captured selectedText not post-await editor", () => {
  // Simulates: user selected test_Alias, InputBox opened (selection cleared in editor),
  // but extension already captured selectedText before await.
  const capturedSelectedText = "test_Alias";
  const { body } = buildAnalyzeRequest({
    equipmentId: 7,
    query: "이 함수 언제 추가되었어?",
    filePath: "card_sc_tm.c",
    selectedCode: capturedSelectedText,
    detectedSymbol: "test_Alias",
    sourceMode: "recent_selection_fallback",
    useOllama: false,
    maxSelectedCodeChars: 4000,
  });
  assert.equal(body.selected_code, "test_Alias");
  assert.match(body.query, /test_Alias/);
});
