using System;
using System.Collections.Generic;

namespace Atec.SourceTrace.Core;

/// <summary>Port of vscode-extension editorContext.ts resolveEditorContext.</summary>
public static class EditorContextResolver
{
    public enum SourceMode
    {
        Selection,
        SelectionSymbol,
        CursorWord,
        RecentSelectionFallback,
        None
    }

    public sealed class Resolved
    {
        public string SelectedText { get; }
        public SourceMode SourceMode { get; }
        public string? DetectedSymbol { get; }

        public Resolved(string selectedText, SourceMode sourceMode, string? detectedSymbol)
        {
            SelectedText = selectedText;
            SourceMode = sourceMode;
            DetectedSymbol = detectedSymbol;
        }

        public string SourceModeWire => SourceMode switch
        {
            SourceMode.Selection => "selection",
            SourceMode.SelectionSymbol => "selection_symbol",
            SourceMode.CursorWord => "cursor_word",
            SourceMode.RecentSelectionFallback => "recent_selection_fallback",
            _ => "none"
        };
    }

    public static Resolved? Resolve(
        string? immediateSelectionText,
        string? recentSelectionText,
        string? cursorWord,
        string? currentLineText)
    {
        var immediate = Trim(immediateSelectionText);
        if (immediate.Length > 0)
        {
            return FromText(immediate, SourceMode.Selection);
        }

        var recent = Trim(recentSelectionText);
        if (recent.Length > 0)
        {
            var r = FromText(recent, SourceMode.RecentSelectionFallback);
            return new Resolved(r.SelectedText, SourceMode.RecentSelectionFallback, r.DetectedSymbol);
        }

        var word = Trim(cursorWord);
        if (word.Length > 0 && SymbolExtractor.ExtractDetectedSymbol(word) != null)
        {
            return new Resolved(word, SourceMode.CursorWord, word);
        }

        var line = Trim(currentLineText);
        if (line.Length > 0)
        {
            var symbol = SymbolExtractor.ExtractDetectedSymbol(line);
            if (symbol != null)
            {
                return new Resolved(line, SourceMode.CursorWord, symbol);
            }
        }

        return null;
    }

    private static Resolved FromText(string text, SourceMode baseMode)
    {
        var trimmed = text.Trim();
        var symbol = SymbolExtractor.ExtractDetectedSymbol(trimmed);
        var isSingleSymbol = symbol != null && trimmed.Equals(symbol, StringComparison.Ordinal);
        return new Resolved(
            trimmed,
            isSingleSymbol ? SourceMode.SelectionSymbol : baseMode,
            symbol);
    }

    private static string Trim(string? s) => (s ?? string.Empty).Trim();
}
