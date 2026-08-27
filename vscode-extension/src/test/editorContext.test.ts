import { test } from "node:test";
import assert from "node:assert/strict";

import { resolveEditorContext, basenameFromPath } from "../editorContext";

test("resolveEditorContext uses immediate selection before recent fallback", () => {
  const r = resolveEditorContext({
    immediateSelectionText: "test_Alias",
    recentSelectionText: "other_func",
  });
  assert.equal(r?.selectedText, "test_Alias");
  assert.equal(r?.sourceMode, "selection_symbol");
  assert.equal(r?.detectedSymbol, "test_Alias");
});

test("resolveEditorContext falls back to recent selection within same document", () => {
  const r = resolveEditorContext({
    immediateSelectionText: "",
    recentSelectionText: "test_Alias",
  });
  assert.equal(r?.selectedText, "test_Alias");
  assert.equal(r?.sourceMode, "recent_selection_fallback");
  assert.equal(r?.detectedSymbol, "test_Alias");
});

test("resolveEditorContext uses cursor word when selection empty", () => {
  const r = resolveEditorContext({
    immediateSelectionText: "",
    cursorWord: "card_sc_check_valid",
  });
  assert.equal(r?.sourceMode, "cursor_word");
  assert.equal(r?.detectedSymbol, "card_sc_check_valid");
  assert.equal(r?.selectedText, "card_sc_check_valid");
});

test("resolveEditorContext returns null when nothing usable", () => {
  const r = resolveEditorContext({
    immediateSelectionText: "",
    recentSelectionText: "",
    cursorWord: "",
    currentLineText: "   ",
  });
  assert.equal(r, null);
});

test("resolveEditorContext multi-line selection keeps full text and extracts symbol", () => {
  const r = resolveEditorContext({
    immediateSelectionText: "void test_Alias(void)\n{\n}",
  });
  assert.equal(r?.sourceMode, "selection");
  assert.equal(r?.detectedSymbol, "test_Alias");
  assert.match(r?.selectedText ?? "", /void test_Alias/);
});

test("basenameFromPath handles Windows and POSIX paths", () => {
  assert.equal(basenameFromPath("C:\\workspace\\card_sc_tm.c"), "card_sc_tm.c");
  assert.equal(basenameFromPath("/workspace/card/sc_kscc/src/card_sc_tm.c"), "card_sc_tm.c");
});
