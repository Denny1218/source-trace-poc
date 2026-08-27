import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Zero-dependency runner for core unit tests (no JUnit jar required).
 */
public class CoreUnitTests {

	private static int passed = 0;
	private static int failed = 0;

	public static void main(String[] args) throws Exception {
		run("serverUrl_normalize", CoreUnitTests::serverUrl_normalize);
		run("repoRelative_posix", CoreUnitTests::repoRelative_posix);
		run("symbol_extract", CoreUnitTests::symbol_extract);
		run("enclosing_function", CoreUnitTests::enclosing_function);
		run("report_request_json", CoreUnitTests::report_request_json);
		run("report_body_non_empty", CoreUnitTests::report_body_non_empty);
		run("report_equipment_id_number", CoreUnitTests::report_equipment_id_number);
		run("selection_request_json", CoreUnitTests::selection_request_json);
		run("selection_body_non_empty", CoreUnitTests::selection_body_non_empty);
		run("line_numbers_1based", CoreUnitTests::line_numbers_1based);
		run("pick_markdown", CoreUnitTests::pick_markdown);
		run("json_escape_korean", CoreUnitTests::json_escape_korean);
		run("ambiguity_detect", CoreUnitTests::ambiguity_detect);
		run("normalize_json_body", CoreUnitTests::normalize_json_body);
		run("fastapi_422_parser", CoreUnitTests::fastapi_422_parser);
		run("plugin_xml_icon_policy", CoreUnitTests::plugin_xml_icon_policy);
		run("icon16_is_sixteen", CoreUnitTests::icon16_is_sixteen);
		System.out.println();
		System.out.println("RESULT passed=" + passed + " failed=" + failed);
		if (failed > 0) {
			System.exit(1);
		}
	}

	private static void run(String name, ThrowingRunnable r) {
		try {
			r.run();
			passed++;
			System.out.println("OK  " + name);
		} catch (Throwable t) {
			failed++;
			System.out.println("FAIL " + name + " — " + t.getMessage());
			t.printStackTrace(System.out);
		}
	}

	interface ThrowingRunnable {
		void run() throws Exception;
	}

	static void assertTrue(boolean c, String msg) {
		if (!c) {
			throw new AssertionError(msg);
		}
	}

	static void assertEq(Object a, Object b) {
		if (a == null ? b != null : !a.equals(b)) {
			throw new AssertionError("expected=" + b + " actual=" + a);
		}
	}

	static void serverUrl_normalize() {
		var n = com.atec.sourcetrace.eclipse.core.ServerUrlUtil.normalizeServerUrl("192.168.1.1:8010");
		assertTrue(n.ok, n.error);
		assertEq(n.url, "http://192.168.1.1:8010");
		n = com.atec.sourcetrace.eclipse.core.ServerUrlUtil.normalizeServerUrl("http://host:8010/api/trace/report");
		assertTrue(n.ok, n.error);
		assertEq(n.url, "http://host:8010");
		n = com.atec.sourcetrace.eclipse.core.ServerUrlUtil.normalizeServerUrl("");
		assertTrue(!n.ok, "empty should fail");
	}

	static void repoRelative_posix() throws Exception {
		String rel = com.atec.sourcetrace.eclipse.core.RepoPathResolver.toRepoRelativePath(
				"D:/workspace/gate", "D:/workspace/gate/src/fare_calc.c");
		assertEq(rel, "src/fare_calc.c");
		rel = com.atec.sourcetrace.eclipse.core.RepoPathResolver.toRepoRelativePath(
				"D:\\workspace\\gate", "D:\\workspace\\gate\\src\\fare_calc.c");
		assertEq(rel, "src/fare_calc.c");
	}

	static void symbol_extract() {
		assertEq(com.atec.sourcetrace.eclipse.core.SymbolExtractor.extractDetectedSymbol("fare_is_xfer"),
				"fare_is_xfer");
		assertEq(com.atec.sourcetrace.eclipse.core.SymbolExtractor.extractDetectedSymbol("static int foo(void) {"),
				"foo");
		assertEq(com.atec.sourcetrace.eclipse.core.SymbolExtractor.extractDetectedSymbol("if"), null);
	}

	static void enclosing_function() {
		String[] lines = {
				"int outer(void)",
				"{",
				"  if (x) {",
				"    return 1;",
				"  }",
				"  return 0;",
				"}"
		};
		assertEq(com.atec.sourcetrace.eclipse.core.SymbolExtractor.findEnclosingFunctionSymbol(lines, 3), "outer");
	}

