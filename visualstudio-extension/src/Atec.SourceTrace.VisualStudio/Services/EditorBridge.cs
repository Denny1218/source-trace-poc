using EnvDTE;
using EnvDTE80;
using Microsoft.VisualStudio.Shell;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Task = System.Threading.Tasks.Task;

namespace Atec.SourceTrace.VisualStudio.Services;

public sealed class EditorBridge
{
    private readonly AsyncPackage _package;

    public EditorBridge(AsyncPackage package)
    {
        _package = package;
    }

    public sealed class Snapshot
    {
        public string FilePath { get; set; } = string.Empty;
        public string SelectedText { get; set; } = string.Empty;
        public bool HasSelection { get; set; }
        public int StartLine1 { get; set; }
        public int EndLine1 { get; set; }
        public int StartLine0 => Math.Max(0, StartLine1 - 1);
        public int EndLine0 => Math.Max(0, EndLine1 - 1);
        public string CursorWord { get; set; } = string.Empty;
        public string CurrentLineText { get; set; } = string.Empty;
        public string[] Lines { get; set; } = Array.Empty<string>();
        public bool IsCppLike { get; set; }
        public bool IsSaved { get; set; }
    }

    public async Task<Snapshot?> CaptureActiveEditorAsync()
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        var dte = await _package.GetServiceAsync(typeof(DTE)) as DTE2;
        if (dte?.ActiveDocument == null)
        {
            return null;
        }

        var doc = dte.ActiveDocument;
        var fullName = doc.FullName;
        if (string.IsNullOrWhiteSpace(fullName) || fullName.StartsWith("Untitled", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var ext = Path.GetExtension(fullName).ToLowerInvariant();
        var cppLike = ext is ".c" or ".cpp" or ".cc" or ".cxx" or ".h" or ".hpp" or ".hh" or ".hxx";
        if (!cppLike)
        {
            return null;
        }

        var textDoc = doc.Object("TextDocument") as TextDocument;
        if (textDoc == null)
        {
            return null;
        }

        var content = textDoc.StartPoint.CreateEditPoint().GetText(textDoc.EndPoint);
        var lines = content.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');

        var sel = dte.ActiveDocument.Selection as TextSelection;
        var selectedText = string.Empty;
        var hasSelection = false;
        var startLine1 = 1;
        var endLine1 = 1;
        var cursorWord = string.Empty;
        var currentLineText = string.Empty;

        if (sel != null)
        {
            startLine1 = sel.ActivePoint.Line;
            endLine1 = sel.ActivePoint.Line;
            if (!sel.IsEmpty)
            {
                hasSelection = true;
                startLine1 = Math.Min(sel.AnchorPoint.Line, sel.ActivePoint.Line);
                endLine1 = Math.Max(sel.AnchorPoint.Line, sel.ActivePoint.Line);
                selectedText = sel.Text ?? string.Empty;
            }

            try
            {
                cursorWord = sel.Text ?? string.Empty;
                if (string.IsNullOrWhiteSpace(cursorWord))
                {
                    var wordSel = sel.ActivePoint.CreateEditPoint();
                    wordSel.WordRight(1);
                    cursorWord = sel.ActivePoint.CreateEditPoint().GetText(wordSel);
                }
            }
            catch
            {
                cursorWord = string.Empty;
            }

            if (startLine1 >= 1 && startLine1 <= lines.Length)
            {
                currentLineText = lines[startLine1 - 1];
            }
        }

        return new Snapshot
        {
            FilePath = fullName,
            SelectedText = selectedText,
            HasSelection = hasSelection && !string.IsNullOrWhiteSpace(selectedText),
            StartLine1 = startLine1,
            EndLine1 = endLine1,
            CursorWord = cursorWord?.Trim() ?? string.Empty,
            CurrentLineText = currentLineText,
            Lines = lines,
            IsCppLike = cppLike,
            IsSaved = doc.Saved,
        };
    }
}
