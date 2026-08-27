package com.atec.sourcetrace.eclipse.ui;

import org.eclipse.core.runtime.IProgressMonitor;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.core.runtime.jobs.Job;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.PlatformUI;

import com.atec.sourcetrace.eclipse.Activator;
import com.atec.sourcetrace.eclipse.core.TraceHttpClient;
import com.atec.sourcetrace.eclipse.core.TraceRequestBuilder;

public final class TraceJobs {

	private TraceJobs() {
	}

	public static void runReport(Shell shell, String serverUrl, String jsonBody) {
		Job job = new Job("Source Trace: 함수 변경 이력 조회") {
			@Override
			protected IStatus run(IProgressMonitor monitor) {
				monitor.beginTask("Backend 요청 중...", IProgressMonitor.UNKNOWN);
				TraceHttpClient.HttpResult r = new TraceHttpClient().postReport(serverUrl, jsonBody);
				monitor.done();
				Display.getDefault().asyncExec(() -> handleResult(shell, r, "함수 변경 이력", false, null));
				return Status.OK_STATUS;
			}
		};
		job.setUser(true);
		job.schedule();
	}

	public static void runSelection(
			Shell shell,
			String serverUrl,
			String jsonBody,
			Runnable onAmbiguityRetry) {
		Job job = new Job("Source Trace: 선택 코드 변경 근거 조회") {
			@Override
			protected IStatus run(IProgressMonitor monitor) {
				monitor.beginTask("git blame / Diff 조회 중...", IProgressMonitor.UNKNOWN);
				TraceHttpClient.HttpResult r = new TraceHttpClient().postSelection(serverUrl, jsonBody);
				monitor.done();
				Display.getDefault().asyncExec(
						() -> handleResult(shell, r, "선택 코드 변경 근거", true, onAmbiguityRetry));
				return Status.OK_STATUS;
			}
		};
		job.setUser(true);
		job.schedule();
	}

	private static void handleResult(
			Shell shell,
			TraceHttpClient.HttpResult r,
			String titleHint,
			boolean allowAmbiguityRetry,
			Runnable onAmbiguityRetry) {
		if (r.error != null) {
			MessageDialog.openError(shell, "ATEC Source Trace",
					TraceHttpClient.userFacingConnectionError(r.error));
			return;
		}
		if (!r.ok()) {
			String err = TraceHttpClient.formatHttpError(titleHint, r);
			if (allowAmbiguityRetry && onAmbiguityRetry != null
					&& TraceRequestBuilder.looksLikeAmbiguity(err + " " + r.body)) {
				boolean retry = MessageDialog.openQuestion(shell, "ATEC Source Trace",
						"Repository를 하나만 결정할 수 없습니다.\nRepo를 선택한 뒤 다시 시도할까요?\n\n" + err);
				if (retry) {
					onAmbiguityRetry.run();
				}
				return;
			}
			// report endpoint often returns 200 with Markdown even on soft errors;
			// selection may return 200 with content too — if body has content, show it.
			String content = TraceRequestBuilder.pickResultMarkdown(r.body);
			if (r.body != null && content != null && content.startsWith("#")) {
				showInView(content, titleHint);
				return;
			}
			MessageDialog.openError(shell, "ATEC Source Trace", err);
			return;
		}
		String markdown = TraceRequestBuilder.pickResultMarkdown(r.body);
		if (allowAmbiguityRetry && onAmbiguityRetry != null
				&& TraceRequestBuilder.looksLikeAmbiguity(markdown)) {
			boolean retry = MessageDialog.openQuestion(shell, "ATEC Source Trace",
					"Repository ambiguity가 감지되었습니다. Repo를 선택하고 다시 시도할까요?");
			if (retry) {
				onAmbiguityRetry.run();
				return;
			}
		}
		showInView(markdown, titleHint);
	}

	public static void showInView(String markdown, String titleHint) {
		try {
			IWorkbenchPage page = PlatformUI.getWorkbench().getActiveWorkbenchWindow().getActivePage();
			ResultView view = (ResultView) page.showView(ResultView.ID);
			String title = "ATEC Source Trace";
			if (markdown != null && markdown.startsWith("# ")) {
				int nl = markdown.indexOf('\n');
				title = nl > 2 ? markdown.substring(2, nl).trim() : titleHint;
			}
			view.showMarkdown(markdown, title);
		} catch (PartInitException e) {
			Activator.getDefault().getLog().log(
					new Status(IStatus.ERROR, Activator.PLUGIN_ID, "Result View 열기 실패", e));
		}
	}
}
