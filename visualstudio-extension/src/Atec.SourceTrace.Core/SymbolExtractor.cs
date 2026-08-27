using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace Atec.SourceTrace.Core;

/// <summary>Port of vscode-extension symbolExtractor.ts.</summary>
public static class SymbolExtractor
{
    private static readonly Regex CIdent = new(@"^[A-Za-z_][A-Za-z0-9_]*$", RegexOptions.Compiled);
    private static readonly Regex CFuncDef = new(
        @"(?:\b(?:static|inline|extern|const|unsigned|signed|volatile)\s+)*(?:struct\s+\w+\s+)?\b([A-Za-z_][A-Za-z0-9_]*)\b[ \t]*\*{0,2}[ \t]*\(",
        RegexOptions.Compiled);
    private static readonly Regex CFuncCall = new(@"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", RegexOptions.Compiled);
    private static readonly Regex ControlBlock = new(@"^\s*(if|for|while|switch)\b", RegexOptions.Compiled);

    private static readonly HashSet<string> CKeywords = new(StringComparer.OrdinalIgnoreCase)
    {
        "if", "else", "for", "while", "do", "switch", "case", "break", "continue", "return", "goto",
        "sizeof", "typedef", "struct", "union", "enum", "static", "extern", "inline", "const",
        "volatile", "unsigned", "signed", "void", "int", "char", "short", "long", "float", "double",
        "bool", "true", "false", "NULL"
    };

    public static string? ExtractDetectedSymbol(string? selectedText)
    {
        if (selectedText == null)
        {
            return null;
        }

        var raw = selectedText.Trim();
        if (raw.Length == 0)
        {
            return null;
        }

        if (CIdent.IsMatch(raw) && !CKeywords.Contains(raw))
        {
            return raw;
        }

        var defMatch = CFuncDef.Match(raw);
        if (defMatch.Success)
        {
            var name = defMatch.Groups[1].Value;
            if (!CKeywords.Contains(name))
            {
                return name;
            }
        }

        foreach (Match callMatch in CFuncCall.Matches(raw))
        {
            var name = callMatch.Groups[1].Value;
            if (!CKeywords.Contains(name))
            {
                return name;
            }
        }

        return null;
    }

    /// <param name="lines">Document lines (0-based index).</param>
    /// <param name="startLine">0-based line index of selection start.</param>
    public static string? FindEnclosingFunctionSymbol(string[]? lines, int startLine)
    {
        if (lines == null || lines.Length == 0)
        {
            return null;
        }

        var pendingCloses = 0;
        var start = Math.Min(Math.Max(startLine, 0), lines.Length - 1);
        var limit = Math.Max(0, start - 4000);
        for (var i = start; i >= limit; i--)
        {
            var line = lines[i] ?? string.Empty;
            for (var ci = line.Length - 1; ci >= 0; ci--)
            {
                var ch = line[ci];
                if (ch == '}')
                {
                    pendingCloses++;
                }
                else if (ch == '{')
                {
                    if (pendingCloses > 0)
                    {
                        pendingCloses--;
                        continue;
                    }

                    var beforeBrace = line.Substring(0, ci);
                    var sigText = beforeBrace.Trim().Length > 0
                        ? beforeBrace
                        : FindPrecedingNonBlankLine(lines, i) ?? string.Empty;

                    if (ControlBlock.IsMatch(sigText))
                    {
                        continue;
                    }

                    var match = CFuncDef.Match(sigText);
                    if (match.Success)
                    {
                        var name = match.Groups[1].Value;
                        if (!CKeywords.Contains(name))
                        {
                            return name;
                        }
                    }
                }
            }
        }

        return null;
    }

    private static string? FindPrecedingNonBlankLine(string[] lines, int fromIndex)
    {
        for (var j = fromIndex - 1; j >= 0 && j >= fromIndex - 5; j--)
        {
            var candidate = lines[j] ?? string.Empty;
            if (candidate.Trim().Length > 0)
            {
                return candidate;
            }
        }

        return null;
    }

    public static string AugmentQueryWithSymbol(string? query, string? symbol)
    {
        var q = (query ?? string.Empty).Trim();
        if (string.IsNullOrEmpty(symbol) || q.Length == 0)
        {
            return q;
        }

        if (q.IndexOf(symbol, StringComparison.Ordinal) >= 0)
        {
            return q;
        }

        var pronounReplaced = Regex.Replace(q, @"이\s*함수", symbol + " 함수");
        if (!pronounReplaced.Equals(q, StringComparison.Ordinal))
        {
            return pronounReplaced;
        }

        return symbol + " " + q;
    }
}
