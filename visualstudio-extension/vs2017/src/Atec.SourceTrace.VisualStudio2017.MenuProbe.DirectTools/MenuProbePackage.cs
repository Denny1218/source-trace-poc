using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;
using System;
using System.ComponentModel.Design;
using System.Runtime.InteropServices;
using System.Threading;
using ThreadingTasks = System.Threading.Tasks;

namespace Atec.SourceTrace.VisualStudio2017.MenuProbe
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [Guid(PackageGuids.PackageString)]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    public sealed class MenuProbePackage : AsyncPackage
    {
        protected override async ThreadingTasks.Task InitializeAsync(CancellationToken cancellationToken, IProgress<ServiceProgressData> progress)
        {
            await JoinableTaskFactory.SwitchToMainThreadAsync(cancellationToken);

            var mcs = await GetServiceAsync(typeof(IMenuCommandService)) as OleMenuCommandService;
            if (mcs == null)
            {
                return;
            }

            var commandId = new CommandID(new Guid(PackageGuids.CommandSetString), PackageIds.ToolsMenuCmd);
            var command = new MenuCommand((sender, args) =>
            {
                ThreadHelper.ThrowIfNotOnUIThread();
                VsShellUtilities.ShowMessageBox(
                    this,
                    "VS2017 minimal menu probe command executed.",
                    "ATEC Source Trace Test",
                    OLEMSGICON.OLEMSGICON_INFO,
                    OLEMSGBUTTON.OLEMSGBUTTON_OK,
                    OLEMSGDEFBUTTON.OLEMSGDEFBUTTON_FIRST);
            }, commandId);
            mcs.AddCommand(command);
        }
    }
}
