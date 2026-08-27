package com.atec.sourcetrace.eclipse.handlers;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.texteditor.ITextEditor;

import com.atec.sourcetrace.eclipse.core.EditorContextResolver;
import com.atec.sourcetrace.eclipse.core.RepoPathResolver;
import com.atec.sourcetrace.eclipse.core.TraceRequestBuilder;
import com.atec.sourcetrace.eclipse.prefs.TracePreferences;
import com.atec.sourcetrace.eclipse.ui.EditorAccess;
import com.atec.sourcetrace.eclipse.ui.TraceJobs;
import com.atec.sourcetrace.eclipse.ui.TraceUi;

/** Source Trace: 함수 변경 이력 조회 → POST /api/trace/report */
public class FunctionHistoryHandler extends AbstractHandler {

	@Override
	public Object execute(ExecutionEvent event) throws ExecutionException {
		Shell shell = HandlerUtil.getActiveShell(event);
		if (!TraceUi.ensureConfigured(shell)) {
			return null;
		}
		ITextEditor editor = EditorAccess.activeTextEditor();
		if (editor == null) {
			MessageDialog.openWarning(shell, "ATEC Source Trace", "분석할 소스 파일을 먼저 열어주세요.");
			return null;
		}
		try {
			EditorAccess.Snapshot snap = EditorAccess.capture(editor);
			EditorContextResolver.Resolved resolved = EditorContextResolver.resolve(
					snap.selectedText, null, snap.cursorWord, snap.currentLineText);
			if (resolved == null) {
				MessageDialog.openWarning(shell, "ATEC Source Trace",
						"분석할 함수명 위에 커서를 두거나 코드 일부를 선택해주세요.");
				return null;
			}

			String filePathForRequest = snap.filePath;
			try {
				RepoPathResolver.Result pathInfo = RepoPathResolver.resolveWithFallback(snap.filePath);
				filePathForRequest = pathInfo.repoRelativePath.replace('\\', '/');
			} catch (RepoPathResolver.ResolveError ignored) {
				// Soft fallback like VS Code function-history path
				if (filePathForRequest != null) {
					filePathForRequest = filePathForRequest.replace('\\', '/');
				}
			}

			String serverUrl = TracePreferences.getServerUrl();
			int equipmentId = TracePreferences.getEquipmentId().intValue();
			TraceRequestBuilder.BuiltRequest built = TraceRequestBuilder.buildReportRequest(
					equipmentId,
					TraceRequestBuilder.DEFAULT_QUERY,
					filePathForRequest,
					resolved.selectedText,
					resolved.detectedSymbol,
					resolved.sourceMode.wire,
					TracePreferences.useOllama(),
					TracePreferences.maxSelectedChars());
			if (built.truncated) {
				MessageDialog.openInformation(shell, "ATEC Source Trace",
						"선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
			}
			TraceJobs.runReport(shell, serverUrl, built.jsonBody);
		} catch (Exception e) {
			MessageDialog.openError(shell, "ATEC Source Trace", e.getMessage());
		}
		return null;
	}
}