	static void report_request_json() {
		var built = com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.buildReportRequest(
				3, "선택한 코드가 왜 변경됐는지 알려줘", "src/a.c", "fare_is_xfer", "fare_is_xfer",
				"selection_symbol", false, 4000);
		assertTrue(built.jsonBody.contains("\"equipment_id\":3"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"detected_symbol\":\"fare_is_xfer\""), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"file_path\":\"src/a.c\""), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"use_ollama\":false"), built.jsonBody);
	}

	static void report_body_non_empty() {
		var built = com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.buildReportRequest(
				1, "q", "src/x.c", "sym", "sym", "cursor_word", false, 4000);
		assertTrue(built.jsonBody != null && !built.jsonBody.isBlank(), "blank");
		assertTrue(built.jsonBody.startsWith("{"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"selected_code\""), built.jsonBody);
	}

	static void report_equipment_id_number() {
		var built = com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.buildReportRequest(
				42, "q", "f.c", "a", "a", "cursor_word", false, 4000);
		assertTrue(built.jsonBody.contains("\"equipment_id\":42"), "must be numeric JSON, not string");
		assertTrue(!built.jsonBody.contains("\"equipment_id\":\"42\""), "must not quote id");
	}

	static void selection_request_json() {
		var built = com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.buildSelectionRequest(
				3, "src/a.c", Integer.valueOf(12), "D:/w/src/a.c", 10, 12, "x = 1;", "outer", 4000, "HEAD");
		assertTrue(built.jsonBody.contains("\"repo_relative_path\":\"src/a.c\""), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"start_line\":10"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"end_line\":12"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"repo_id_hint\":12"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"revision\":\"HEAD\""), built.jsonBody);
	}

	static void selection_body_non_empty() {
		var built = com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.buildSelectionRequest(
				1, "src/a.c", null, null, 1, 1, "int x;", null, 4000, "HEAD");
		assertTrue(built.jsonBody.contains("\"equipment_id\":1"), built.jsonBody);
		assertTrue(built.jsonBody.contains("\"selected_code\""), built.jsonBody);
	}

	static void line_numbers_1based() {
		int start0 = 9;
		int end0 = 11;
		assertEq(Integer.valueOf(start0 + 1), Integer.valueOf(10));
		assertEq(Integer.valueOf(end0 + 1), Integer.valueOf(12));
	}

	static void pick_markdown() {
		String json = "{\"content\":\"# hello\",\"answer\":\"ignored\"}";
		assertEq(com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.pickResultMarkdown(json), "# hello");
	}

	static void json_escape_korean() {
		String q = com.atec.sourcetrace.eclipse.core.JsonUtil.quote("한글\n테스트");
		assertTrue(q.contains("한글"), q);
		assertTrue(q.contains("\\n"), q);
	}

	static void ambiguity_detect() {
		assertTrue(com.atec.sourcetrace.eclipse.core.TraceRequestBuilder.looksLikeAmbiguity(
				"동일한 파일 경로가 여러 장비 Repository에서 확인되어 하나를 결정할 수 없습니다"), "detect");
	}

	static void normalize_json_body() {
		assertEq(com.atec.sourcetrace.eclipse.core.TraceHttpClient.normalizeJsonBody(null), "{}");
		assertEq(com.atec.sourcetrace.eclipse.core.TraceHttpClient.normalizeJsonBody("  "), "{}");
		assertEq(com.atec.sourcetrace.eclipse.core.TraceHttpClient.normalizeJsonBody("{\"a\":1}"), "{\"a\":1}");
	}

	static void fastapi_422_parser() {
		String body = "{\"detail\":[{\"type\":\"missing\",\"loc\":[\"body\"],\"msg\":\"Field required\",\"input\":null}]}";
		var items = com.atec.sourcetrace.eclipse.core.FastApiErrorParser.parseDetail(body);
		assertTrue(!items.isEmpty(), "items");
		assertEq(items.get(0).type, "missing");
		assertEq(items.get(0).loc, "body");
		String msg = com.atec.sourcetrace.eclipse.core.FastApiErrorParser.formatUserMessage("함수 변경 이력 조회", 422, body);
		assertTrue(msg.contains("HTTP 422"), msg);
		assertTrue(msg.contains("body"), msg);
		assertTrue(msg.contains("본문") || msg.contains("Field required") || msg.contains("형식"), msg);
	}

	static void plugin_xml_icon_policy() throws Exception {
		Path xml = Path.of("..", "com.atec.sourcetrace.eclipse", "plugin.xml").normalize().toAbsolutePath();
		if (!Files.exists(xml)) {
			xml = Path.of("c:/sourcechangeTrace/eclipse-plugin/com.atec.sourcetrace.eclipse/plugin.xml");
		}
		String text = Files.readString(xml, StandardCharsets.UTF_8);
		assertTrue(!text.contains("point=\"org.eclipse.ui.commandImages\""), "no commandImages extension");
		assertTrue(!text.contains("toolbar:"), "no toolbar contribution");
		assertTrue(!text.contains("icon64") && !text.contains("icon128") && !text.contains("plugin.png"),
				"no large brand icons in plugin.xml");
		assertTrue(text.contains("menu:org.eclipse.ui.main.menu"), "main menu present");
		// main menu block must not set icon=
		int main = text.indexOf("menu:org.eclipse.ui.main.menu");
		assertTrue(main > 0, "main loc");
		String mainSection = text.substring(main, Math.min(text.length(), main + 800));
		assertTrue(!mainSection.contains("icon=\""), "main menu text-only");
		assertTrue(text.contains("popup:org.eclipse.ui.popup.any"), "context menu");
		assertTrue(text.contains("icon=\"icons/icon16.png\""), "context/view 16x16");
	}

	static void icon16_is_sixteen() throws Exception {
		Path png = Path.of("..", "com.atec.sourcetrace.eclipse", "icons", "icon16.png").normalize().toAbsolutePath();
		if (!Files.exists(png)) {
			png = Path.of("c:/sourcechangeTrace/eclipse-plugin/com.atec.sourcetrace.eclipse/icons/icon16.png");
		}
		assertTrue(Files.exists(png), "icon16 missing");
		// PNG IHDR width/height at bytes 16-23 (big-endian) after 8-byte signature + 8-byte chunk hdr
		byte[] all = Files.readAllBytes(png);
		assertTrue(all.length > 24, "too small");
		int w = ((all[16] & 0xff) << 24) | ((all[17] & 0xff) << 16) | ((all[18] & 0xff) << 8) | (all[19] & 0xff);
		int h = ((all[20] & 0xff) << 24) | ((all[21] & 0xff) << 16) | ((all[22] & 0xff) << 8) | (all[23] & 0xff);
		assertEq(Integer.valueOf(w), Integer.valueOf(16));
		assertEq(Integer.valueOf(h), Integer.valueOf(16));
	}
}
