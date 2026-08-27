"""Copy VS2017 VSIX to vs2017/out, visualstudio-extension/out, and 산출물/운영PC/visualstudio/."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: copy_vsix_deliverable.py <source.vsix> <dest_filename>", file=sys.stderr)
        return 2
    src = Path(sys.argv[1]).resolve()
    name = sys.argv[2]
    if not src.is_file():
        print("source missing: " + str(src), file=sys.stderr)
        return 1
    vs2017_root = Path(__file__).resolve().parents[1]
    ext_root = vs2017_root.parent
    repo = ext_root.parent
    dest_dirs = [
        vs2017_root / "out",
        ext_root / "out",
        repo / "산출물" / "운영PC" / "visualstudio",
    ]
    for dest_dir in dest_dirs:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        shutil.copy2(src, dest)
        print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
