using EnvDTE;
using EnvDTE80;
using Microsoft.VisualStudio.Shell;
using System;
using System.IO;

namespace Atec.SourceTrace.VisualStudio2010.Services
{
    public sealed class EditorBridge
    {
        private readonly AtecSourceTracePackage _package;

        public EditorBridge(AtecSourceTracePackage package)
        {
            _package = package;
        }

        public sealed class Snapshot
        {
            public string FilePath { get; set; }
            public string SelectedText { get; set; }
            public bool HasSelection { get; set; }
            public int StartLine1 { get; set; }
            public int EndLine1 { get; set; }
            public int StartLine0 { get { return Math.Max(0, StartLine1 - 1); } }
            public string CursorWord { get; set; }
            public string CurrentLineText { get; set; }
            public string[] Lines { get; set; }
            public bool IsSaved { get; set; }

            public Snapshot()
            {
                FilePath = string.Empty;
                SelectedText = string.Empty;
                CursorWord = string.Empty;
                CurrentLineText = string.Empty;
                Lines = new string[0];
            }
        }

        public Snapshot CaptureActiveEditor()
        {
            var dte = _package.QueryService(typeof(DTE)) as DTE2;
            if (dte == null || dte.ActiveDocument == null)
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
            if (!IsCppLikeExtension(ext))
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
                CursorWord = cursorWord == null ? string.Empty : cursorWord.Trim(),
                CurrentLineText = currentLineText,
                Lines = lines,
                IsSaved = doc.Saved,
            };
        }

        private static bool IsCppLikeExtension(string ext)
        {
            switch (ext)
            {
                case ".c":
                case ".cpp":
                case ".cc":
                case ".cxx":
                case ".h":
                case ".hpp":
                case ".hh":
                case ".hxx":
                    return true;
                default:
                    return false;
            }
        }
    }
}
