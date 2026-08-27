"""Embed a compiled VSCT .cto file into a managed DLL as a VS menu-table resource.

VS2010 reads pkgdef Menus entries of the form:
    ", Menus.ctmenu, 1"
which maps to Win32 resource TYPE "Menus.ctmenu" and resource ID 1.
(RT_RCDATA named "Menus.ctmenu" is NOT what the shell expects.)

The SDK-style net40 build produces a .cto in obj/ but does not embed it;
this script patches the DLL via BeginUpdateResource (PowerShell C# P/Invoke).

Usage:
    python embed_cto.py <dll_path> <cto_path>
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


_CS_SOURCE = r"""
using System;
using System.IO;
using System.Runtime.InteropServices;

public static class CtoEmbedder {
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern IntPtr BeginUpdateResource(string pFileName, bool bDeleteExistingResources);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool UpdateResource(
        IntPtr hUpdate, string lpType, IntPtr lpName,
        ushort wLanguage, byte[] lpData, uint cb);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool EndUpdateResource(IntPtr hUpdate, bool fDiscard);

    // pkgdef: ", Menus.ctmenu, 1"  =>  TYPE "Menus.ctmenu", ID 1 (MAKEINTRESOURCE)
    public static int Embed(string dllPath, string ctoPath) {
        byte[] data = File.ReadAllBytes(ctoPath);
        IntPtr h = BeginUpdateResource(dllPath, false);
        if (h == IntPtr.Zero)
            return Marshal.GetLastWin32Error();
        bool ok = UpdateResource(h, "Menus.ctmenu", (IntPtr)1, 0, data, (uint)data.Length);
        int err = ok ? 0 : Marshal.GetLastWin32Error();
        EndUpdateResource(h, !ok);
        return err;
    }
}
"""


def embed(dll_path: Path, cto_path: Path) -> None:
    """Embed cto_path into dll_path as VS menu-table resource (Menus.ctmenu / ID 1)."""
    if sys.platform != "win32":
        raise RuntimeError("embed_cto requires Windows")

    # Escape paths for PowerShell single-quoted strings
    dll_ps = str(dll_path).replace("'", "''")
    cto_ps = str(cto_path).replace("'", "''")

    ps_script = f"""
$src = @'
{_CS_SOURCE}
'@
Add-Type -TypeDefinition $src -Language CSharp
$rc = [CtoEmbedder]::Embed('{dll_ps}', '{cto_ps}')
Write-Output $rc
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True, text=True, check=False,
    )
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if result.returncode != 0 or stderr:
        raise RuntimeError(f"PowerShell failed (rc={result.returncode}): {stderr}")
    try:
        rc = int(stdout)
    except ValueError:
        raise RuntimeError(f"Unexpected output from embed: {stdout!r}")
    if rc != 0:
        raise RuntimeError(f"CtoEmbedder.Embed returned Win32 error {rc}")

    print(f"  [embed_cto] Menus.ctmenu/1 ({cto_path.stat().st_size} B) -> {dll_path.name}")


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: embed_cto.py <dll_path> <cto_path>", file=sys.stderr)
        return 2
    dll = Path(sys.argv[1]).resolve()
    cto = Path(sys.argv[2]).resolve()
    if not dll.is_file():
        print(f"ERROR: DLL not found: {dll}", file=sys.stderr)
        return 1
    if not cto.is_file():
        print(f"ERROR: CTO not found: {cto}", file=sys.stderr)
        return 1
    try:
        embed(dll, cto)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
