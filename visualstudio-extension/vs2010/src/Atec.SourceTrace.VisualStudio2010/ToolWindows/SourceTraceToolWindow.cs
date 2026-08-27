using Microsoft.VisualStudio.Shell;
using System.Runtime.InteropServices;

namespace Atec.SourceTrace.VisualStudio2010.ToolWindows
{
    [Guid(PackageGuids.ToolWindowString)]
    public sealed class SourceTraceToolWindow : ToolWindowPane
    {
        public SourceTraceToolWindow() : base(null)
        {
            Caption = "ATEC Source Trace";
            Content = new SourceTraceToolWindowControl();
        }

        public void ShowMarkdown(string markdown, string titleHint)
        {
            var ctrl = Content as SourceTraceToolWindowControl;
            if (ctrl != null)
            {
                ctrl.ShowMarkdown(markdown, titleHint);
            }
        }
    }
}
