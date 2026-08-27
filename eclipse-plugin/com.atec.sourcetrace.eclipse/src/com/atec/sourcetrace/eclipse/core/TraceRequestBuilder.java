package com.atec.sourcetrace.eclipse.core;

import java.util.Map;

/**
 * Builds request JSON for Backend v2.6 contracts — mirrors
 * vscode-extension {@code requestBuilder.ts}.
 */
public final class TraceRequestBuilder {

	public static final int DEFAULT_MAX_SELECTED_CHARS = 4000;
	public static final String DEFAULT_QUERY = "선택한 코드가 왜 변경됐는지 알려줘";

	public static final class TruncateResult {
		public final String code;
		public final boolean truncated;

		public TruncateResult(String code, boolean truncated) {
			this.code = code;
			this.truncated = truncated;
		}
	}

	public static final class BuiltRequest {
		public final String jsonBody;
		public final boolean truncated;

		public BuiltRequest(String jsonBody, boolean truncated) {
			this.jsonBody = jsonBody;
			this.truncated = truncated;
		}
	}

	private TraceRequestBuilder() {
	}

	public static TruncateResult truncateSelectedCode(String code, int maxChars) {
		if (code == null) {
			return new TruncateResult("", false);
		}
		if (code.length() <= maxChars) {
			return new TruncateResult(code, false);
		}
		return new TruncateResult(code.substring(0, maxChars), true);
	}

	public static BuiltRequest buildReportRequest(
			int equipmentId,
			String query,
			String filePath,
			String selectedCode,
			String detectedSymbol,
			String sourceMode,
			boolean useOllama,
			int maxSelectedCodeChars) {
		String selectedText = selectedCode == null ? "" : selectedCode.trim();
		String symbol = detectedSymbol == null ? null : detectedSymbol.trim();
		if (symbol != null && symbol.isEmpty()) {
			symbol = null;
		}
		String selectedForBody = !selectedText.isEmpty() ? selectedText
				: (symbol != null ? symbol : "");
		String augmentedQuery = SymbolExtractor.augmentQueryWithSymbol(
				query == null || query.trim().isEmpty() ? DEFAULT_QUERY : query.trim(),
				symbol);
		TruncateResult sent = truncateSelectedCode(selectedForBody, maxSelectedCodeChars);

		Map<String, Object> body = JsonUtil.mapOf();
		body.put("equipment_id", Integer.valueOf(equipmentId));
		body.put("query", augmentedQuery);
		body.put("file_path", filePath);
		body.put("selected_code", sent.code);
		body.put("use_ollama", Boolean.valueOf(useOllama));
		if (sourceMode != null && !sourceMode.isEmpty()) {
			body.put("source_mode", sourceMode);
		}
		if (symbol != null) {
			body.put("detected_symbol", symbol);
		}
		String json = JsonUtil.object(body);
		if (json == null || json.isBlank() || "{}".equals(json.trim())) {
			throw new IllegalStateException("report request body가 비어 있습니다.");
		}
		if (!json.contains("\"equipment_id\"")) {
			throw new IllegalStateException("report request에 equipment_id가 없습니다.");
		}
		return new BuiltRequest(json, sent.truncated);
	}

	public static BuiltRequest buildSelectionRequest(
			int equipmentId,
			String repoRelativePath,
			Integer repoIdHint,
			String clientFilePath,
			int startLine,
			int endLine,
			String selectedCode,
			String enclosingSymbol,
			int maxSelectedCodeChars,
			String revision) {
		TruncateResult sent = truncateSelectedCode(
				selectedCode == null ? "" : selectedCode,
				maxSelectedCodeChars);
		Map<String, Object> body = JsonUtil.mapOf();
		body.put("equipment_id", Integer.valueOf(equipmentId));
		body.put("start_line", Integer.valueOf(startLine));
		body.put("end_line", Integer.valueOf(endLine));
		body.put("selected_code", sent.code);
		body.put("revision", revision == null || revision.trim().isEmpty() ? "HEAD" : revision.trim());
		if (enclosingSymbol != null && !enclosingSymbol.trim().isEmpty()) {
			body.put("enclosing_symbol", enclosingSymbol.trim());
		}
		String rel = repoRelativePath == null ? "" : repoRelativePath.trim().replace('\\', '/');
		if (!rel.isEmpty()) {
			body.put("repo_relative_path", rel);
			if (repoIdHint != null && repoIdHint.intValue() > 0) {
				body.put("repo_id", repoIdHint);
				body.put("repo_id_hint", repoIdHint);
			}
			if (clientFilePath != null && !clientFilePath.trim().isEmpty()) {
				body.put("client_file_path", clientFilePath);
			}
		} else if (clientFilePath != null && !clientFilePath.trim().isEmpty()) {
			body.put("file_path", clientFilePath);
		}
		return new BuiltRequest(JsonUtil.object(body), sent.truncated);
	}

	/** Prefer Backend Markdown fields in the same order as VS Code pickResultMarkdown. */
	public static String pickResultMarkdown(String responseJson) {
		if (responseJson == null || responseJson.trim().isEmpty()) {
			return "(빈 응답)";
		}
		for (String key : new String[] { "content", "answer", "evidence_answer" }) {
			String value = JsonUtil.getStringField(responseJson, key);
			if (value != null && !value.trim().isEmpty()) {
				return value;
			}
		}
		return "```json\n" + responseJson + "\n```";
	}

	public static boolean looksLikeAmbiguity(String messageOrBody) {
		if (messageOrBody == null) {
			return false;
		}
		String m = messageOrBody;
		return m.contains("여러 장비 Repository")
				|| m.contains("AMBIGUOUS")
				|| m.contains("하나를 결정할 수 없")
				|| m.contains("동일한 파일 경로가 여러");
	}
}
