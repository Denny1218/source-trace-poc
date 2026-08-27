package com.atec.sourcetrace.eclipse.prefs;

import org.eclipse.jface.preference.IPreferenceStore;

import com.atec.sourcetrace.eclipse.Activator;
import com.atec.sourcetrace.eclipse.core.ServerUrlUtil;

public final class TracePreferences {

	private TracePreferences() {
	}

	private static IPreferenceStore store() {
		return Activator.getDefault().getPreferenceStore();
	}

	public static String getServerUrl() {
		String raw = store().getString(PreferenceInitializer.PREF_SERVER_URL);
		ServerUrlUtil.NormalizeResult n = ServerUrlUtil.normalizeServerUrl(raw);
		return n.ok ? n.url : null;
	}

	public static String getRawServerUrl() {
		return store().getString(PreferenceInitializer.PREF_SERVER_URL);
	}

	public static void setServerUrl(String url) {
		store().setValue(PreferenceInitializer.PREF_SERVER_URL, url == null ? "" : url);
	}

	public static Integer getEquipmentId() {
		int id = store().getInt(PreferenceInitializer.PREF_EQUIPMENT_ID);
		return id > 0 ? Integer.valueOf(id) : null;
	}

	public static void setEquipment(int id, String name) {
		store().setValue(PreferenceInitializer.PREF_EQUIPMENT_ID, id);
		store().setValue(PreferenceInitializer.PREF_EQUIPMENT_NAME, name == null ? "" : name);
	}

	public static String getEquipmentName() {
		return store().getString(PreferenceInitializer.PREF_EQUIPMENT_NAME);
	}

	public static boolean useOllama() {
		return store().getBoolean(PreferenceInitializer.PREF_USE_OLLAMA);
	}

	public static int maxSelectedChars() {
		int n = store().getInt(PreferenceInitializer.PREF_MAX_SELECTED_CHARS);
		return n > 0 ? n : 4000;
	}
}
