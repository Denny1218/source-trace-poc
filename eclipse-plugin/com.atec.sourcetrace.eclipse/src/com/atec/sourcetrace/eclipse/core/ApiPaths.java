package com.atec.sourcetrace.eclipse.core;

/**
 * Backend v2.6 API paths — must stay identical to vscode-extension
 * {@code serverConfig.ts} PATHS. Do not invent Eclipse-only endpoints.
 */
public final class ApiPaths {

	public static final String HEALTH = "/api/health";
	public static final String EQUIPMENT_LIST = "/api/equipment";
	public static final String TRACE_REPORT = "/api/trace/report";
	public static final String TRACE_SELECTION = "/api/trace/selection";

	private ApiPaths() {
	}

	public static String equipmentById(int id) {
		return EQUIPMENT_LIST + "/" + id;
	}

	public static String equipmentRepositories(int id) {
		return EQUIPMENT_LIST + "/" + id + "/repositories";
	}
}
