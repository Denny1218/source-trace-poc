using Atec.SourceTrace.Core;
using Atec.SourceTrace.VisualStudio2010.ToolWindows;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;
using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Threading;
using ThreadingTasks = System.Threading.Tasks;

namespace Atec.SourceTrace.VisualStudio2010.Services
{
    public sealed class TraceService
    {
        private readonly AtecSourceTracePackage _package;
        private readonly SettingsService _settings;
        private readonly EditorBridge _editor;
        private readonly Dispatcher _dispatcher;
        private readonly TraceHttpClient _http = new TraceHttpClient();

        public TraceService(AtecSourceTracePackage package, SettingsService settings, EditorBridge editor, Dispatcher dispatcher)
        {
            _package = package;
            _settings = settings;
            _editor = editor;
            _dispatcher = dispatcher;
        }

        public void RunFunctionHistory(object sender, EventArgs e)
        {
            string cfgMsg;
            if (!_settings.EnsureConfigured(out cfgMsg))
            {
                ShowWarning(cfgMsg);
                return;
            }

            var snap = _editor.CaptureActiveEditor();
            if (snap == null)
            {
                ShowWarning("C/C++ 편집기에서 분석할 소스 파일을 먼저 열어주세요.\n(저장되지 않은 Untitled 문서는 지원하지 않습니다.)");
                return;
            }

            var resolved = EditorContextResolver.Resolve(
                snap.SelectedText, null, snap.CursorWord, snap.CurrentLineText);
            if (resolved == null || string.IsNullOrEmpty(resolved.DetectedSymbol))
            {
                ShowWarning("분석할 함수명 위에 커서를 두거나 코드 일부를 선택해주세요.\nSymbol을 추측하여 서버에 보내지 않습니다.");
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
                ShowInfo("선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
            }

            RunInBackground(delegate
            {
                var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url;
                var result = _http.PostReport(serverUrl, built.JsonBody);
                OnUi(delegate { HandleResult(result, "함수 변경 이력", false, null); });
            });
        }

        public void RunSelectionTrace(object sender, EventArgs e)
        {
            string cfgMsg;
            if (!_settings.EnsureConfigured(out cfgMsg))
            {
                ShowWarning(cfgMsg);
                return;
            }

            var snap = _editor.CaptureActiveEditor();
            if (snap == null)
            {
                ShowWarning("C/C++ 편집기에서 분석할 소스 파일을 먼저 열어주세요.");
                return;
            }

            if (!snap.HasSelection)
            {
                ShowWarning("변경 근거를 조회할 코드를 먼저 선택해 주세요 (한 줄 또는 여러 줄 블록).");
                return;
            }

            RepoPathResolver.Result pathInfo;
            try
            {
                pathInfo = RepoPathResolver.ResolveWithFallback(snap.FilePath);
            }
            catch (RepoPathResolver.ResolveError ex)
            {
                ShowError(ex.Message + "\n현재 파일이 Git Repository 안에 있는지 확인하세요.");
                return;
            }

            var enclosing = SymbolExtractor.FindEnclosingFunctionSymbol(snap.Lines, snap.StartLine0);
            SubmitSelection(
                pathInfo.RepoRelativePath,
                null,
                snap.FilePath,
                snap.StartLine1,
                snap.EndLine1,
                snap.SelectedText,
                enclosing);
        }

        private void SubmitSelection(
            string repoRelativePath,
            int? repoIdHint,
            string filePath,
            int startLine,
            int endLine,
            string selectedText,
            string enclosing)
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
                ShowInfo("선택한 코드가 제한 길이를 초과해 앞부분만 전송됩니다.");
            }

            RunInBackground(delegate
            {
                var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url;
                var result = _http.PostSelection(serverUrl, built.JsonBody);
                OnUi(delegate
                {
                    HandleResult(result, "선택 코드 변경 근거", true, delegate
                    {
                        var picked = PickRepoHint();
                        if (picked.HasValue)
                        {
                            SubmitSelection(
                                repoRelativePath, picked, filePath, startLine, endLine, selectedText, enclosing);
                        }
                    });
                });
            });
        }

        public void CheckServer(object sender, EventArgs e)
        {
            var url = _settings.GetServerUrl();
            if (string.IsNullOrWhiteSpace(url))
            {
                ShowWarning("Server URL을 먼저 설정하세요.");
                return;
            }

            var norm = ServerUrlUtil.NormalizeServerUrl(url);
            if (!norm.Ok)
            {
                ShowError(norm.Error ?? "URL 형식 오류");
                return;
            }

            RunInBackground(delegate
            {
                var result = _http.Health(norm.Url);
                OnUi(delegate
                {
                    if (result.Ok)
                    {
                        ShowInfo("서버 연결 성공:\n" + norm.Url);
                    }
                    else
                    {
                        ShowError(TraceHttpClient.FormatHttpError("서버 연결 확인", result));
                    }
                });
            });
        }

