"""Build a VS2010-installable VSIX 1.0 zip from compiled outputs."""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="vsixmanifest" ContentType="text/xml" />
  <Default Extension="pkgdef" ContentType="text/plain" />
  <Default Extension="dll" ContentType="application/octet-stream" />
  <Default Extension="png" ContentType="image/png" />
</Types>
"""


def add_file(zf: zipfile.ZipFile, src: Path, arcname: str) -> None:
    if not src.is_file():
        raise FileNotFoundError(src)
    zf.write(src, arcname.replace("\\", "/"))


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: pack_vsix.py <project_dir> <output.vsix>", file=sys.stderr)
        return 2
    proj = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve()
    bin_dir = proj / "bin" / "Release" / "net40"
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp = dest.with_suffix(".zip")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        add_file(zf, proj / "source.extension.vsixmanifest", "extension.vsixmanifest")
        add_file(zf, proj / "Atec.SourceTrace.VisualStudio2010.pkgdef", "Atec.SourceTrace.VisualStudio2010.pkgdef")
        add_file(zf, bin_dir / "Atec.SourceTrace.VisualStudio2010.dll", "Atec.SourceTrace.VisualStudio2010.dll")
        add_file(zf, bin_dir / "Atec.SourceTrace.Core.dll", "Atec.SourceTrace.Core.dll")
        add_file(zf, proj / "Icons" / "icon16.png", "Icons/icon16.png")
        add_file(zf, proj / "Icons" / "ExtensionIcon128.png", "Icons/ExtensionIcon128.png")
    if dest.exists():
        dest.unlink()
    shutil.move(str(tmp), str(dest))
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
