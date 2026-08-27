package com.atec.sourcetrace.eclipse.core;

import java.util.ArrayList;
import java.util.List;

/**
 * Parses FastAPI/Pydantic 422 {@code detail} arrays into short UI messages.
 */
public final class FastApiErrorParser {

	public static final class DetailItem {
		public final String type;
		public final String loc;
		public final String msg;

		public DetailItem(String type, String loc, String msg) {
			this.type = type;
			this.loc = loc;
			this.msg = msg;
		}
	}

	private FastApiErrorParser() {
	}

	public static List<DetailItem> parseDetail(String responseBody) {
		List<DetailItem> out = new ArrayList<>();
		if (responseBody == null || responseBody.isBlank()) {
			return out;
		}
		String trimmed = responseBody.trim();
		// Prefer {"detail":[...]} wrapper; else raw array.
		String arrayJson = trimmed;
		if (trimmed.startsWith("{")) {
			int detailIdx = trimmed.indexOf("\"detail\"");
			if (detailIdx >= 0) {
				int bracket = trimmed.indexOf('[', detailIdx);
				if (bracket >= 0) {
					arrayJson = extractArray(trimmed, bracket);
				}
			}
		}
		if (!arrayJson.startsWith("[")) {
			return out;
		}
		for (String obj : JsonUtil.getObjectArrayItems("{\"items\":" + arrayJson + "}", "items")) {
			String type = JsonUtil.getStringField(obj, "type");
			String msg = JsonUtil.getStringField(obj, "msg");
			String loc = formatLoc(obj);
			out.add(new DetailItem(type, loc, msg));
		}
		// Fallback: scan objects directly from array
		if (out.isEmpty()) {
			for (String obj : JsonUtil.getObjectArrayItems(arrayJson, null)) {
				String type = JsonUtil.getStringField(obj, "type");
				String msg = JsonUtil.getStringField(obj, "msg");
				String loc = formatLoc(obj);
				if (type != null || msg != null) {
					out.add(new DetailItem(type, loc, msg));
				}
			}
		}
		return out;
	}

	private static String extractArray(String json, int startBracket) {
		int depth = 0;
		boolean inString = false;
		boolean escape = false;
		for (int i = startBracket; i < json.length(); i++) {
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
			} else if (c == '[') {
				depth++;
			} else if (c == ']') {
				depth--;
				if (depth == 0) {
					return json.substring(startBracket, i + 1);
				}
			}
		}
		return json.substring(startBracket);
	}

	private static String formatLoc(String obj) {
		// loc is typically ["body","equipment_id"] — extract quoted segments after "loc"
		int locIdx = obj.indexOf("\"loc\"");
		if (locIdx < 0) {
			return "";
		}
		int arr = obj.indexOf('[', locIdx);
		if (arr < 0) {
			return "";
		}
		String arrText = extractArray(obj, arr);
		List<String> parts = new ArrayList<>();
		StringBuilder cur = new StringBuilder();
		boolean inString = false;
		boolean escape = false;
		for (int i = 0; i < arrText.length(); i++) {
			char c = arrText.charAt(i);
			if (inString) {
				if (escape) {
					cur.append(c);
					escape = false;
				} else if (c == '\\') {
					escape = true;
				} else if (c == '"') {
					inString = false;
					parts.add(cur.toString());
					cur.setLength(0);
				} else {
					cur.append(c);
				}
			} else if (c == '"') {
				inString = true;
			}
		}
		if (parts.isEmpty()) {
			return arrText;
		}
		return String.join(".", parts);
	}

	/** Short multi-line message for dialogs. */
	public static String formatUserMessage(String action, int httpStatus, String responseBody) {
		List<DetailItem> items = parseDetail(responseBody);
		StringBuilder b = new StringBuilder();
		b.append(action).append("에 실패했습니다. (HTTP ").append(httpStatus).append(")\n\n");
		if (items.isEmpty()) {
			b.append("서버가 요청을 거부했습니다.");
			if (responseBody != null && !responseBody.isBlank()) {
				String preview = responseBody.length() > 200 ? responseBody.substring(0, 200) + "…" : responseBody;
				b.append("\n").append(preview);
			}
			return b.toString();
		}
		boolean bodyMissing = items.stream().anyMatch(i ->
				"missing".equals(i.type) && (i.loc == null || i.loc.equals("body") || i.loc.isEmpty()));
		if (bodyMissing) {
			b.append("요청 본문(JSON body)이 서버에 전달되지 않았습니다.\n");
		} else {
			b.append("요청 데이터가 서버 형식과 맞지 않습니다.\n");
		}
		b.append("상세:");
		for (DetailItem i : items) {
			b.append("\n- ");
			if (i.loc != null && !i.loc.isEmpty()) {
				b.append(i.loc);
				if (i.msg != null && !i.msg.isEmpty()) {
					b.append(" — ").append(i.msg);
				}
			} else if (i.msg != null) {
				b.append(i.msg);
			} else {
				b.append(String.valueOf(i.type));
			}
		}
		return b.toString();
	}
}
