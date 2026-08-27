using Microsoft.VisualStudio.Shell;
using System;
using System.ComponentModel.Design;

namespace Atec.SourceTrace.VisualStudio2010.Commands
{
    internal sealed class TraceCommands
    {
        private readonly AtecSourceTracePackage _package;
        private readonly Services.TraceService _trace;

        public TraceCommands(AtecSourceTracePackage package, Services.TraceService trace)
        {
            _package = package;
            _trace = trace;
        }

        public void Initialize()
        {
            var mcs = _package.QueryService(typeof(IMenuCommandService)) as OleMenuCommandService;
            if (mcs == null)
            {
                return;
            }

            Add(mcs, PackageIds.FunctionHistoryCmd, _trace.RunFunctionHistory);
            Add(mcs, PackageIds.SelectionTraceCmd, _trace.RunSelectionTrace);
            Add(mcs, PackageIds.FunctionHistoryCmdMain, _trace.RunFunctionHistory);
            Add(mcs, PackageIds.SelectionTraceCmdMain, _trace.RunSelectionTrace);
            Add(mcs, PackageIds.ConfigureCmd, _trace.Configure);
            Add(mcs, PackageIds.CheckServerCmd, _trace.CheckServer);
        }

        private void Add(OleMenuCommandService mcs, int commandId, EventHandler handler)
        {
            var cmdId = new CommandID(new Guid(PackageGuids.CommandSetString), commandId);
            mcs.AddCommand(new OleMenuCommand(handler, cmdId));
        }
    }
}
