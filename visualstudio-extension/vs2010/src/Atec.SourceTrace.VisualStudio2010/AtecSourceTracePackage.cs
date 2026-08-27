using Atec.SourceTrace.VisualStudio2010.Commands;
using Atec.SourceTrace.VisualStudio2010.Options;
using Atec.SourceTrace.VisualStudio2010.Services;
using Atec.SourceTrace.VisualStudio2010.ToolWindows;
using Microsoft.VisualStudio.Shell;
using System;
using System.Runtime.InteropServices;
using System.Windows.Threading;

namespace Atec.SourceTrace.VisualStudio2010
{
    [PackageRegistration(UseManagedResourcesOnly = true)]
    [Guid(PackageGuids.PackageString)]
    [ProvideMenuResource("Menus.ctmenu", 2)]
    [ProvideToolWindow(typeof(SourceTraceToolWindow))]
    [ProvideOptionPage(typeof(SourceTraceOptionsPage), "ATEC Source Trace", "General", 0, 0, true)]
    public sealed class AtecSourceTracePackage : Package
    {
        private TraceService _traceService;

        public object QueryService(Type serviceType)
        {
            return GetService(serviceType);
        }

        public SourceTraceOptionsPage GetOptionsPage()
        {
            return (SourceTraceOptionsPage)GetDialogPage(typeof(SourceTraceOptionsPage));
        }

        public ToolWindowPane FindOrCreateToolWindow()
        {
            return FindToolWindow(typeof(SourceTraceToolWindow), 0, true);
        }

        protected override void Initialize()
        {
            base.Initialize();
            var dispatcher = Dispatcher.CurrentDispatcher;
            var settings = new SettingsService(this);
            var editor = new EditorBridge(this);
            _traceService = new TraceService(this, settings, editor, dispatcher);
            var commands = new TraceCommands(this, _traceService);
            commands.Initialize();
        }
    }
}
