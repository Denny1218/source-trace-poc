using System;

namespace Atec.SourceTrace.Core;

/// <summary>Mirrors vscode-extension serverConfig normalizeServerUrl.</summary>
public static class ServerUrlUtil
{
    public sealed class NormalizeResult
    {
        public bool Ok { get; }
        public string? Url { get; }
        public string? Error { get; }

        private NormalizeResult(bool ok, string? url, string? error)
        {
            Ok = ok;
            Url = url;
            Error = error;
        }

        public static NormalizeResult Success(string url) => new(true, url, null);

        public static NormalizeResult Failure(string error) => new(false, null, error);
    }

    public static string SanitizeUrl(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
        {
            return string.Empty;
        }

        var s = raw.Trim();
        if (!Uri.TryCreate(s, UriKind.Absolute, out var u) || u.Host == null)
        {
            return s.TrimEnd('/');
        }

        var builder = new UriBuilder(u.Scheme, u.Host, u.Port > 0 ? u.Port : -1);
        return builder.Uri.GetLeftPart(UriPartial.Authority).TrimEnd('/');
    }

    public static NormalizeResult NormalizeServerUrl(string? input)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            return NormalizeResult.Failure("서버 주소를 입력해 주세요.");
        }

        var s = input.Trim();
        if (s.Contains("@") && System.Text.RegularExpressions.Regex.IsMatch(s, @"(?i)^https?://[^/]*@.*"))
        {
            return NormalizeResult.Failure(
                "서버 주소에 사용자명/비밀번호를 포함하지 마세요. 인증이 필요한 경우 관리자에게 문의하세요.");
        }

        if (!System.Text.RegularExpressions.Regex.IsMatch(s, @"(?i)^https?://.*"))
        {
            s = "http://" + s;
        }

        s = SanitizeUrl(s);
        if (!Uri.TryCreate(s, UriKind.Absolute, out var u) || string.IsNullOrEmpty(u.Host))
        {
            return NormalizeResult.Failure($"호스트명을 확인해 주세요: \"{input}\"");
        }

        var origin = u.GetLeftPart(UriPartial.Authority).TrimEnd('/');
        return NormalizeResult.Success(origin);
    }

    public static string BuildApiUrl(string? serverUrl, string path)
    {
        var baseUrl = (serverUrl ?? string.Empty).TrimEnd('/');
        if (!path.StartsWith("/", StringComparison.Ordinal))
        {
            path = "/" + path;
        }

        return baseUrl + path;
    }
}
