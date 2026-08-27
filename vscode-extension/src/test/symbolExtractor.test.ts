import { test } from "node:test";
import assert from "node:assert/strict";

import {
  augmentQueryWithSymbol,
  extractDetectedSymbol,
  findEnclosingFunctionSymbol,
} from "../symbolExtractor";

test("extractDetectedSymbol from single identifier test_Alias", () => {
  assert.equal(extractDetectedSymbol("test_Alias"), "test_Alias");
});

test("extractDetectedSymbol from void test_Alias() declaration", () => {
  assert.equal(extractDetectedSymbol("void test_Alias()"), "test_Alias");
});

test("extractDetectedSymbol from function call site", () => {
  assert.equal(
    extractDetectedSymbol("trans_write_climatecard_data(card_decode_data_ptr, ...)"),
    "trans_write_climatecard_data"
  );
});

test("extractDetectedSymbol ignores C keyword void as sole token", () => {
  assert.equal(extractDetectedSymbol("void"), undefined);
});

test("augmentQueryWithSymbol replaces 이 함수 with symbol", () => {
  const q = augmentQueryWithSymbol("이 함수 언제 추가되었어?", "test_Alias");
  assert.equal(q, "test_Alias 함수 언제 추가되었어?");
  assert.match(q, /test_Alias/);
});

test("augmentQueryWithSymbol does not duplicate symbol already in query", () => {
  const q = augmentQueryWithSymbol("test_Alias 변경 이력", "test_Alias");
  assert.equal(q, "test_Alias 변경 이력");
});

test("augmentQueryWithSymbol prefixes symbol for generic question", () => {
  const q = augmentQueryWithSymbol("변경 이력 알려줘", "test_Alias");
  assert.equal(q, "test_Alias 변경 이력 알려줘");
});

// PROJECT_SPEC v2.4 §4 — 선택 코드 변경 근거 조회의 "포함 함수" 탐지.
const SAMPLE_C_SOURCE = [
  /* 0 */ "/* header */",
  /* 1 */ "bool example_check_condition(TRANS_INFO *trans_info_ptr)",
  /* 2 */ "{",
  /* 3 */ "    word prev_station_id = 0;",
  /* 4 */ "",
  /* 5 */ "    if (trans_info_ptr->flag == true) {",
  /* 6 */ "        if (trans_info_ptr->is_climate_init == CLEAR_PENALTY) {",
  /* 7 */ "            return false;",
  /* 8 */ "        }",
  /* 9 */ "    }",
  /* 10 */ "    return true;",
  /* 11 */ "}",
  /* 12 */ "",
  /* 13 */ "int other_function(int a)",
  /* 14 */ "{",
  /* 15 */ "    return a + 1;",
  /* 16 */ "}",
];

test("findEnclosingFunctionSymbol finds the function enclosing a nested if-condition", () => {
  const symbol = findEnclosingFunctionSymbol(SAMPLE_C_SOURCE, 6);
  assert.equal(symbol, "example_check_condition");
});

test("findEnclosingFunctionSymbol resolves the correct function for a later definition", () => {
  const symbol = findEnclosingFunctionSymbol(SAMPLE_C_SOURCE, 15);
  assert.equal(symbol, "other_function");
});

test("findEnclosingFunctionSymbol returns undefined outside any function", () => {
  const symbol = findEnclosingFunctionSymbol(SAMPLE_C_SOURCE, 0);
  assert.equal(symbol, undefined);
});

test("findEnclosingFunctionSymbol returns undefined for an empty document", () => {
  assert.equal(findEnclosingFunctionSymbol([], 0), undefined);
});
