/**
 * Remembers the most recent non-empty editor selection per document so that
 * a context-menu click (which often clears editor.selection before the command
 * handler runs) can still recover what the user had selected.
 */

import * as vscode from "vscode";

const RECENT_SELECTION_TTL_MS = 10_000;

interface RecentSelection {
  documentUri: string;
  text: string;
  timestamp: number;
}

let lastNonEmptySelection: RecentSelection | null = null;

export function registerSelectionTracker(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.window.onDidChangeTextEditorSelection((event) => {
      const selection = event.selections[0];
      if (!selection || selection.isEmpty) {
        return;
      }
      const text = event.textEditor.document.getText(selection);
      if (!text.trim()) {
        return;
      }
      lastNonEmptySelection = {
        documentUri: event.textEditor.document.uri.toString(),
        text,
        timestamp: Date.now(),
      };
    })
  );
}

/** Same-document non-empty selection captured within the last 10 seconds. */
export function getRecentSelectionFallback(documentUri: string): string | undefined {
  if (!lastNonEmptySelection) {
    return undefined;
  }
  if (lastNonEmptySelection.documentUri !== documentUri) {
    return undefined;
  }
  if (Date.now() - lastNonEmptySelection.timestamp > RECENT_SELECTION_TTL_MS) {
    return undefined;
  }
  return lastNonEmptySelection.text;
}

/** Test-only reset. */
export function _resetSelectionTrackerForTest(): void {
  lastNonEmptySelection = null;
}
