package com.atec.sourcetrace.eclipse.prefs;

import org.eclipse.core.runtime.preferences.AbstractPreferenceInitializer;
import org.eclipse.jface.preference.IPreferenceStore;

import com.atec.sourcetrace.eclipse.Activator;

public class PreferenceInitializer extends AbstractPreferenceInitializer {

	public static final String PREF_SERVER_URL = "serverUrl";
	public static final String PREF_EQUIPMENT_ID = "equipmentId";
	public static final String PREF_EQUIPMENT_NAME = "equipmentName";
	public static final String PREF_USE_OLLAMA = "useOllama";
	public static final String PREF_MAX_SELECTED_CHARS = "maxSelectedCodeChars";

	@Override
	public void initializeDefaultPreferences() {
		IPreferenceStore store = Activator.getDefault().getPreferenceStore();
		store.setDefault(PREF_SERVER_URL, "");
		store.setDefault(PREF_EQUIPMENT_ID, 0);
		store.setDefault(PREF_EQUIPMENT_NAME, "");
		store.setDefault(PREF_USE_OLLAMA, false);
		store.setDefault(PREF_MAX_SELECTED_CHARS, 4000);
	}
}
