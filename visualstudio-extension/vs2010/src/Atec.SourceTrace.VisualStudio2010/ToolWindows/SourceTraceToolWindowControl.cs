using Atec.SourceTrace.Core;
using System.Windows.Controls;

namespace Atec.SourceTrace.VisualStudio2010.ToolWindows
{
    public sealed class SourceTraceToolWindowControl : UserControl
    {
        private readonly WebBrowser _browser = new WebBrowser();

        public SourceTraceToolWindowControl()
        {
            Content = _browser;
        }

        public void ShowMarkdown(string markdown, string titleHint)
        {
            var title = "ATEC Source Trace";
            if (!string.IsNullOrEmpty(markdown) && markdown.StartsWith("# ", System.StringComparison.Ordinal))
            {
                var nl = markdown.IndexOf('\n');
                title = nl > 2 ? markdown.Substring(2, nl - 2).Trim() : titleHint;
            }

            _browser.NavigateToString(MarkdownHtml.ToHtmlDocument(markdown, title));
        }
    }
}