        public void Configure(object sender, EventArgs e)
        {
            var url = _settings.GetServerUrl();
            if (string.IsNullOrWhiteSpace(url))
            {
                _settings.OpenOptionsHint();
                return;
            }

            var norm = ServerUrlUtil.NormalizeServerUrl(url);
            if (!norm.Ok)
            {
                ShowError(norm.Error ?? "URL 형식 오류");
                _settings.OpenOptionsHint();
                return;
            }

            RunInBackground(delegate
            {
                try
                {
                    var items = _http.ListEquipment(norm.Url);
                    OnUi(delegate
                    {
                        if (items.Count == 0)
                        {
                            ShowWarning("등록된 장비가 없습니다.");
                            _settings.OpenOptionsHint();
                            return;
                        }

                        var picked = PickEquipment(items);
                        if (picked == null)
                        {
                            return;
                        }

                        _settings.SaveServerUrl(norm.Url);
                        _settings.SaveEquipment(picked.Id, picked.Name);
                        ShowInfo("장비 선택 저장: " + picked.Name + " (ID " + picked.Id + ")");
                    });
                }
                catch (Exception ex)
                {
                    OnUi(delegate
                    {
                        ShowError(ex.Message);
                        _settings.OpenOptionsHint();
                    });
                }
            });
        }

        private void HandleResult(
            TraceHttpClient.HttpResult r,
            string titleHint,
            bool allowAmbiguityRetry,
            Action onAmbiguityRetry)
        {
            if (r.Error != null)
            {
                ShowError(TraceHttpClient.UserFacingConnectionError(r.Error));
                return;
            }

            if (!r.Ok)
            {
                var err = TraceHttpClient.FormatHttpError(titleHint, r);
                if (allowAmbiguityRetry && onAmbiguityRetry != null
                    && TraceRequestBuilder.LooksLikeAmbiguity(err + " " + r.Body))
                {
                    if (AskYesNo("Repository를 하나만 결정할 수 없습니다.\nRepo를 선택한 뒤 다시 시도할까요?\n\n" + err))
                    {
                        onAmbiguityRetry();
                    }

                    return;
                }

                var content = TraceRequestBuilder.PickResultMarkdown(r.Body);
                if (r.Body != null && content.StartsWith("#", StringComparison.Ordinal))
                {
                    ShowMarkdown(content, titleHint);
                    return;
                }

                ShowError(err);
                return;
            }

            var markdown = TraceRequestBuilder.PickResultMarkdown(r.Body);
            if (allowAmbiguityRetry && onAmbiguityRetry != null
                && TraceRequestBuilder.LooksLikeAmbiguity(markdown))
            {
                if (AskYesNo("Repository ambiguity가 감지되었습니다. Repo를 선택하고 다시 시도할까요?"))
                {
                    onAmbiguityRetry();
                    return;
                }
            }

            ShowMarkdown(markdown, titleHint);
        }

        private void ShowMarkdown(string markdown, string titleHint)
        {
            var window = _package.FindOrCreateToolWindow() as SourceTraceToolWindow;
            if (window == null)
            {
                ShowError("ATEC Source Trace Tool Window를 열 수 없습니다.");
                return;
            }

            window.ShowMarkdown(markdown, titleHint);
            var frame = window.Frame as IVsWindowFrame;
            if (frame != null)
            {
                frame.Show();
            }
        }

        private int? PickRepoHint()
        {
            var serverUrl = ServerUrlUtil.NormalizeServerUrl(_settings.GetServerUrl()).Url;
            var equipmentId = _settings.GetEquipmentId();
            List<TraceHttpClient.RepoItem> repos;
            try
            {
                repos = _http.ListRepositories(serverUrl, equipmentId);
            }
            catch (Exception ex)
            {
                ShowError(ex.Message);
                return null;
            }

            if (repos.Count == 0)
            {
                ShowWarning("등록된 Repository가 없습니다.");
                return null;
            }

            var labels = new string[repos.Count];
            for (var i = 0; i < repos.Count; i++)
            {
                labels[i] = repos[i].ToString();
            }

            var dlg = new SimplePickDialog("Repository 선택", "동일 경로가 여러 Repo에 있을 때 repo_id_hint로 사용합니다.", labels);
            if (dlg.ShowDialog() != true || dlg.SelectedIndex < 0)
            {
                return null;
            }

            return repos[dlg.SelectedIndex].Id;
        }

        private TraceHttpClient.EquipmentItem PickEquipment(List<TraceHttpClient.EquipmentItem> items)
        {
            var labels = new string[items.Count];
            for (var i = 0; i < items.Count; i++)
            {
                labels[i] = items[i].ToString();
            }

            var dlg = new SimplePickDialog("장비 선택", "Source Trace Backend에 등록된 장비를 선택하세요.", labels);
            if (dlg.ShowDialog() != true || dlg.SelectedIndex < 0)
            {
                return null;
            }

            return items[dlg.SelectedIndex];
        }

        private void RunInBackground(Action work)
        {
            ThreadingTasks.Task.Factory.StartNew(delegate
            {
                try
                {
                    work();
                }
                catch (Exception ex)
                {
                    OnUi(delegate { ShowError(ex.Message); });
                }
            });
        }

        private void OnUi(Action work)
        {
            if (_dispatcher.CheckAccess())
            {
                work();
            }
            else
            {
                _dispatcher.Invoke(work);
            }
        }

        private void ShowWarning(string msg)
        {
            MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Warning);
        }

        private void ShowError(string msg)
        {
            MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Error);
        }

        private void ShowInfo(string msg)
        {
            MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private bool AskYesNo(string msg)
        {
            return MessageBox.Show(msg, "ATEC Source Trace", MessageBoxButton.YesNo, MessageBoxImage.Question)
                   == MessageBoxResult.Yes;
        }
    }
}
