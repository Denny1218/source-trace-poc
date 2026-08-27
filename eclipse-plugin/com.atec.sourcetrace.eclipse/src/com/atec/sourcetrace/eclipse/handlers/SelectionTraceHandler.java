package com.atec.sourcetrace.eclipse.handlers;

import org.eclipse.core.commands.AbstractHandler;
import org.eclipse.core.commands.ExecutionEvent;
import org.eclipse.core.commands.ExecutionException;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.handlers.HandlerUtil;
import org.eclipse.ui.texteditor.ITextEditor;

import com.atec.sourcetrace.eclipse.core.RepoPathResolver;
import com.atec.sourcetrace.eclipse.core.SymbolExtractor;
import com.atec.sourcetrace.eclipse.core.TraceRequestBuilder;
import com.atec.sourcetrace.eclipse.prefs.TracePreferences;
import com.atec.sourcetrace.eclipse.ui.EditorAccess;
import com.atec.sourcetrace.eclipse.ui.TraceJobs;
import com.atec.sourcetrace.eclipse.ui.TraceUi;

/** Source Trace: 선택 코드 변경 근거 조회 → POST /api/trace/selection */
public class SelectionTraceHandler extends AbstractHandler {

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
			if (!snap.hasSelection) {
				MessageDialog.openWarning(shell, "ATEC Source Trace",
						"변경 근거를 조회할 코드를 먼저 선택해 주세요 (한 줄 또는 여러 줄 블록).");
				return null;
			}

			final RepoPathResolver.Result pathInfo;
			try {
				pathInfo = RepoPathResolver.resolveWithFallback(snap.filePath);
			} catch (RepoPathResolver.ResolveError e) {
				MessageDialog.openError(shell, "ATEC Source Trace",
						e.getMessage() + "\n현재 파일이 Git Repository 안에 있는지 확인하세요.");
				return null;
			}

			final String enclosing = SymbolExtractor.findEnclosingFunctionSymbol(snap.lines, snap.startLine0);
			final int startLine = snap.startLine0 + 1;
			final int endLine = snap.endLine0 + 1;
			final String serverUrl = TracePreferences.getServerUrl();
			final int equipmentId = TracePreferences.getEquipmentId().intValue();
			final String selectedText = snap.selectedText;
			final String filePath = snap.filePath;

			submit(shell, serverUrl, equipmentId, pathInfo.repoRelativePath, null, filePath,
					startLine, endLine, selectedText, enclosing);
		} catch (Exception e) {
			MessageDialog.openError(shell, "ATEC Source Trace", e.getMessage());
		}
		return null;
	}

	private static void submit(
			Shell shell,
			String serverUrl,
			int equipmentId,
			String repoRelativePath,
			Integer repoIdHint,
			String filePath,
			int startLine,
			int endLine,
			String selectedText,
			String enclosing) {
		TraceRequestBuilder.BuiltRequest built = TraceRequestBuilder.buildSelectionRequest(
				equipmentId,
				repoRelativePath,
				repoIdHint,
				filePath,
				startLine,
				endLine,
				selectedText,
				enclosing,
				TracePreferences.maxSelectedChars(),
				"HEAD");
		if (built.truncated) {
			MessageDialog.openInformation(shell, "ATEC Source Trace",
					"선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
		}
		TraceJobs.runSelection(shell, serverUrl, built.jsonBody, () -> {
			Integer picked = TraceUi.pickRepoHint(shell, serverUrl, equipmentId);
			if (picked == null) {
				return;
			}
			submit(shell, serverUrl, equipmentId, repoRelativePath, picked, filePath,
					startLine, endLine, selectedText, enclosing);
		});
	}
}
