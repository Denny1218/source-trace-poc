using Atec.SourceTrace.Core;
using Atec.SourceTrace.VisualStudio.Options;
using Microsoft.VisualStudio.Shell;
using System.Threading.Tasks;
using System.Windows;
using Task = System.Threading.Tasks.Task;

namespace Atec.SourceTrace.VisualStudio.Services;

public sealed class SettingsService
{
    private readonly AsyncPackage _package;

    public SettingsService(AsyncPackage package)
    {
        _package = package;
    }

    public SourceTraceOptionsPage GetOptionsPage()
    {
        return (SourceTraceOptionsPage)_package.GetDialogPage(typeof(SourceTraceOptionsPage));
    }

    public string GetServerUrl() => GetOptionsPage().ServerUrl?.Trim() ?? string.Empty;

    public int GetEquipmentId() => GetOptionsPage().EquipmentId;

    public string GetEquipmentName() => GetOptionsPage().EquipmentName?.Trim() ?? string.Empty;

    public bool UseOllama() => GetOptionsPage().UseOllama;

    public void SaveEquipment(int id, string name)
    {
        var page = GetOptionsPage();
        page.EquipmentId = id;
        page.EquipmentName = name ?? string.Empty;
        page.SaveSettingsToStorage();
    }

    public void SaveServerUrl(string url)
    {
        var page = GetOptionsPage();
        page.ServerUrl = url ?? string.Empty;
        page.SaveSettingsToStorage();
    }

    public bool EnsureConfigured(out string message)
    {
        var url = GetServerUrl();
        if (string.IsNullOrWhiteSpace(url))
        {
            message = "Source Trace 서버 URL이 설정되지 않았습니다.\n도구 > 옵션 > ATEC Source Trace에서 Server URL을 입력하세요.";
            return false;
        }

        var norm = ServerUrlUtil.NormalizeServerUrl(url);
        if (!norm.Ok)
        {
            message = norm.Error ?? "서버 URL 형식이 올바르지 않습니다.";
            return false;
        }

        if (GetEquipmentId() <= 0)
        {
            message = "장비가 선택되지 않았습니다.\n메뉴 ATEC Source Trace > 서버 및 장비 설정에서 장비를 선택하세요.";
            return false;
        }

        message = string.Empty;
        return true;
    }

    public async Task OpenOptionsPageAsync()
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
            MessageBox.Show(
                "도구 > 옵션 > ATEC Source Trace > General\n\nServer URL을 입력한 뒤\nATEC Source Trace > 서버 및 장비 설정 메뉴에서 장비를 선택하세요.",
                "ATEC Source Trace 설정",
            MessageBoxButton.OK,
            MessageBoxImage.Information);
    }
}
