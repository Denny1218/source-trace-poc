using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Atec.SourceTrace.Core;

/// <summary>Minimal JSON encode/decode for Source Trace request/response shapes.</summary>
public static class JsonUtil
{
    public static string Quote(string? s)
    {
        if (s == null)
        {
            return "null";
        }

        var b = new StringBuilder("\"");
        foreach (var c in s)
        {
            switch (c)
            {
                case '\\': b.Append("\\\\"); break;
                case '"': b.Append("\\\""); break;
                case '\n': b.Append("\\n"); break;
                case '\r': b.Append("\\r"); break;
                case '\t': b.Append("\\t"); break;
                default:
                    if (c < 0x20)
                    {
                        b.AppendFormat(CultureInfo.InvariantCulture, "\\u{0:x4}", (int)c);
                    }
                    else
                    {
                        b.Append(c);
                    }
                    break;
            }
        }

        b.Append('"');
        return b.ToString();
    }

    public static string Object(Dictionary<string, object?> fields)
    {
        var b = new StringBuilder("{");
        var first = true;
        foreach (var e in fields)
        {
            if (e.Value == null)
            {
                continue;
            }

            if (!first)
            {
                b.Append(',');
            }

            first = false;
            b.Append(Quote(e.Key)).Append(':');
            switch (e.Value)
            {
                case string sv:
                    b.Append(Quote(sv));
                    break;
                case bool bv:
                    b.Append(bv ? "true" : "false");
                    break;
                case int iv:
                    b.Append(iv.ToString(CultureInfo.InvariantCulture));
                    break;
                case long lv:
                    b.Append(lv.ToString(CultureInfo.InvariantCulture));
                    break;
                default:
                    b.Append(Quote(e.Value.ToString()));
                    break;
            }
        }

        b.Append('}');
        return b.ToString();
    }

    public static string? GetStringField(string? json, string field)
    {
        if (string.IsNullOrEmpty(json) || field == null)
        {
            return null;
        }

        var key = "\"" + field + "\"";
        var idx = json.IndexOf(key, StringComparison.Ordinal);
        if (idx < 0)
        {
            return null;
        }

        var colon = json.IndexOf(':', idx + key.Length);
        if (colon < 0)
        {
            return null;
        }

        var i = colon + 1;
        while (i < json.Length && char.IsWhiteSpace(json[i]))
        {
            i++;
        }

        if (i >= json.Length)
        {
            return null;
        }

        if (json.Substring(i).StartsWith("null", StringComparison.Ordinal))
        {
            return null;
        }

        if (json[i] != '"')
        {
            var end = i;
            while (end < json.Length)
            {
                var c = json[end];
                if (c == ',' || c == '}' || c == ']')
                {
                    break;
                }

                end++;
            }

            return json.Substring(i, end - i).Trim();
        }

        return ParseQuoted(json, i);
    }

    public static int? GetIntField(string? json, string field)
    {
        var raw = GetStringField(json, field);
        if (raw == null)
        {
            return null;
        }

        if (int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out var n))
        {
            return n;
        }

        return null;
    }

    public static List<string> GetObjectArrayItems(string? json, string? arrayField)
    {
        var outList = new List<string>();
        if (string.IsNullOrEmpty(json))
        {
            return outList;
        }

        string arrayJson;
        if (arrayField == null)
        {
            arrayJson = json.Trim();
        }
        else
        {
            var key = "\"" + arrayField + "\"";
            var idx = json.IndexOf(key, StringComparison.Ordinal);
            if (idx < 0)
            {
                return outList;
            }

            var bracket = json.IndexOf('[', idx);
            if (bracket < 0)
            {
                return outList;
            }

            arrayJson = ExtractArray(json, bracket);
        }

        if (!arrayJson.StartsWith("[", StringComparison.Ordinal))
        {
            return outList;
        }

        var i = 1;
        while (i < arrayJson.Length)
        {
            while (i < arrayJson.Length && (char.IsWhiteSpace(arrayJson[i]) || arrayJson[i] == ','))
            {
                i++;
            }

            if (i >= arrayJson.Length || arrayJson[i] == ']')
            {
                break;
            }

            if (arrayJson[i] == '{')
            {
                var obj = ExtractObject(arrayJson, i);
                outList.Add(obj);
                i += obj.Length;
            }
            else
            {
                i++;
            }
        }

        return outList;
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
                if (escape)
                {
                    escape = false;
                }
                else if (c == '\\')
                {
                    escape = true;
                }
                else if (c == '"')
                {
                    inString = false;
                }

                continue;
            }

            if (c == '"')
            {
                inString = true;
            }
            else if (c == '[')
            {
                depth++;
            }
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

    private static string ExtractObject(string json, int start)
    {
        var depth = 0;
        var inString = false;
        var escape = false;
        for (var i = start; i < json.Length; i++)
        {
            var c = json[i];
            if (inString)
            {
                if (escape)
                {
                    escape = false;
                }
                else if (c == '\\')
                {
                    escape = true;
                }
                else if (c == '"')
                {
                    inString = false;
                }

                continue;
            }

            if (c == '"')
            {
                inString = true;
            }
            else if (c == '{')
            {
                depth++;
            }
            else if (c == '}')
            {
                depth--;
                if (depth == 0)
                {
                    return json.Substring(start, i - start + 1);
                }
            }
        }

        return json.Substring(start);
    }

    private static string? ParseQuoted(string json, int startQuote)
    {
        if (startQuote >= json.Length || json[startQuote] != '"')
        {
            return null;
        }

        var b = new StringBuilder();
        var escape = false;
        for (var i = startQuote + 1; i < json.Length; i++)
        {
            var c = json[i];
            if (escape)
            {
                switch (c)
                {
                    case 'n': b.Append('\n'); break;
                    case 'r': b.Append('\r'); break;
                    case 't': b.Append('\t'); break;
                    case '"': b.Append('"'); break;
                    case '\\': b.Append('\\'); break;
                    default: b.Append(c); break;
                }

                escape = false;
            }
            else if (c == '\\')
            {
                escape = true;
            }
            else if (c == '"')
            {
                return b.ToString();
            }
            else
            {
                b.Append(c);
            }
        }

        return b.ToString();
    }
}
