using Atec.SourceTrace.VisualStudio2017.Commands;
using Atec.SourceTrace.VisualStudio2017.Options;
using Atec.SourceTrace.VisualStudio2017.Services;
using Atec.SourceTrace.VisualStudio2017.ToolWindows;
using Microsoft.VisualStudio.Shell;
using System;
using System.Runtime.InteropServices;
using System.Threading;
using ThreadingTasks = System.Threading.Tasks;

namespace Atec.SourceTrace.VisualStudio2017
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [Guid(PackageGuids.PackageString)]
    [ProvideMenuResource("Menus.ctmenu", 3)]
    [ProvideToolWindow(typeof(SourceTraceToolWindow), Style = VsDockStyle.Tabbed, Window = "3004", Orientation = ToolWindowOrientation.Right, Transient = false)]
    [ProvideOptionPage(typeof(SourceTraceOptionsPage), "ATEC Source Trace", "General", 0, 0, true)]
    public sealed class AtecSourceTracePackage : AsyncPackage
    {
        private TraceService _traceService;

        protected override async ThreadingTasks.Task InitializeAsync(CancellationToken cancellationToken, IProgress<ServiceProgressData> progress)
        {
            await JoinableTaskFactory.SwitchToMainThreadAsync(cancellationToken);
            var settings = new SettingsService(this);
            var editor = new EditorBridge(this);
            _traceService = new TraceService(this, settings, editor);
            var commands = new TraceCommands(this, _traceService);
            await commands.InitializeAsync();
        }
    }
}
