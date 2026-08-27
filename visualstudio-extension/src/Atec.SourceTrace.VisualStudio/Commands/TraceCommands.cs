using Microsoft.VisualStudio.Shell;
using System;
using System.ComponentModel.Design;
using System.Threading;
using Task = System.Threading.Tasks.Task;

namespace Atec.SourceTrace.VisualStudio.Commands;

internal sealed class TraceCommands
{
    private readonly AsyncPackage _package;
    private readonly Services.TraceService _trace;

    public TraceCommands(AsyncPackage package, Services.TraceService trace)
    {
        _package = package;
        _trace = trace;
    }

    public async Task InitializeAsync()
    {
        await _package.JoinableTaskFactory.SwitchToMainThreadAsync();
        var mcs = await _package.GetServiceAsync(typeof(IMenuCommandService)) as OleMenuCommandService;
        if (mcs == null)
        {
            return;
        }

        Add(mcs, PackageIds.FunctionHistoryCmd, () => _trace.RunFunctionHistoryAsync());
        Add(mcs, PackageIds.SelectionTraceCmd, () => _trace.RunSelectionTraceAsync());
        Add(mcs, 0x0110, () => _trace.RunFunctionHistoryAsync());
        Add(mcs, 0x0111, () => _trace.RunSelectionTraceAsync());
        Add(mcs, PackageIds.ConfigureCmd, () => _trace.ConfigureAsync());
        Add(mcs, PackageIds.CheckServerCmd, () => _trace.CheckServerAsync());
    }

    private void Add(OleMenuCommandService mcs, int commandId, Func<Task> handler)
    {
        var cmdId = new CommandID(new Guid(PackageGuids.CommandSetString), commandId);
        var cmd = new OleMenuCommand((_, __) =>
        {
            ThreadHelper.JoinableTaskFactory.RunAsync(async () => await handler().ConfigureAwait(true));
        }, cmdId);
        mcs.AddCommand(cmd);
    }
}
