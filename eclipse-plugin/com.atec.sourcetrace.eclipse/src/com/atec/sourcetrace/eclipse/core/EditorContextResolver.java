package com.atec.sourcetrace.eclipse.core;

/**
 * Port of vscode-extension {@code editorContext.ts} resolveEditorContext.
 */
public final class EditorContextResolver {

	public enum SourceMode {
		SELECTION("selection"),
		SELECTION_SYMBOL("selection_symbol"),
		CURSOR_WORD("cursor_word"),
		RECENT_SELECTION_FALLBACK("recent_selection_fallback"),
		NONE("none");

		public final String wire;

		SourceMode(String wire) {
			this.wire = wire;
		}
	}

	public static final class Resolved {
		public final String selectedText;
		public final SourceMode sourceMode;
		public final String detectedSymbol;

		public Resolved(String selectedText, SourceMode sourceMode, String detectedSymbol) {
			this.selectedText = selectedText;
			this.sourceMode = sourceMode;
			this.detectedSymbol = detectedSymbol;
		}
	}

	private EditorContextResolver() {
	}

	public static Resolved resolve(
			String immediateSelectionText,
			String recentSelectionText,
			String cursorWord,
			String currentLineText) {
		String immediate = trim(immediateSelectionText);
		if (!immediate.isEmpty()) {
			return fromText(immediate, SourceMode.SELECTION);
		}
		String recent = trim(recentSelectionText);
		if (!recent.isEmpty()) {
			Resolved r = fromText(recent, SourceMode.RECENT_SELECTION_FALLBACK);
			return new Resolved(r.selectedText, SourceMode.RECENT_SELECTION_FALLBACK, r.detectedSymbol);
		}
		String word = trim(cursorWord);
		if (!word.isEmpty() && SymbolExtractor.extractDetectedSymbol(word) != null) {
			return new Resolved(word, SourceMode.CURSOR_WORD, word);
		}
		String line = trim(currentLineText);
		if (!line.isEmpty()) {
			String symbol = SymbolExtractor.extractDetectedSymbol(line);
			if (symbol != null) {
				return new Resolved(line, SourceMode.CURSOR_WORD, symbol);
			}
		}
		return null;
	}

	private static Resolved fromText(String text, SourceMode baseMode) {
		String trimmed = text.trim();
		String symbol = SymbolExtractor.extractDetectedSymbol(trimmed);
		boolean isSingleSymbol = symbol != null && trimmed.equals(symbol);
		return new Resolved(
				trimmed,
				isSingleSymbol ? SourceMode.SELECTION_SYMBOL : baseMode,
				symbol);
	}

	private static String trim(String s) {
		return s == null ? "" : s.trim();
	}
}
