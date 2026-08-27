package com.atec.sourcetrace.eclipse.core;

/**
 * Very small Markdown → HTML for Eclipse Browser widget (offline, no CDN).
 * Preserves Backend wording; does not reinterpret Commit/PPT facts.
 */
public final class MarkdownHtml {

	private MarkdownHtml() {
	}

	public static String toHtmlDocument(String markdown, String title) {
		String body = toHtmlBody(markdown == null ? "" : markdown);
		String safeTitle = escape(title == null ? "ATEC Source Trace" : title);
		return "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/><title>"
				+ safeTitle
				+ "</title><style>"
				+ "body{font-family:Consolas,'Malgun Gothic',sans-serif;font-size:13px;"
				+ "line-height:1.45;padding:12px;color:#1a1a1a;background:#fafafa;}"
				+ "pre,code{font-family:Consolas,monospace;background:#f0f0f0;}"
				+ "pre{padding:8px;overflow:auto;border:1px solid #ddd;}"
				+ "table{border-collapse:collapse;margin:8px 0;}"
				+ "th,td{border:1px solid #ccc;padding:4px 8px;vertical-align:top;}"
				+ "h1,h2,h3{margin:12px 0 6px;}"
				+ "hr{border:none;border-top:1px solid #ccc;margin:12px 0;}"
				+ "details{margin:8px 0;}"
				+ "</style></head><body>"
				+ body
				+ "</body></html>";
	}

	static String toHtmlBody(String md) {
		String[] lines = md.replace("\r\n", "\n").replace('\r', '\n').split("\n", -1);
		StringBuilder out = new StringBuilder();
		boolean inCode = false;
		boolean inTable = false;
		StringBuilder code = new StringBuilder();
		for (int i = 0; i < lines.length; i++) {
			String line = lines[i];
			if (line.startsWith("```")) {
				if (inCode) {
					out.append("<pre><code>").append(escape(code.toString())).append("</code></pre>\n");
					code.setLength(0);
					inCode = false;
				} else {
					if (inTable) {
						out.append("</table>\n");
						inTable = false;
					}
					inCode = true;
				}
				continue;
			}
			if (inCode) {
				if (code.length() > 0) {
					code.append('\n');
				}
				code.append(line);
				continue;
			}
			if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
				if (isTableSep(line)) {
					continue;
				}
				if (!inTable) {
					out.append("<table>\n");
					inTable = true;
				}
				out.append("<tr>");
				String[] cells = line.trim().substring(1, line.trim().length() - 1).split("\\|", -1);
				for (String cell : cells) {
					out.append("<td>").append(inline(cell.trim())).append("</td>");
				}
				out.append("</tr>\n");
				continue;
			} else if (inTable) {
				out.append("</table>\n");
				inTable = false;
			}
			if (line.startsWith("# ")) {
				out.append("<h1>").append(inline(line.substring(2))).append("</h1>\n");
			} else if (line.startsWith("## ")) {
				out.append("<h2>").append(inline(line.substring(3))).append("</h2>\n");
			} else if (line.startsWith("### ")) {
				out.append("<h3>").append(inline(line.substring(4))).append("</h3>\n");
			} else if (line.trim().equals("---")) {
				out.append("<hr/>\n");
			} else if (line.trim().isEmpty()) {
				out.append("<br/>\n");
			} else {
				out.append("<p>").append(inline(line)).append("</p>\n");
			}
		}
		if (inCode) {
			out.append("<pre><code>").append(escape(code.toString())).append("</code></pre>\n");
		}
		if (inTable) {
			out.append("</table>\n");
		}
		return out.toString();
	}

	private static boolean isTableSep(String line) {
		String t = line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "");
		return t.isEmpty();
	}

	private static String inline(String s) {
		String e = escape(s);
		e = e.replaceAll("`([^`]+)`", "<code>$1</code>");
		e = e.replaceAll("\\*\\*([^*]+)\\*\\*", "<strong>$1</strong>");
		return e;
	}

	public static String escape(String s) {
		if (s == null) {
			return "";
		}
		return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
	}
}
