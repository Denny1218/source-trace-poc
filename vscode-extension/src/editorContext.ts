/**
 * Pure selection-resolution logic (no VS Code API).
 * Used by extension.ts and unit-tested without @vscode/test-electron.
 */

import { extractDetectedSymbol } from "./symbolExtractor";

export type SourceMode =
  | "selection"
  | "selection_symbol"
  | "cursor_word"
  | "recent_selection_fallback"
  | "none";

export interface ResolveSelectionInput {
  /** editor.document.getText(editor.selection) at command entry — before any await. */
  immediateSelectionText: string;
  /** Same-document non-empty selection from onDidChangeTextEditorSelection (≤10s). */
  recentSelectionText?: string;
  /** editor.document.getWordRangeAtPosition cursor word. */
  cursorWord?: string;
  /** Full text of the line at the cursor (debug / last-resort selected_code). */
  currentLineText?: string;
}

export interface ResolvedEditorContext {
  selectedText: string;
  sourceMode: SourceMode;
  detectedSymbol?: string;
}

function resolveFromText(
  text: string,
  baseMode: "selection" | "recent_selection_fallback"
): ResolvedEditorContext {
  const trimmed = text.trim();
  const symbol = extractDetectedSymbol(trimmed);
  const isSingleSymbol = symbol !== undefined && trimmed === symbol;
  return {
    selectedText: trimmed,
    sourceMode: isSingleSymbol ? "selection_symbol" : baseMode,
    detectedSymbol: symbol,
  };
}

/**
 * Pick the best available editor context using immediate selection, recent
 * selection fallback, then cursor word — never the whole file.
 */
export function resolveEditorContext(
  input: ResolveSelectionInput
): ResolvedEditorContext | null {
  const immediate = (input.immediateSelectionText ?? "").trim();
  if (immediate) {
    return resolveFromText(immediate, "selection");
  }

  const recent = (input.recentSelectionText ?? "").trim();
  if (recent) {
    const resolved = resolveFromText(recent, "recent_selection_fallback");
    return { ...resolved, sourceMode: "recent_selection_fallback" };
  }

  const word = (input.cursorWord ?? "").trim();
  if (word && extractDetectedSymbol(word)) {
    return {
      selectedText: word,
      sourceMode: "cursor_word",
      detectedSymbol: word,
    };
  }

  const line = (input.currentLineText ?? "").trim();
  if (line) {
    const symbol = extractDetectedSymbol(line);
    if (symbol) {
      return {
        selectedText: line,
        sourceMode: "cursor_word",
        detectedSymbol: symbol,
      };
    }
  }

  return null;
}

/** Basename for debug / title — works with Windows and POSIX paths. */
export function basenameFromPath(filePath: string | undefined): string | undefined {
  const p = (filePath ?? "").trim();
  if (!p) {
    return undefined;
  }
  const parts = p.split(/[/\\]/);
  return parts[parts.length - 1] || undefined;
}
