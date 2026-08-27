using System;
using System.Collections.Generic;
using System.Text;

namespace Atec.SourceTrace.Core;

/// <summary>Parses FastAPI/Pydantic 422 detail arrays into short UI messages.</summary>
public static class FastApiErrorParser
{
    public sealed class DetailItem
    {
        public string? Type { get; }
        public string? Loc { get; }
        public string? Msg { get; }

        public DetailItem(string? type, string? loc, string? msg)
        {
            Type = type;
            Loc = loc;
            Msg = msg;
        }
    }

    public static List<DetailItem> ParseDetail(string? responseBody)
    {
        var outList = new List<DetailItem>();
        if (string.IsNullOrWhiteSpace(responseBody))
        {
            return outList;
        }

        var trimmed = responseBody.Trim();
        var arrayJson = trimmed;
        if (trimmed.StartsWith("{", StringComparison.Ordinal))
        {
            var detailIdx = trimmed.IndexOf("\"detail\"", StringComparison.Ordinal);
            if (detailIdx >= 0)
            {
                var bracket = trimmed.IndexOf('[', detailIdx);
                if (bracket >= 0)
                {
                    arrayJson = ExtractArray(trimmed, bracket);
                }
            }
        }

        if (!arrayJson.StartsWith("[", StringComparison.Ordinal))
        {
            return outList;
        }

        foreach (var obj in JsonUtil.GetObjectArrayItems("{\"items\":" + arrayJson + "}", "items"))
        {
            outList.Add(new DetailItem(
                JsonUtil.GetStringField(obj, "type"),
                FormatLoc(obj),
                JsonUtil.GetStringField(obj, "msg")));
        }

        if (outList.Count == 0)
        {
            foreach (var obj in JsonUtil.GetObjectArrayItems(arrayJson, null))
            {
                var type = JsonUtil.GetStringField(obj, "type");
                var msg = JsonUtil.GetStringField(obj, "msg");
                var loc = FormatLoc(obj);
                if (type != null || msg != null)
                {
                    outList.Add(new DetailItem(type, loc, msg));
                }
            }
        }

        return outList;
    }

    public static string FormatUserMessage(string action, int httpStatus, string? responseBody)
    {
        var items = ParseDetail(responseBody);
        var b = new StringBuilder();
        b.Append(action).Append("에 실패했습니다. (HTTP ").Append(httpStatus).Append(")\n\n");
        if (items.Count == 0)
        {
            b.Append("서버가 요청을 거부했습니다.");
            if (!string.IsNullOrWhiteSpace(responseBody))
            {
                var preview = responseBody.Length > 200 ? responseBody.Substring(0, 200) + "…" : responseBody;
                b.Append('\n').Append(preview);
            }

            return b.ToString();
        }

        var bodyMissing = items.Exists(i =>
            i.Type == "missing" && (string.IsNullOrEmpty(i.Loc) || i.Loc == "body"));
        b.Append(bodyMissing
            ? "요청 본문(JSON body)이 서버에 전달되지 않았습니다.\n"
            : "요청 데이터가 서버 형식과 맞지 않습니다.\n");
        b.Append("상세:");
        foreach (var i in items)
        {
            b.Append("\n- ");
            if (!string.IsNullOrEmpty(i.Loc))
            {
                b.Append(i.Loc);
                if (!string.IsNullOrEmpty(i.Msg))
                {
                    b.Append(" — ").Append(i.Msg);
                }
            }
            else if (!string.IsNullOrEmpty(i.Msg))
            {
                b.Append(i.Msg);
            }
            else
            {
                b.Append(i.Type);
            }
        }

        return b.ToString();
    }

    private static string ExtractArray(string json, int startBracket)
    {
        var depth = 0;
        var inString = false;
        var escape = false;
        for (var i = startBracket; i < json.Length; i++)
        {
            var c = json[i];
            if (inString)
            {
                if (escape) escape = false;
                else if (c == '\\') escape = true;
                else if (c == '"') inString = false;
                continue;
            }

            if (c == '"') inString = true;
            else if (c == '[') depth++;
            else if (c == ']')
            {
                depth--;
                if (depth == 0)
                {
                    return json.Substring(startBracket, i - startBracket + 1);
                }
            }
        }

        return json.Substring(startBracket);
    }

    private static string FormatLoc(string obj)
    {
        var locIdx = obj.IndexOf("\"loc\"", StringComparison.Ordinal);
        if (locIdx < 0)
        {
            return string.Empty;
        }

        var arr = obj.IndexOf('[', locIdx);
        if (arr < 0)
        {
            return string.Empty;
        }

        var arrText = ExtractArray(obj, arr);
        var parts = new List<string>();
        var cur = new StringBuilder();
        var inString = false;
        var escape = false;
        foreach (var c in arrText)
        {
            if (inString)
            {
                if (escape)
                {
                    cur.Append(c);
                    escape = false;
                }
                else if (c == '\\')
                {
                    escape = true;
                }
                else if (c == '"')
                {
                    inString = false;
                    parts.Add(cur.ToString());
                    cur.Clear();
                }
                else
                {
                    cur.Append(c);
                }
            }
            else if (c == '"')
            {
                inString = true;
            }
        }

        return parts.Count == 0 ? arrText : string.Join(".", parts);
    }
}
