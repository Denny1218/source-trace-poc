"""Compare Menus.ctmenu SHA256 inside two VSIX packages (must match for ResourceVersion2 A/B)."""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PS = r"""
param([string]$DllPath)
Add-Type -AssemblyName System.Windows.Forms
$asm = [Reflection.Assembly]::ReflectionOnlyLoadFrom($DllPath)
$s = $asm.GetManifestResourceStream('VSPackage.resources')
if (-not $s) { throw 'VSPackage.resources missing' }
$r = New-Object System.Resources.ResourceReader($s)
try {
  foreach ($e in $r) {
    if ($e.Key -eq 'Menus.ctmenu') {
      $h = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([byte[]]$e.Value)).Replace('-','').ToLower()
      Write-Output $h
      exit 0
    }
  }
  throw 'Menus.ctmenu key missing'
} finally { $r.Close(); $s.Close() }
"""


def ctmenu_sha(vsix: Path) -> str:
    with zipfile.ZipFile(vsix) as zf:
        dll_name = next(
            n
            for n in zf.namelist()
            if n.endswith("Atec.SourceTrace.VisualStudio2017.dll") and "Core" not in n
        )
        dll_bytes = zf.read(dll_name)
    with tempfile.TemporaryDirectory() as td:
        dll_path = Path(td) / "ext.dll"
        dll_path.write_bytes(dll_bytes)
        ps1 = Path(td) / "h.ps1"
        ps1.write_text(PS, encoding="utf-8")
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), str(dll_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr or proc.stdout or "hash failed")
        return proc.stdout.strip().splitlines()[-1].strip()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_ctmenu_sha.py <probe.vsix> <baseline-0.1.2.vsix>", file=sys.stderr)
        return 2
    probe = Path(sys.argv[1]).resolve()
    base = Path(sys.argv[2]).resolve()
    sp = ctmenu_sha(probe)
    sb = ctmenu_sha(base)
    print(f"probe  Menus.ctmenu sha256 {sp}")
    print(f"0.1.2  Menus.ctmenu sha256 {sb}")
    if sp != sb:
        print("ERROR: CTMENU hash differs — VSCT must be identical for this A/B", file=sys.stderr)
        return 1
    print("OK  CTMENU hash identical to Source Trace 0.1.2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
