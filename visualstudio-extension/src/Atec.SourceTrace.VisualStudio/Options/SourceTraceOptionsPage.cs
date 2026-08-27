using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.VisualStudio.Shell;

namespace Atec.SourceTrace.VisualStudio.Options;

[Guid("a1b2c3d4-e5f6-7890-abcd-ef1234567891")]
public class SourceTraceOptionsPage : DialogPage
{
    private string _serverUrl = string.Empty;
    private int _equipmentId;
    private string _equipmentName = string.Empty;
    private bool _useOllama;

    [Category("Source Trace")]
    [DisplayName("Server URL")]
    [Description("Source Trace Backend origin (예: http://192.168.x.x:8010). API 경로는 자동으로 붙입니다.")]
    public string ServerUrl
    {
        get => _serverUrl;
        set => _serverUrl = value ?? string.Empty;
    }

    [Browsable(false)]
    public int EquipmentId
    {
        get => _equipmentId;
        set => _equipmentId = value;
    }

    [Category("Source Trace")]
    [DisplayName("장비")]
    [Description("선택된 장비명. ATEC Source Trace > 서버 및 장비 설정 메뉴에서 목록으로 선택하세요.")]
    [ReadOnly(true)]
    public string EquipmentName
    {
        get
        {
            if (_equipmentId <= 0) return "(선택 안 됨)";
            return string.IsNullOrEmpty(_equipmentName)
                ? $"(ID {_equipmentId})"
                : $"{_equipmentName} (ID: {_equipmentId})";
        }
        set => _equipmentName = value ?? string.Empty;
    }

    [Category("Source Trace")]
    [DisplayName("Use Ollama")]
    [Description("함수 변경 이력 조회 시 use_ollama=true 전송 (Backend 기본 정책과 동일).")]
    public bool UseOllama
    {
        get => _useOllama;
        set => _useOllama = value;
    }
}
