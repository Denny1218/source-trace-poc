using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Text;

namespace Atec.SourceTrace.Core;

/// <summary>
/// HTTP client using HttpWebRequest with fixed-length UTF-8 POST bodies
/// (prevents FastAPI 422 missing body).
/// </summary>
public sealed class TraceHttpClient
{
    public sealed class HttpResult
    {
        public int Status { get; }
        public string? Body { get; }
        public string? Error { get; }

        public HttpResult(int status, string? body, string? error)
        {
            Status = status;
            Body = body;
            Error = error;
        }

        public bool Ok => Error == null && Status >= 200 && Status < 300;
    }

    public sealed class EquipmentItem
    {
        public int Id { get; }
        public string Name { get; }

        public EquipmentItem(int id, string name)
        {
            Id = id;
            Name = name;
        }

        public override string ToString() => $"{Name} (ID {Id})";
    }

    public sealed class RepoItem
    {
        public int Id { get; }
        public string Name { get; }
        public string? Status { get; }

        public RepoItem(int id, string name, string? status)
        {
            Id = id;
            Name = name;
            Status = status;
        }

        public override string ToString() =>
            $"{Name} (#{Id})" + (Status != null ? $" [{Status}]" : string.Empty);
    }

    private readonly int _timeoutMs;

    public TraceHttpClient(TimeSpan? timeout = null)
    {
        var t = timeout ?? TimeSpan.FromSeconds(180);
        _timeoutMs = (int)Math.Min(int.MaxValue, Math.Max(1000, t.TotalMilliseconds));
    }

    public HttpResult Get(string url) => Send(url, "GET", null);

    public HttpResult PostJson(string url, string? jsonBody)
    {
        var payload = NormalizeJsonBody(jsonBody);
        return Send(url, "POST", payload);
    }

    public static string NormalizeJsonBody(string? jsonBody)
    {
        return string.IsNullOrWhiteSpace(jsonBody) ? "{}" : jsonBody;
    }

    private HttpResult Send(string url, string method, string? jsonPayload)
    {
        try
        {
            var request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = method;
            request.Accept = "application/json";
            request.Timeout = _timeoutMs;
            request.ReadWriteTimeout = _timeoutMs;
            request.AllowAutoRedirect = false;

            if (method == "POST")
            {
                var bytes = Encoding.UTF8.GetBytes(jsonPayload ?? "{}");
                request.ContentType = "application/json; charset=utf-8";
                request.ContentLength = bytes.Length;
                using (var stream = request.GetRequestStream())
                {
                    stream.Write(bytes, 0, bytes.Length);
                    stream.Flush();
                }
            }

            using var response = (HttpWebResponse)request.GetResponse();
            var body = ReadResponseBody(response);
            return new HttpResult((int)response.StatusCode, body, null);
        }
        catch (WebException ex) when (ex.Response is HttpWebResponse err)
        {
            var body = ReadResponseBody(err);
            return new HttpResult((int)err.StatusCode, body, null);
        }
        catch (Exception ex)
        {
            return new HttpResult(-1, null, ex.Message);
        }
    }

    private static string ReadResponseBody(HttpWebResponse response)
    {
        var stream = response.GetResponseStream();
        if (stream == null)
        {
            return string.Empty;
        }

        using var reader = new StreamReader(stream, Encoding.UTF8);
        return reader.ReadToEnd();
    }

    public HttpResult Health(string serverUrl) =>
        Get(ServerUrlUtil.BuildApiUrl(serverUrl, ApiPaths.Health));

    public List<EquipmentItem> ListEquipment(string serverUrl)
    {
        var r = Get(ServerUrlUtil.BuildApiUrl(serverUrl, ApiPaths.EquipmentList));
        if (!r.Ok)
        {
            throw new Exception(FormatHttpError("장비 목록 조회", r));
        }

        var outList = new List<EquipmentItem>();
        foreach (var obj in JsonUtil.GetObjectArrayItems(r.Body, null))
        {
            var id = JsonUtil.GetIntField(obj, "id");
            var name = JsonUtil.GetStringField(obj, "name") ?? string.Empty;
            if (id.HasValue)
            {
                outList.Add(new EquipmentItem(id.Value, name));
            }
        }

        return outList;
    }

    public List<RepoItem> ListRepositories(string serverUrl, int equipmentId)
    {
        var r = Get(ServerUrlUtil.BuildApiUrl(serverUrl, ApiPaths.EquipmentRepositories(equipmentId)));
        if (!r.Ok)
        {
            throw new Exception(FormatHttpError("Repository 목록 조회", r));
        }

        var outList = new List<RepoItem>();
        foreach (var obj in JsonUtil.GetObjectArrayItems(r.Body, null))
        {
            var id = JsonUtil.GetIntField(obj, "id");
            var name = JsonUtil.GetStringField(obj, "name") ?? string.Empty;
            var status = JsonUtil.GetStringField(obj, "status");
            if (id.HasValue)
            {
                outList.Add(new RepoItem(id.Value, name, status));
            }
        }

        return outList;
    }

    public HttpResult PostReport(string serverUrl, string jsonBody) =>
        PostJson(ServerUrlUtil.BuildApiUrl(serverUrl, ApiPaths.TraceReport), jsonBody);

    public HttpResult PostSelection(string serverUrl, string jsonBody) =>
        PostJson(ServerUrlUtil.BuildApiUrl(serverUrl, ApiPaths.TraceSelection), jsonBody);

    public static string FormatHttpError(string action, HttpResult r)
    {
        if (r.Error != null)
        {
            return action + " 실패: 서버에 연결할 수 없습니다. (" + r.Error + ")";
        }

        if (r.Status == 422)
        {
            return FastApiErrorParser.FormatUserMessage(action, r.Status, r.Body);
        }

        var detail = r.Body ?? string.Empty;
        var msg = JsonUtil.GetStringField(detail, "detail")
                  ?? JsonUtil.GetStringField(detail, "content")
                  ?? (detail.Length > 300 ? detail.Substring(0, 300) : detail);
        return action + "에 실패했습니다. (HTTP " + r.Status + ")\n" + msg;
    }

    public static string UserFacingConnectionError(string? detail) =>
        "Backend 서버에 연결할 수 없습니다. Source Trace 서버 URL 설정을 확인하세요."
        + (string.IsNullOrEmpty(detail) ? string.Empty : "\n원인: " + detail);
}
