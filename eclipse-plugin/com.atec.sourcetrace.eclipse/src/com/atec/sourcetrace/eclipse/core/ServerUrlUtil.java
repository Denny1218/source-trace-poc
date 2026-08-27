package com.atec.sourcetrace.eclipse.core;

import java.net.URI;
import java.net.URISyntaxException;

/**
 * Mirrors vscode-extension {@code serverConfig.ts} normalizeServerUrl /
 * sanitizeUrl behaviour for Source Trace Backend origin only.
 */
public final class ServerUrlUtil {

	private ServerUrlUtil() {
	}

	public static final class NormalizeResult {
		public final boolean ok;
		public final String url;
		public final String error;

		private NormalizeResult(boolean ok, String url, String error) {
			this.ok = ok;
			this.url = url;
			this.error = error;
		}

		public static NormalizeResult success(String url) {
			return new NormalizeResult(true, url, null);
		}

		public static NormalizeResult failure(String error) {
			return new NormalizeResult(false, null, error);
		}
	}

	/** Strip userinfo credentials; return sanitized string. */
	public static String sanitizeUrl(String raw) {
		if (raw == null) {
			return "";
		}
		try {
			URI u = new URI(raw.trim());
			String scheme = u.getScheme();
			String host = u.getHost();
			int port = u.getPort();
			if (scheme == null || host == null) {
				return raw.trim().replaceAll("/$", "");
			}
			StringBuilder b = new StringBuilder();
			b.append(scheme).append("://").append(host);
			if (port > 0) {
				b.append(':').append(port);
			}
			return b.toString();
		} catch (URISyntaxException e) {
			return raw.trim().replaceAll("/$", "");
		}
	}

	/**
	 * Accepts {@code 192.168.1.1:8010}, {@code http://host:8010/}, or a full API
	 * URL and returns origin only (no path).
	 */
	public static NormalizeResult normalizeServerUrl(String input) {
		if (input == null || input.trim().isEmpty()) {
			return NormalizeResult.failure("서버 주소를 입력해 주세요.");
		}
		String s = input.trim();
		if (s.contains("@") && s.matches("(?i)^https?://[^/]*@.*")) {
			return NormalizeResult.failure(
					"서버 주소에 사용자명/비밀번호를 포함하지 마세요. 인증이 필요한 경우 관리자에게 문의하세요.");
		}
		if (!s.matches("(?i)^https?://.*")) {
			s = "http://" + s;
		}
		s = sanitizeUrl(s);
		try {
			URI u = new URI(s);
			if (u.getHost() == null || u.getHost().isEmpty()) {
				return NormalizeResult.failure("호스트명을 확인해 주세요: \"" + input + "\"");
			}
			String origin = u.getScheme() + "://" + u.getHost();
			if (u.getPort() > 0) {
				origin += ":" + u.getPort();
			}
			return NormalizeResult.success(origin);
		} catch (URISyntaxException e) {
			return NormalizeResult.failure("올바르지 않은 URL 형식입니다: \"" + input + "\"");
		}
	}

	public static String buildApiUrl(String serverUrl, String path) {
		String base = serverUrl == null ? "" : serverUrl.replaceAll("/$", "");
		if (!path.startsWith("/")) {
			path = "/" + path;
		}
		return base + path;
	}
}
