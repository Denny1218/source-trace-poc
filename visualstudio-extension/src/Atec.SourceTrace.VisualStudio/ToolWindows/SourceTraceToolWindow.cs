using Microsoft.VisualStudio.Shell;
using System;
using System.Runtime.InteropServices;

namespace Atec.SourceTrace.VisualStudio.ToolWindows;

[Guid(PackageGuids.ToolWindowString)]
public sealed class SourceTraceToolWindow : ToolWindowPane
{
    public SourceTraceToolWindow() : base(null)
    {
        Caption = "ATEC Source Trace";
    }

    protected override void Initialize()
    {
        base.Initialize();
        Content = new SourceTraceToolWindowControl();
    }

    public void ShowMarkdown(string markdown, string titleHint)
    {
        if (Content is SourceTraceToolWindowControl ctrl)
        {
            ctrl.ShowMarkdown(markdown, titleHint);
        }
    }
}
