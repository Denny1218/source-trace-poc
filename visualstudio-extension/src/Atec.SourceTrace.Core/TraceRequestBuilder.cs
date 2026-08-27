using System;
using System.Collections.Generic;

namespace Atec.SourceTrace.Core;

/// <summary>Builds request JSON for Backend v2.6 — mirrors vscode-extension requestBuilder.ts.</summary>
public static class TraceRequestBuilder
{
    public const int DefaultMaxSelectedChars = 4000;
    public const string DefaultQuery = "선택한 코드가 왜 변경됐는지 알려줘";

    public sealed class TruncateResult
    {
        public string Code { get; }
        public bool Truncated { get; }

        public TruncateResult(string code, bool truncated)
        {
            Code = code;
            Truncated = truncated;
        }
    }

    public sealed class BuiltRequest
    {
        public string JsonBody { get; }
        public bool Truncated { get; }

        public BuiltRequest(string jsonBody, bool truncated)
        {
            JsonBody = jsonBody;
            Truncated = truncated;
        }
    }

    public static TruncateResult TruncateSelectedCode(string? code, int maxChars)
    {
        if (code == null)
        {
            return new TruncateResult(string.Empty, false);
        }

        if (code.Length <= maxChars)
        {
            return new TruncateResult(code, false);
        }

        return new TruncateResult(code.Substring(0, maxChars), true);
    }

    public static BuiltRequest BuildReportRequest(
        int equipmentId,
        string? query,
        string filePath,
        string? selectedCode,
        string? detectedSymbol,
        string? sourceMode,
        bool useOllama,
        int maxSelectedCodeChars)
    {
        var selectedText = (selectedCode ?? string.Empty).Trim();
        var symbol = string.IsNullOrWhiteSpace(detectedSymbol) ? null : detectedSymbol.Trim();
        var selectedForBody = selectedText.Length > 0 ? selectedText : (symbol ?? string.Empty);
        var augmentedQuery = SymbolExtractor.AugmentQueryWithSymbol(
            string.IsNullOrWhiteSpace(query) ? DefaultQuery : query.Trim(),
            symbol);
        var sent = TruncateSelectedCode(selectedForBody, maxSelectedCodeChars);

        var body = new Dictionary<string, object?>
        {
            ["equipment_id"] = equipmentId,
            ["query"] = augmentedQuery,
            ["file_path"] = filePath,
            ["selected_code"] = sent.Code,
            ["use_ollama"] = useOllama,
        };

        if (!string.IsNullOrEmpty(sourceMode))
        {
            body["source_mode"] = sourceMode;
        }

        if (symbol != null)
        {
            body["detected_symbol"] = symbol;
        }

        var json = JsonUtil.Object(body);
        if (string.IsNullOrWhiteSpace(json) || json == "{}")
        {
            throw new InvalidOperationException("report request body가 비어 있습니다.");
        }

        if (!json.Contains("\"equipment_id\""))
        {
            throw new InvalidOperationException("report request에 equipment_id가 없습니다.");
        }

        return new BuiltRequest(json, sent.Truncated);
    }

    public static BuiltRequest BuildSelectionRequest(
        int equipmentId,
        string? repoRelativePath,
        int? repoIdHint,
        string? clientFilePath,
        int startLine,
        int endLine,
        string? selectedCode,
        string? enclosingSymbol,
        int maxSelectedCodeChars,
        string? revision)
    {
        var sent = TruncateSelectedCode(selectedCode ?? string.Empty, maxSelectedCodeChars);
        var body = new Dictionary<string, object?>
        {
            ["equipment_id"] = equipmentId,
            ["start_line"] = startLine,
            ["end_line"] = endLine,
            ["selected_code"] = sent.Code,
            ["revision"] = string.IsNullOrWhiteSpace(revision) ? "HEAD" : revision.Trim(),
        };

        if (!string.IsNullOrWhiteSpace(enclosingSymbol))
        {
            body["enclosing_symbol"] = enclosingSymbol.Trim();
        }

        var rel = (repoRelativePath ?? string.Empty).Trim().Replace('\\', '/');
        if (rel.Length > 0)
        {
            body["repo_relative_path"] = rel;
            if (repoIdHint.HasValue && repoIdHint.Value > 0)
            {
                body["repo_id"] = repoIdHint.Value;
                body["repo_id_hint"] = repoIdHint.Value;
            }

            if (!string.IsNullOrWhiteSpace(clientFilePath))
            {
                body["client_file_path"] = clientFilePath;
            }
        }
        else if (!string.IsNullOrWhiteSpace(clientFilePath))
        {
            body["file_path"] = clientFilePath;
        }

        return new BuiltRequest(JsonUtil.Object(body), sent.Truncated);
    }

    public static string PickResultMarkdown(string? responseJson)
    {
        if (string.IsNullOrWhiteSpace(responseJson))
        {
            return "(빈 응답)";
        }

        foreach (var key in new[] { "content", "answer", "evidence_answer" })
        {
            var value = JsonUtil.GetStringField(responseJson, key);
            if (!string.IsNullOrWhiteSpace(value))
            {
                return value;
            }
        }

        return "```json\n" + responseJson + "\n```";
    }

    public static bool LooksLikeAmbiguity(string? messageOrBody)
    {
        if (string.IsNullOrEmpty(messageOrBody))
        {
            return false;
        }

        return messageOrBody.Contains("여러 장비 Repository")
               || messageOrBody.IndexOf("AMBIGUOUS", StringComparison.OrdinalIgnoreCase) >= 0
               || messageOrBody.Contains("하나를 결정할 수 없")
               || messageOrBody.Contains("동일한 파일 경로가 여러");
    }
}
