namespace Atec.SourceTrace.Core;

/// <summary>Backend v2.6 API paths — identical to vscode-extension serverConfig PATHS.</summary>
public static class ApiPaths
{
    public const string Health = "/api/health";
    public const string EquipmentList = "/api/equipment";
    public const string TraceReport = "/api/trace/report";
    public const string TraceSelection = "/api/trace/selection";

    public static string EquipmentById(int id) => $"{EquipmentList}/{id}";

    public static string EquipmentRepositories(int id) => $"{EquipmentList}/{id}/repositories";
}
