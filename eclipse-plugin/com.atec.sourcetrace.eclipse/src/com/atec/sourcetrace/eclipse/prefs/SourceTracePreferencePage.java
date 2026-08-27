package com.atec.sourcetrace.eclipse.prefs;

import org.eclipse.jface.preference.BooleanFieldEditor;
import org.eclipse.jface.preference.FieldEditorPreferencePage;
import org.eclipse.jface.preference.IntegerFieldEditor;
import org.eclipse.jface.preference.StringFieldEditor;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchPreferencePage;

import com.atec.sourcetrace.eclipse.Activator;

public class SourceTracePreferencePage extends FieldEditorPreferencePage implements IWorkbenchPreferencePage {

	public SourceTracePreferencePage() {
		super(GRID);
		setPreferenceStore(Activator.getDefault().getPreferenceStore());
		setDescription("ATEC Source Trace — Backend 서버 및 장비 설정 (장비 프로젝트 파일은 변경하지 않습니다).");
	}

	@Override
	public void init(IWorkbench workbench) {
		// no-op
	}

	@Override
	protected void createFieldEditors() {
		addField(new StringFieldEditor(
				PreferenceInitializer.PREF_SERVER_URL,
				"Server URL:",
				getFieldEditorParent()));
		addField(new IntegerFieldEditor(
				PreferenceInitializer.PREF_EQUIPMENT_ID,
				"Equipment ID:",
				getFieldEditorParent()));
		addField(new StringFieldEditor(
				PreferenceInitializer.PREF_EQUIPMENT_NAME,
				"Equipment Name (표시용):",
				getFieldEditorParent()));
		addField(new BooleanFieldEditor(
				PreferenceInitializer.PREF_USE_OLLAMA,
				"useOllama (AI 보조 설명)",
				getFieldEditorParent()));
		addField(new IntegerFieldEditor(
				PreferenceInitializer.PREF_MAX_SELECTED_CHARS,
				"maxSelectedCodeChars:",
				getFieldEditorParent()));
	}
}
