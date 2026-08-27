package com.atec.sourcetrace.eclipse.handlers;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.ui.handlers.HandlerUtil;

import com.atec.sourcetrace.eclipse.ui.TraceUi;

public class CheckServerHandler extends AbstractHandler {
	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		TraceUi.checkServer(HandlerUtil.getActiveShell(event));
		return null;
	}
}
