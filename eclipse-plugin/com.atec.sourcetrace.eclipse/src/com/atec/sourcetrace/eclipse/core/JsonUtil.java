package com.atec.sourcetrace.eclipse.core;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Minimal JSON encode/decode for Source Trace request/response shapes.
 * Avoids third-party JSON libraries in the Eclipse plug-in classpath.
 */
public final class JsonUtil {

	private JsonUtil() {
	}

	public static String quote(String s) {
		if (s == null) {
			return "null";
		}
		StringBuilder b = new StringBuilder("\"");
		for (int i = 0; i < s.length(); i++) {
			char c = s.charAt(i);
			switch (c) {
			case '\\':
				b.append("\\\\");
				break;
			case '"':
				b.append("\\\"");
				break;
			case '\n':
				b.append("\\n");
				break;
			case '\r':
				b.append("\\r");
				break;
			case '\t':
				b.append("\\t");
				break;
			default:
				if (c < 0x20) {
					b.append(String.format("\\u%04x", (int) c));
				} else {
					b.append(c);
				}
			}
		}
		b.append('"');
		return b.toString();
	}

	public static String object(Map<String, Object> fields) {
		StringBuilder b = new StringBuilder("{");
		boolean first = true;
		for (Map.Entry<String, Object> e : fields.entrySet()) {
			if (e.getValue() == null) {
				continue;
			}
			if (!first) {
				b.append(',');
			}
			first = false;
			b.append(quote(e.getKey())).append(':');
			Object v = e.getValue();
			if (v instanceof String) {
				b.append(quote((String) v));
			} else if (v instanceof Number || v instanceof Boolean) {
				b.append(v.toString());
			} else {
				b.append(quote(String.valueOf(v)));
			}
		}
		b.append('}');
		return b.toString();
	}

	/** Extract a top-level string field (handles escaped strings). */
	public static String getStringField(String json, String field) {
		if (json == null || field == null) {
			return null;
		}
		String key = "\"" + field + "\"";
		int idx = json.indexOf(key);
		if (idx < 0) {
			return null;
		}
		int colon = json.indexOf(':', idx + key.length());
		if (colon < 0) {
			return null;
		}
		int i = colon + 1;
		while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
			i++;
		}
		if (i >= json.length()) {
			return null;
		}
		if (json.startsWith("null", i)) {
			return null;
		}
		if (json.charAt(i) != '"') {
			// non-string — return raw token until comma/brace
			int end = i;
			while (end < json.length()) {
				char c = json.charAt(end);
				if (c == ',' || c == '}' || c == ']') {
					break;
				}
				end++;
			}
			return json.substring(i, end).trim();
		}
		return parseQuoted(json, i);
	}

	public static Integer getIntField(String json, String field) {
		String raw = getStringField(json, field);
		if (raw == null) {
			return null;
		}
		try {
			return Integer.valueOf(raw.trim());
		} catch (NumberFormatException e) {
			return null;
		}
	}

	/** Parse a JSON array of objects into raw object substrings (best-effort). */
	public static List<String> getObjectArrayItems(String json, String field) {
		List<String> out = new ArrayList<>();
		if (json == null) {
			return out;
		}
		String key = "\"" + field + "\"";
		int idx = json.indexOf(key);
		if (idx < 0) {
			// root array
			idx = json.indexOf('[');
			if (idx < 0) {
				return out;
			}
		} else {
			idx = json.indexOf('[', idx);
			if (idx < 0) {
				return out;
			}
		}
		int depth = 0;
		int start = -1;
		boolean inString = false;
		boolean escape = false;
		for (int i = idx; i < json.length(); i++) {
			char c = json.charAt(i);
			if (inString) {
				if (escape) {
					escape = false;
				} else if (c == '\\') {
					escape = true;
				} else if (c == '"') {
					inString = false;
				}
				continue;
			}
			if (c == '"') {
				inString = true;
				continue;
			}
			if (c == '{') {
				if (depth == 1) {
					start = i;
				}
				depth++;
			} else if (c == '}') {
				depth--;
				if (depth == 1 && start >= 0) {
					out.add(json.substring(start, i + 1));
					start = -1;
				}
			} else if (c == '[') {
				depth++;
			} else if (c == ']') {
				depth--;
				if (depth == 0) {
					break;
				}
			}
		}
		return out;
	}

	private static String parseQuoted(String json, int startQuote) {
		StringBuilder b = new StringBuilder();
		boolean escape = false;
		for (int i = startQuote + 1; i < json.length(); i++) {
			char c = json.charAt(i);
			if (escape) {
				switch (c) {
				case 'n':
					b.append('\n');
					break;
				case 'r':
					b.append('\r');
					break;
				case 't':
					b.append('\t');
					break;
				case 'u':
					if (i + 4 < json.length()) {
						String hex = json.substring(i + 1, i + 5);
						b.append((char) Integer.parseInt(hex, 16));
						i += 4;
					}
					break;
				default:
					b.append(c);
				}
				escape = false;
				continue;
			}
			if (c == '\\') {
				escape = true;
			} else if (c == '"') {
				return b.toString();
			} else {
				b.append(c);
			}
		}
		return b.toString();
	}

	public static Map<String, Object> mapOf() {
		return new LinkedHashMap<>();
	}
}
