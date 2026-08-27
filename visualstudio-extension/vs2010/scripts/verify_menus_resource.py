"""Verify VS2010 package DLL has Menus.ctmenu/1 Win32 resource (not RT_RCDATA)."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

try:
    import pefile  # type: ignore
except ImportError:
    print("ERROR: pefile required", file=sys.stderr)
    raise SystemExit(1)


def verify_dll(data: bytes) -> None:
    pe = pefile.PE(data=data)
    if not hasattr(pe, "DIRECTORY_ENTRY_RESOURCE"):
        raise RuntimeError("DLL has no resource directory")

    found = False
    for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        type_name = entry.name.string.decode() if entry.name else str(entry.struct.Id)
        if str(type_name).upper() != "MENUS.CTMENU":
            continue
        if not hasattr(entry, "directory"):
            continue
        for sub in entry.directory.entries:
            res_id = sub.name.string.decode() if sub.name else sub.struct.Id
            if res_id == 1:
                size = sub.directory.entries[0].data.struct.Size
                if size <= 0:
                    raise RuntimeError("Menus.ctmenu/1 resource is empty")
                found = True
    if not found:
        raise RuntimeError(
            'Expected Win32 resource TYPE "Menus.ctmenu" ID 1 — '
            "VS2010 will not show Tools/context menus without it"
        )


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify_menus_resource.py <file.dll|file.vsix>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1]).resolve()
    if not path.is_file():
        print(f"ERROR: not found: {path}", file=sys.stderr)
        return 1
    if path.suffix.lower() == ".vsix":
        with zipfile.ZipFile(path) as zf:
            dll_name = next(
                (n for n in zf.namelist() if n.endswith("Atec.SourceTrace.VisualStudio2010.dll")),
                None,
            )
            if not dll_name:
                raise RuntimeError("VSIX missing Atec.SourceTrace.VisualStudio2010.dll")
            verify_dll(zf.read(dll_name))
    else:
        verify_dll(path.read_bytes())
    print(f"OK  Menus.ctmenu/1 verified in {path.name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
