package com.atec.sourcetrace.eclipse.core;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Java port of vscode-extension {@code symbolExtractor.ts}. Keep behaviour
 * aligned so the same C source position yields the same Backend symbol.
 */
public final class SymbolExtractor {

	private static final Pattern C_IDENT = Pattern.compile("^[A-Za-z_][A-Za-z0-9_]*$");
	private static final Pattern C_FUNC_DEF = Pattern.compile(
			"(?:\\b(?:static|inline|extern|const|unsigned|signed|volatile)\\s+)*(?:struct\\s+\\w+\\s+)?\\b([A-Za-z_][A-Za-z0-9_]*)\\b[ \\t]*\\*{0,2}[ \\t]*\\(");
	private static final Pattern C_FUNC_CALL = Pattern.compile("\\b([A-Za-z_][A-Za-z0-9_]*)\\s*\\(");
	private static final Pattern CONTROL_BLOCK = Pattern.compile("^\\s*(if|for|while|switch)\\b");

	private static final Set<String> C_KEYWORDS = new HashSet<>(Arrays.asList(
			"if", "else", "for", "while", "do", "switch", "case", "break", "continue", "return", "goto",
			"sizeof", "typedef", "struct", "union", "enum", "static", "extern", "inline", "const",
			"volatile", "unsigned", "signed", "void", "int", "char", "short", "long", "float", "double",
			"bool", "true", "false", "NULL"));

	private SymbolExtractor() {
	}

	public static String extractDetectedSymbol(String selectedText) {
		if (selectedText == null) {
			return null;
		}
		String raw = selectedText.trim();
		if (raw.isEmpty()) {
			return null;
		}
		if (C_IDENT.matcher(raw).matches() && !C_KEYWORDS.contains(raw)) {
			return raw;
		}
		Matcher defMatch = C_FUNC_DEF.matcher(raw);
		if (defMatch.find()) {
			String name = defMatch.group(1);
			if (!C_KEYWORDS.contains(name.toLowerCase(Locale.ROOT))) {
				return name;
			}
		}
		Matcher callMatch = C_FUNC_CALL.matcher(raw);
		while (callMatch.find()) {
			String name = callMatch.group(1);
			if (!C_KEYWORDS.contains(name.toLowerCase(Locale.ROOT))) {
				return name;
			}
		}
		return null;
	}

	/**
	 * @param lines     document lines (0-based index)
	 * @param startLine 0-based line index of selection start
	 */
	public static String findEnclosingFunctionSymbol(String[] lines, int startLine) {
		if (lines == null || lines.length == 0) {
			return null;
		}
		int pendingCloses = 0;
		int start = Math.min(Math.max(startLine, 0), lines.length - 1);
		int limit = Math.max(0, start - 4000);
		for (int i = start; i >= limit; i--) {
			String line = lines[i] != null ? lines[i] : "";
			for (int ci = line.length() - 1; ci >= 0; ci--) {
				char ch = line.charAt(ci);
				if (ch == '}') {
					pendingCloses++;
				} else if (ch == '{') {
					if (pendingCloses > 0) {
						pendingCloses--;
						continue;
					}
					String beforeBrace = line.substring(0, ci);
					String sigText = beforeBrace.trim().isEmpty()
							? findPrecedingNonBlankLine(lines, i)
							: beforeBrace;
					if (sigText == null) {
						sigText = "";
					}
					if (CONTROL_BLOCK.matcher(sigText).find()) {
						continue;
					}
					Matcher match = C_FUNC_DEF.matcher(sigText);
					if (match.find()) {
						String name = match.group(1);
						if (!C_KEYWORDS.contains(name.toLowerCase(Locale.ROOT))) {
							return name;
						}
					}
				}
			}
		}
		return null;
	}

	private static String findPrecedingNonBlankLine(String[] lines, int fromIndex) {
		for (int j = fromIndex - 1; j >= 0 && j >= fromIndex - 5; j--) {
			String candidate = lines[j] != null ? lines[j] : "";
			if (!candidate.trim().isEmpty()) {
				return candidate;
			}
		}
		return null;
	}

	public static String augmentQueryWithSymbol(String query, String symbol) {
		String q = query == null ? "" : query.trim();
		if (symbol == null || symbol.isEmpty() || q.isEmpty()) {
			return q;
		}
		if (q.contains(symbol)) {
			return q;
		}
		String pronounReplaced = q.replaceAll("이\\s*함수", symbol + " 함수");
		if (!pronounReplaced.equals(q)) {
			return pronounReplaced;
		}
		return symbol + " " + q;
	}
}
