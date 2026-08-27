package com.atec.sourcetrace.eclipse.ui;

import org.eclipse.jface.dialogs.IInputValidator;
import org.eclipse.jface.dialogs.InputDialog;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.dialogs.ElementListSelectionDialog;

import com.atec.sourcetrace.eclipse.core.ServerUrlUtil;
import com.atec.sourcetrace.eclipse.core.TraceHttpClient;
import com.atec.sourcetrace.eclipse.core.TraceHttpClient.EquipmentItem;
import com.atec.sourcetrace.eclipse.core.TraceHttpClient.RepoItem;
import com.atec.sourcetrace.eclipse.prefs.TracePreferences;

public final class TraceUi {

	private TraceUi() {
	}

	public static boolean ensureConfigured(Shell shell) {
		String url = TracePreferences.getServerUrl();
		Integer eid = TracePreferences.getEquipmentId();
		if (url == null || eid == null) {
			MessageDialog.openError(shell, "ATEC Source Trace",
					"Source Trace 서버 또는 장비가 설정되지 않았습니다.\n"
							+ "메뉴: ATEC Source Trace → 서버 및 장비 설정");
			return false;
		}
		return true;
	}

	public static void configureServer(Shell shell) {
		InputDialog dlg = new InputDialog(shell, "ATEC Source Trace",
				"Source Trace Server URL (예: http://192.168.0.10:8010)",
				TracePreferences.getRawServerUrl(),
				new IInputValidator() {
					@Override
					public String isValid(String newText) {
						ServerUrlUtil.NormalizeResult n = ServerUrlUtil.normalizeServerUrl(newText);
						return n.ok ? null : n.error;
					}
				});
		if (dlg.open() != InputDialog.OK) {
			return;
		}
		ServerUrlUtil.NormalizeResult n = ServerUrlUtil.normalizeServerUrl(dlg.getValue());
		if (!n.ok) {
			MessageDialog.openError(shell, "ATEC Source Trace", n.error);
			return;
		}
		TracePreferences.setServerUrl(n.url);
		TraceHttpClient client = new TraceHttpClient();
		TraceHttpClient.HttpResult health = client.health(n.url);
		if (!health.ok()) {
			MessageDialog.openWarning(shell, "ATEC Source Trace",
					"Server URL을 저장했습니다.\n다만 연결 확인에 실패했습니다.\n"
							+ TraceHttpClient.formatHttpError("Health", health));
			return;
		}
		try {
			selectEquipment(shell, n.url);
		} catch (Exception e) {
			MessageDialog.openError(shell, "ATEC Source Trace",
					"장비 목록 조회 실패: " + e.getMessage());
		}
	}

	public static void selectEquipment(Shell shell, String serverUrl) throws Exception {
		TraceHttpClient client = new TraceHttpClient();
		java.util.List<EquipmentItem> list = client.listEquipment(serverUrl);
		if (list.isEmpty()) {
			MessageDialog.openInformation(shell, "ATEC Source Trace", "등록된 장비가 없습니다.");
			return;
		}
		ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider());
		dlg.setTitle("장비 선택");
		dlg.setMessage("조회에 사용할 장비를 선택하세요.");
		dlg.setElements(list.toArray());
		if (dlg.open() != ElementListSelectionDialog.OK) {
			return;
		}
		Object sel = dlg.getFirstResult();
		if (sel instanceof EquipmentItem) {
			EquipmentItem eq = (EquipmentItem) sel;
			TracePreferences.setEquipment(eq.id, eq.name);
			MessageDialog.openInformation(shell, "ATEC Source Trace",
					"장비 저장: " + eq.name + " (ID " + eq.id + ")");
		}
	}

	public static Integer pickRepoHint(Shell shell, String serverUrl, int equipmentId) {
		try {
			TraceHttpClient client = new TraceHttpClient();
			java.util.List<RepoItem> repos = client.listRepositories(serverUrl, equipmentId);
			if (repos.isEmpty()) {
				return null;
			}
			ElementListSelectionDialog dlg = new ElementListSelectionDialog(shell, new LabelProvider());
			dlg.setTitle("Repository 선택 (ambiguity)");
			dlg.setMessage("동일 상대경로가 여러 Repo에 있습니다. 조회할 Repository를 선택하세요.\n"
					+ "(repo_id_hint로 Backend에 전달됩니다)");
			dlg.setElements(repos.toArray());
			if (dlg.open() != ElementListSelectionDialog.OK) {
				return null;
			}
			Object sel = dlg.getFirstResult();
			if (sel instanceof RepoItem) {
				return Integer.valueOf(((RepoItem) sel).id);
			}
		} catch (Exception e) {
			MessageDialog.openError(shell, "ATEC Source Trace", e.getMessage());
		}
		return null;
	}

	public static void checkServer(Shell shell) {
		String url = TracePreferences.getServerUrl();
		if (url == null) {
			MessageDialog.openError(shell, "ATEC Source Trace", "Server URL이 설정되지 않았습니다.");
			return;
		}
		TraceHttpClient.HttpResult r = new TraceHttpClient().health(url);
		if (r.ok()) {
			MessageDialog.openInformation(shell, "ATEC Source Trace",
					"서버 연결 정상\n" + url + "\nHTTP " + r.status);
		} else {
			MessageDialog.openError(shell, "ATEC Source Trace",
					TraceHttpClient.formatHttpError("서버 연결 확인", r));
		}
	}
}
