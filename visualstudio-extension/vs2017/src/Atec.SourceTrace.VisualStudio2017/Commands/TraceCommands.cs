using Microsoft.VisualStudio.Shell;
using System;
using System.ComponentModel.Design;
using ThreadingTasks = System.Threading.Tasks;

namespace Atec.SourceTrace.VisualStudio2017.Commands
{
    internal sealed class TraceCommands
    {
        private readonly AsyncPackage _package;
        private readonly Services.TraceService _trace;

        public TraceCommands(AsyncPackage package, Services.TraceService trace)
        {
            _package = package;
            _trace = trace;
        }

        public async ThreadingTasks.Task InitializeAsync()
        {
            await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
            var mcs = await _package.GetServiceAsync(typeof(IMenuCommandService)) as OleMenuCommandService;
            if (mcs == null)
            {
                return;
            }

            Add(mcs, PackageIds.FunctionHistoryCmd, () => _trace.RunFunctionHistoryAsync());
            Add(mcs, PackageIds.SelectionTraceCmd, () => _trace.RunSelectionTraceAsync());
            Add(mcs, PackageIds.FunctionHistoryCmdMain, () => _trace.RunFunctionHistoryAsync());
            Add(mcs, PackageIds.SelectionTraceCmdMain, () => _trace.RunSelectionTraceAsync());
            Add(mcs, PackageIds.ConfigureCmd, () => _trace.ConfigureAsync());
            Add(mcs, PackageIds.CheckServerCmd, () => _trace.CheckServerAsync());
        }

        private void Add(OleMenuCommandService mcs, int commandId, Func<ThreadingTasks.Task> handler)
        {
            var cmdId = new CommandID(new Guid(PackageGuids.CommandSetString), commandId);
            var cmd = new OleMenuCommand((sender, args) =>
            {
                ThreadHelper.JoinableTaskFactory.RunAsync(async () => await handler().ConfigureAwait(true));
            }, cmdId);
            mcs.AddCommand(cmd);
        }
    }
}
