package com.atec.sourcetrace.eclipse.core;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * HTTP client for Backend v2.6 using {@link HttpURLConnection}.
 * <p>
 * Uses fixed-length POST bodies and explicit {@code Content-Type: application/json}
 * so FastAPI receives a real JSON body (empty/missing body → HTTP 422
 * {@code type=missing, loc=["body"]}).
 */
public final class TraceHttpClient {

	public static final class HttpResult {
		public final int status;
		public final String body;
		public final String error;

		public HttpResult(int status, String body, String error) {
			this.status = status;
			this.body = body;
			this.error = error;
		}

		public boolean ok() {
			return error == null && status >= 200 && status < 300;
		}
	}

	public static final class EquipmentItem {
		public final int id;
		public final String name;

		public EquipmentItem(int id, String name) {
			this.id = id;
			this.name = name;
		}

		@Override
		public String toString() {
			return name + " (ID " + id + ")";
		}
	}

	public static final class RepoItem {
		public final int id;
		public final String name;
		public final String status;

		public RepoItem(int id, String name, String status) {
			this.id = id;
			this.name = name;
			this.status = status;
		}

		@Override
		public String toString() {
			return name + " (#" + id + ")" + (status != null ? " [" + status + "]" : "");
		}
	}

	private final int timeoutMs;

	public TraceHttpClient(Duration timeout) {
		Duration t = timeout == null ? Duration.ofSeconds(180) : timeout;
		this.timeoutMs = (int) Math.min(Integer.MAX_VALUE, Math.max(1000, t.toMillis()));
	}

	public TraceHttpClient() {
		this(Duration.ofSeconds(180));
	}

	public HttpResult get(String url) {
		HttpURLConnection conn = null;
		try {
			conn = open(url, "GET", false);
			conn.setRequestProperty("Accept", "application/json");
			int status = conn.getResponseCode();
			String body = readBody(conn, status);
			return new HttpResult(status, body, null);
		} catch (Exception e) {
			return new HttpResult(-1, null, e.getMessage() == null ? e.toString() : e.getMessage());
		} finally {
			if (conn != null) {
				conn.disconnect();
			}
		}
	}

	public HttpResult postJson(String url, String jsonBody) {
		HttpURLConnection conn = null;
		try {
			String payload = normalizeJsonBody(jsonBody);
			byte[] bytes = payload.getBytes(StandardCharsets.UTF_8);
			conn = open(url, "POST", true);
			conn.setRequestProperty("Accept", "application/json");
			conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
			conn.setFixedLengthStreamingMode(bytes.length);
			try (OutputStream os = conn.getOutputStream()) {
				os.write(bytes);
				os.flush();
			}
			int status = conn.getResponseCode();
			String body = readBody(conn, status);
			return new HttpResult(status, body, null);
		} catch (Exception e) {
			return new HttpResult(-1, null, e.getMessage() == null ? e.toString() : e.getMessage());
		} finally {
			if (conn != null) {
				conn.disconnect();
			}
		}
	}

	/** Never send blank — FastAPI treats missing/empty body as 422 body required. */
	public static String normalizeJsonBody(String jsonBody) {
		if (jsonBody == null || jsonBody.isBlank()) {
			return "{}";
		}
		return jsonBody;
	}

	private HttpURLConnection open(String url, String method, boolean doOutput) throws Exception {
		URL u = URI.create(url).toURL();
		HttpURLConnection conn = (HttpURLConnection) u.openConnection();
		conn.setConnectTimeout(Math.min(timeoutMs, 15_000));
		conn.setReadTimeout(timeoutMs);
		conn.setInstanceFollowRedirects(false);
		conn.setRequestMethod(method);
		conn.setDoInput(true);
		conn.setDoOutput(doOutput);
		conn.setUseCaches(false);
		return conn;
	}

	private static String readBody(HttpURLConnection conn, int status) throws Exception {
		InputStream in = status >= 400 ? conn.getErrorStream() : conn.getInputStream();
		if (in == null) {
			in = conn.getInputStream();
		}
		if (in == null) {
			return "";
		}
		try (InputStream stream = in; ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
			byte[] buf = new byte[4096];
			int n;
			while ((n = stream.read(buf)) >= 0) {
				bos.write(buf, 0, n);
			}
			return bos.toString(StandardCharsets.UTF_8);
		}
	}

	public HttpResult health(String serverUrl) {
		return get(ServerUrlUtil.buildApiUrl(serverUrl, ApiPaths.HEALTH));
	}

	public List<EquipmentItem> listEquipment(String serverUrl) throws Exception {
		HttpResult r = get(ServerUrlUtil.buildApiUrl(serverUrl, ApiPaths.EQUIPMENT_LIST));
		if (!r.ok()) {
			throw new Exception(formatHttpError("장비 목록 조회", r));
		}
		List<EquipmentItem> out = new ArrayList<>();
		for (String obj : JsonUtil.getObjectArrayItems(r.body, null)) {
			Integer id = JsonUtil.getIntField(obj, "id");
			String name = JsonUtil.getStringField(obj, "name");
			if (id != null) {
				out.add(new EquipmentItem(id.intValue(), name == null ? "" : name));
			}
		}
		return out;
	}

	public List<RepoItem> listRepositories(String serverUrl, int equipmentId) throws Exception {
		HttpResult r = get(ServerUrlUtil.buildApiUrl(serverUrl, ApiPaths.equipmentRepositories(equipmentId)));
		if (!r.ok()) {
			throw new Exception(formatHttpError("Repository 목록 조회", r));
		}
		List<RepoItem> out = new ArrayList<>();
		for (String obj : JsonUtil.getObjectArrayItems(r.body, null)) {
			Integer id = JsonUtil.getIntField(obj, "id");
			String name = JsonUtil.getStringField(obj, "name");
			String status = JsonUtil.getStringField(obj, "status");
			if (id != null) {
				out.add(new RepoItem(id.intValue(), name == null ? "" : name, status));
			}
		}
		return out;
	}

	public HttpResult postReport(String serverUrl, String jsonBody) {
		return postJson(ServerUrlUtil.buildApiUrl(serverUrl, ApiPaths.TRACE_REPORT), jsonBody);
	}

	public HttpResult postSelection(String serverUrl, String jsonBody) {
		return postJson(ServerUrlUtil.buildApiUrl(serverUrl, ApiPaths.TRACE_SELECTION), jsonBody);
	}

	public static String formatHttpError(String action, HttpResult r) {
		if (r.error != null) {
			return action + " 실패: 서버에 연결할 수 없습니다. (" + r.error + ")";
		}
		if (r.status == 422) {
			return FastApiErrorParser.formatUserMessage(action, r.status, r.body);
		}
		String detail = r.body == null ? "" : r.body;
		String msg = JsonUtil.getStringField(detail, "detail");
		if (msg == null || msg.isEmpty()) {
			msg = JsonUtil.getStringField(detail, "content");
		}
		if (msg == null || msg.isEmpty()) {
			msg = detail.length() > 300 ? detail.substring(0, 300) : detail;
		}
		return action + "에 실패했습니다. (HTTP " + r.status + ")\n" + msg;
	}

	public static String userFacingConnectionError(String detail) {
		return "Backend 서버에 연결할 수 없습니다. Source Trace 서버 URL 설정을 확인하세요."
				+ (detail != null && !detail.isEmpty() ? "\n원인: " + detail : "");
	}
}
