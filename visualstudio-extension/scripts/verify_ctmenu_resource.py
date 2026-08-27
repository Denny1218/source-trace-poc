"""Verify managed VSPackage .resources contains command-table byte[] (VSSDK standard pipeline)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PS_VERIFY = r"""
param(
  [string]$DllPath,
  [string]$CtoPath,
  [string]$ManifestResourceName,
  [string]$CommandTableKey
)
Add-Type -AssemblyName System.Windows.Forms
$ErrorActionPreference = 'Stop'
$asm = [Reflection.Assembly]::ReflectionOnlyLoadFrom($DllPath)
$stream = $asm.GetManifestResourceStream($ManifestResourceName)
if (-not $stream) {
  $names = $asm.GetManifestResourceNames()
  throw "Manifest resource '$ManifestResourceName' not found. Available: $($names -join ', ')"
}
$reader = New-Object System.Resources.ResourceReader($stream)
try {
  $foundKey = $null
  $tableBytes = $null
  $keys = @()
  foreach ($entry in $reader) {
    $keys += $entry.Key
    if ($entry.Key -eq $CommandTableKey -or ($entry.Key -eq 'CTMENU' -and -not $foundKey)) {
      $foundKey = $entry.Key
      $tableBytes = [byte[]]$entry.Value
    }
  }
  if (-not $foundKey) {
    throw "Command table key '$CommandTableKey' (or CTMENU) missing in $ManifestResourceName. Keys: $($keys -join ', ')"
  }
  if ($tableBytes.Length -le 0) {
    throw "$foundKey byte[] is empty"
  }
  if ($tableBytes.GetType().FullName -ne 'System.Byte[]') {
    throw "$foundKey type is $($tableBytes.GetType().FullName), expected System.Byte[]"
  }
  $hash = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($tableBytes))).Replace('-','').ToLower()
  $result = @{
    resourceName = $ManifestResourceName
    commandTableKey = $foundKey
    ctmenuSize = $tableBytes.Length
    ctmenuSha256 = $hash
    ctoMatch = $null
    ctoSize = $null
    ctoSha256 = $null
  }
  if ($CtoPath -and (Test-Path $CtoPath)) {
    $ctoBytes = [IO.File]::ReadAllBytes($CtoPath)
    $ctoHash = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($ctoBytes))).Replace('-','').ToLower()
    $result.ctoSize = $ctoBytes.Length
    $result.ctoSha256 = $ctoHash
    $result.ctoMatch = ($hash -eq $ctoHash)
  }
  $result | ConvertTo-Json -Compress
} finally {
  $reader.Close()
  $stream.Close()
}
"""


def _extract_dll(vsix_or_dll: Path, work: Path) -> Path:
    if vsix_or_dll.suffix.lower() == ".vsix":
        with zipfile.ZipFile(vsix_or_dll) as zf:
            root_dlls = [
                n
                for n in zf.namelist()
                if n.lower().endswith(".dll") and "/" not in n.replace("\\", "/") and "Core" not in n
            ]
            preferred = [
                n
                for n in root_dlls
                if "SourceTrace.VisualStudio" in n or "ControlTest" in n or "MenuProbe" in n
            ]
            dll_name = (preferred or root_dlls or [None])[0]
            if not dll_name:
                raise RuntimeError(f"No extension DLL in VSIX: {vsix_or_dll}")
            out = work / Path(dll_name).name
            out.write_bytes(zf.read(dll_name))
            return out
    return vsix_or_dll


def verify(
    dll_path: Path,
    *,
    cto_path: Path | None,
    manifest_resource_name: str,
    command_table_key: str = "Menus.ctmenu",
) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as tf:
        tf.write(PS_VERIFY)
        ps1 = Path(tf.name)
    try:
        args = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps1),
            str(dll_path),
            str(cto_path) if cto_path else "",
            manifest_resource_name,
            command_table_key,
        ]
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "PowerShell verify failed")
        return json.loads(proc.stdout.strip())
    finally:
        ps1.unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: verify_ctmenu_resource.py <dll|vsix> <ManifestResourceName> [cto-path] [command-table-key]",
            file=sys.stderr,
        )
        return 2
    target = Path(sys.argv[1]).resolve()
    manifest_name = sys.argv[2]
    cto_path = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 and sys.argv[3] else None
    command_table_key = sys.argv[4] if len(sys.argv) > 4 else "Menus.ctmenu"
    if not target.is_file():
        print(f"ERROR: not found: {target}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        dll = _extract_dll(target, Path(td))
        result = verify(
            dll,
            cto_path=cto_path,
            manifest_resource_name=manifest_name,
            command_table_key=command_table_key,
        )
    key = result["commandTableKey"]
    print(
        f"OK  {manifest_name} {key} size={result['ctmenuSize']} sha256={result['ctmenuSha256']}"
    )
    if cto_path:
        if not result.get("ctoMatch"):
            raise SystemExit(
                f"ERROR: {key} sha256 {result['ctmenuSha256']} != .cto sha256 {result.get('ctoSha256')}"
            )
        print(f"OK  {key} matches .cto ({result['ctoSize']} bytes)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
