using System;
using System.Text;
using System.Text.RegularExpressions;

namespace Atec.SourceTrace.Core;

/// <summary>Small Markdown → HTML for offline Tool Window display (no CDN).</summary>
public static class MarkdownHtml
{
    public static string ToHtmlDocument(string? markdown, string? title)
    {
        var body = ToHtmlBody(markdown ?? string.Empty);
        var safeTitle = Escape(title ?? "ATEC Source Trace");
        return "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/><title>"
               + safeTitle
               + "</title><style>"
               + "body{font-family:Consolas,'Malgun Gothic',sans-serif;font-size:13px;"
               + "line-height:1.45;padding:12px;color:#1a1a1a;background:#fafafa;}"
               + "pre,code{font-family:Consolas,monospace;background:#f0f0f0;}"
               + "pre{padding:8px;overflow:auto;border:1px solid #ddd;}"
               + "table{border-collapse:collapse;margin:8px 0;}"
               + "th,td{border:1px solid #ccc;padding:4px 8px;vertical-align:top;}"
               + "h1,h2,h3{margin:12px 0 6px;}"
               + "hr{border:none;border-top:1px solid #ccc;margin:12px 0;}"
               + "details{margin:8px 0;}"
               + "</style></head><body>"
               + body
               + "</body></html>";
    }

    public static string ToHtmlBody(string md)
    {
        var lines = md.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');
        var outSb = new StringBuilder();
        var inCode = false;
        var inTable = false;
        var code = new StringBuilder();
        foreach (var line in lines)
        {
            if (line.StartsWith("```", StringComparison.Ordinal))
            {
                if (inCode)
                {
                    outSb.Append("<pre><code>").Append(Escape(code.ToString())).Append("</code></pre>\n");
                    code.Clear();
                    inCode = false;
                }
                else
                {
                    if (inTable)
                    {
                        outSb.Append("</table>\n");
                        inTable = false;
                    }

                    inCode = true;
                }

                continue;
            }

            if (inCode)
            {
                if (code.Length > 0)
                {
                    code.Append('\n');
                }

                code.Append(line);
                continue;
            }

            var trimmed = line.Trim();
            if (trimmed.StartsWith("|", StringComparison.Ordinal) && trimmed.EndsWith("|", StringComparison.Ordinal))
            {
                if (IsTableSep(line))
                {
                    continue;
                }

                if (!inTable)
                {
                    outSb.Append("<table>\n");
                    inTable = true;
                }

                outSb.Append("<tr>");
                var cells = trimmed.Substring(1, trimmed.Length - 2).Split('|');
                foreach (var cell in cells)
                {
                    outSb.Append("<td>").Append(Inline(cell.Trim())).Append("</td>");
                }

                outSb.Append("</tr>\n");
                continue;
            }

            if (inTable)
            {
                outSb.Append("</table>\n");
                inTable = false;
            }

            if (line.StartsWith("# ", StringComparison.Ordinal))
            {
                outSb.Append("<h1>").Append(Inline(line.Substring(2))).Append("</h1>\n");
            }
            else if (line.StartsWith("## ", StringComparison.Ordinal))
            {
                outSb.Append("<h2>").Append(Inline(line.Substring(3))).Append("</h2>\n");
            }
            else if (line.StartsWith("### ", StringComparison.Ordinal))
            {
                outSb.Append("<h3>").Append(Inline(line.Substring(4))).Append("</h3>\n");
            }
            else if (trimmed == "---")
            {
                outSb.Append("<hr/>\n");
            }
            else if (trimmed.Length == 0)
            {
                outSb.Append("<br/>\n");
            }
            else
            {
                outSb.Append("<p>").Append(Inline(line)).Append("</p>\n");
            }
        }

        if (inCode)
        {
            outSb.Append("<pre><code>").Append(Escape(code.ToString())).Append("</code></pre>\n");
        }

        if (inTable)
        {
            outSb.Append("</table>\n");
        }

        return outSb.ToString();
    }

    private static bool IsTableSep(string line)
    {
        var t = line.Replace("|", string.Empty).Replace("-", string.Empty)
            .Replace(":", string.Empty).Replace(" ", string.Empty);
        return t.Length == 0;
    }

    private static string Inline(string s)
    {
        var e = Escape(s);
        e = Regex.Replace(e, "`([^`]+)`", "<code>$1</code>");
        e = Regex.Replace(e, "\\*\\*([^*]+)\\*\\*", "<strong>$1</strong>");
        return e;
    }

    public static string Escape(string? s)
    {
        if (s == null)
        {
            return string.Empty;
        }

        return s.Replace("&", "&amp;")
            .Replace("<", "&lt;")
            .Replace(">", "&gt;")
            .Replace("\"", "&quot;");
    }
}
