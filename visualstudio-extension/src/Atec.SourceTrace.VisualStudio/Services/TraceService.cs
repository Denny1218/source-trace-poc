using Atec.SourceTrace.Core;
using Atec.SourceTrace.VisualStudio.ToolWindows;
using Microsoft.VisualStudio.Shell;
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using Task = System.Threading.Tasks.Task;

namespace Atec.SourceTrace.VisualStudio.Services;

public sealed class TraceService
{
    private readonly AsyncPackage _package;
    private readonly SettingsService _settings;
    private readonly EditorBridge _editor;
    private readonly TraceHttpClient _http = new();

    public TraceService(AsyncPackage package, SettingsService settings, EditorBridge editor)
    {
        _package = package;
        _settings = settings;
        _editor = editor;
    }

    public async Task RunFunctionHistoryAsync()
    {
        if (!_settings.EnsureConfigured(out var cfgMsg))
        {
            await ShowWarningAsync(cfgMsg);
            return;
        }

        var snap = await _editor.CaptureActiveEditorAsync();
        if (snap == null)
        {
            await ShowWarningAsync("C/C++ 편집기에서 분석할 소스 파일을 먼저 열어주세요.\n(저장되지 않은 Untitled 문서는 지원하지 않습니다.)");
            return;
        }

        var resolved = EditorContextResolver.Resolve(
            snap.SelectedText, null, snap.CursorWord, snap.CurrentLineText);
        if (resolved == null || string.IsNullOrEmpty(resolved.DetectedSymbol))
        {
            await ShowWarningAsync("분석할 함수명 위에 커서를 두거나 코드 일부를 선택해주세요.\nSymbol을 추측하여 서버에 보내지 않습니다.");
            return;
        }

        var filePathForRequest = snap.FilePath;
        try
        {
            var pathInfo = RepoPathResolver.ResolveWithFallback(snap.FilePath);
            filePathForRequest = pathInfo.RepoRelativePath.Replace('\\', '/');
        }
        catch (RepoPathResolver.ResolveError)
        {
            filePathForRequest = snap.FilePath.Replace('\\', '/');
        }

        var built = TraceRequestBuilder.BuildReportRequest(
            _settings.GetEquipmentId(),
            TraceRequestBuilder.DefaultQuery,
            filePathForRequest,
            resolved.SelectedText,
            resolved.DetectedSymbol,
            resolved.SourceModeWire,
            _settings.UseOllama(),
            TraceRequestBuilder.DefaultMaxSelectedChars);

        if (built.Truncated)
        {
            await ShowInfoAsync("선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
        }

        await PostReportAsync(built.JsonBody);
    }

    public async Task RunSelectionTraceAsync()
    {
        if (!_settings.EnsureConfigured(out var cfgMsg))
        {
            await ShowWarningAsync(cfgMsg);
            return;
        }

        var snap = await _editor.CaptureActiveEditorAsync();
        if (snap == null)
        {
            await ShowWarningAsync("C/C++ 편집기에서 분석할 소스 파일을 먼저 열어주세요.");
            return;
        }

        if (!snap.HasSelection)
        {
            await ShowWarningAsync("변경 근거를 조회할 코드를 먼저 선택해 주세요 (한 줄 또는 여러 줄 블록).");
            return;
        }

        RepoPathResolver.Result pathInfo;
        try
        {
            pathInfo = RepoPathResolver.ResolveWithFallback(snap.FilePath);
        }
        catch (RepoPathResolver.ResolveError ex)
        {
            await ShowErrorAsync(ex.Message + "\n현재 파일이 Git Repository 안에 있는지 확인하세요.");
            return;
        }

        var enclosing = SymbolExtractor.FindEnclosingFunctionSymbol(snap.Lines, snap.StartLine0);
        await SubmitSelectionAsync(
            pathInfo.RepoRelativePath,
            null,
            snap.FilePath,
            snap.StartLine1,
            snap.EndLine1,
            snap.SelectedText,
            enclosing);
    }

    private async Task SubmitSelectionAsync(
        string repoRelativePath,
        int? repoIdHint,
        string filePath,
        int startLine,
        int endLine,
        string selectedText,
        string? enclosing)
    {
        var built = TraceRequestBuilder.BuildSelectionRequest(
            _settings.GetEquipmentId(),
            repoRelativePath,
            repoIdHint,
            filePath,
            startLine,
            endLine,
            selectedText,
            enclosing,
            TraceRequestBuilder.DefaultMaxSelectedChars,
            "HEAD");

        if (built.Truncated)
        {
            await ShowInfoAsync("선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
        }

        await PostSelectionAsync(built.JsonBody, async () =>
        {
            var picked = await PickRepoHintAsync();
            if (picked.HasValue)
            {
                await SubmitSelectionAsync(
                    repoRelativePath, picked, filePath, startLine, endLine, selectedText, enclosing);
            }
        });
    }

    public async Task CheckServerAsync()
    {
        var url = _settings.GetServerUrl();
        if (string.IsNullOrWhiteSpace(url))
        {
            await ShowWarningAsync("Server URL을 먼저 설정하세요.");
            return;
        }

        var norm = ServerUrlUtil.NormalizeServerUrl(url);
        if (!norm.Ok)
        {
            await ShowErrorAsync(norm.Error ?? "URL 형식 오류");
            return;
        }

        var result = await Task.Run(() => _http.Health(norm.Url!));
        if (result.Ok)
        {
            await ShowInfoAsync("서버 연결 성공:\n" + norm.Url);
        }
        else
        {
            await ShowErrorAsync(TraceHttpClient.FormatHttpError("서버 연결 확인", result));
        }
    }

    public async Task ConfigureAsync()
    {
        var url = _settings.GetServerUrl();
        if (string.IsNullOrWhiteSpace(url))
        {
            await _settings.OpenOptionsPageAsync();
            return;
        }

        var norm = ServerUrlUtil.NormalizeServerUrl(url);
        if (!norm.Ok)
        {
            await ShowErrorAsync(norm.Error ?? "URL 형식 오류");
            await _settings.OpenOptionsPageAsync();
            return;
        }

        try
        {
            var items = await Task.Run(() => _http.ListEquipment(norm.Url!));
            if (items.Count == 0)
            {
                await ShowWarningAsync("등록된 장비가 없습니다.");
                await _settings.OpenOptionsPageAsync();
                return;
            }

            var picked = await PickEquipmentAsync(items);
            if (picked == null)
            {
                return;
            }

            _settings.SaveServerUrl(norm.Url!);
            _settings.SaveEquipment(picked.Id, picked.Name);
            await ShowInfoAsync($"장비 선택 저장: {picked.Name} (ID {picked.Id})");
        }
        catch (Exception ex)
        {
            await ShowErrorAsync(ex.Message);
            await _settings.OpenOptionsPageAsync();
        }
    }

    private async Task PostReportAsync(string jsonBody)
    {
        var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url!;
        var result = await Task.Run(() => _http.PostReport(serverUrl, jsonBody));
        await HandleResultAsync(result, "함수 변경 이력", false, null);
    }

    private async Task PostSelectionAsync(string jsonBody, Func<Task>? onAmbiguityRetry)
    {
        var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url!;
        var result = await Task.Run(() => _http.PostSelection(serverUrl, jsonBody));
        await HandleResultAsync(result, "선택 코드 변경 근거", true, onAmbiguityRetry);
    }

    private async Task HandleResultAsync(
        TraceHttpClient.HttpResult r,
        string titleHint,
        bool allowAmbiguityRetry,
        Func<Task>? onAmbiguityRetry)
    {
        if (r.Error != null)
        {
            await ShowErrorAsync(TraceHttpClient.UserFacingConnectionError(r.Error));
            return;
        }

        if (!r.Ok)
        {
            var err = TraceHttpClient.FormatHttpError(titleHint, r);
            if (allowAmbiguityRetry && onAmbiguityRetry != null
                && TraceRequestBuilder.LooksLikeAmbiguity(err + " " + r.Body))
            {
                var retry = await AskYesNoAsync(
                    "Repository를 하나만 결정할 수 없습니다.\nRepo를 선택한 뒤 다시 시도할까요?\n\n" + err);
                if (retry)
                {
                    await onAmbiguityRetry();
                }

                return;
            }

            var content = TraceRequestBuilder.PickResultMarkdown(r.Body);
            if (r.Body != null && content.StartsWith("#", StringComparison.Ordinal))
            {
                await ShowMarkdownAsync(content, titleHint);
                return;
            }

            await ShowErrorAsync(err);
            return;
        }

        var markdown = TraceRequestBuilder.PickResultMarkdown(r.Body);
        if (allowAmbiguityRetry && onAmbiguityRetry != null
            && TraceRequestBuilder.LooksLikeAmbiguity(markdown))
        {
            var retry = await AskYesNoAsync("Repository ambiguity가 감지되었습니다. Repo를 선택하고 다시 시도할까요?");
            if (retry)
            {
                await onAmbiguityRetry();
                return;
            }
        }

        await ShowMarkdownAsync(markdown, titleHint);
    }

    private async Task ShowMarkdownAsync(string markdown, string titleHint)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        var window = await _package.ShowToolWindowAsync(
            typeof(SourceTraceToolWindow),
            0,
            create: true,
            CancellationToken.None) as SourceTraceToolWindow;
        window?.ShowMarkdown(markdown, titleHint);
    }

    private async Task<int?> PickRepoHintAsync()
    {
        var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url!;
        var equipmentId = _settings.GetEquipmentId();
        var repos = await Task.Run(() => _http.ListRepositories(serverUrl, equipmentId));
        if (repos.Count == 0)
        {
            await ShowWarningAsync("등록된 Repository가 없습니다.");
            return null;
        }

        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        var labels = repos.Select(r => r.ToString()).ToArray();
        var dlg = new SimplePickDialog("Repository 선택", "동일 경로가 여러 Repo에 있을 때 repo_id_hint로 사용합니다.", labels);
        if (dlg.ShowDialog() != true || dlg.SelectedIndex < 0)
        {
            return null;
        }

        return repos[dlg.SelectedIndex].Id;
    }

    private async Task<TraceHttpClient.EquipmentItem?> PickEquipmentAsync(
        System.Collections.Generic.List<TraceHttpClient.EquipmentItem> items)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        var labels = items.Select(i => i.ToString()).ToArray();
        var dlg = new SimplePickDialog("장비 선택", "Source Trace Backend에 등록된 장비를 선택하세요.", labels);
        if (dlg.ShowDialog() != true || dlg.SelectedIndex < 0)
        {
            return null;
        }

        return items[dlg.SelectedIndex];
    }

    private async Task ShowWarningAsync(string msg)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Warning);
    }

    private async Task ShowErrorAsync(string msg)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Error);
    }

    private async Task ShowInfoAsync(string msg)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private async Task<bool> AskYesNoAsync(string msg)
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        return MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.YesNo, MessageBoxImage.Question)
               == MessageBoxResult.Yes;
    }
}
