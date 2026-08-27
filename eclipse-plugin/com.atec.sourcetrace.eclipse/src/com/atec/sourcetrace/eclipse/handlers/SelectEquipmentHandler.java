package com.atec.sourcetrace.eclipse.handlers;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.handlers.HandlerUtil;

import com.atec.sourcetrace.eclipse.prefs.TracePreferences;
import com.atec.sourcetrace.eclipse.ui.TraceUi;

public class SelectEquipmentHandler extends AbstractHandler {
	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		Shell shell = HandlerUtil.getActiveShell(event);
		String url = TracePreferences.getServerUrl();
		if (url == null) {
			MessageDialog.openError(shell, "ATEC Source Trace", "먼저 Server URL을 설정하세요.");
			return null;
		}
		try {
			TraceUi.selectEquipment(shell, url);
		} catch (Exception e) {
			MessageDialog.openError(shell, "ATEC Source Trace", e.getMessage());
		}
		return null;
	}
}
