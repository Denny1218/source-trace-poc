"""Copy VSIX to out/ and 산출물/운영PC/visualstudio/ (UTF-8 paths on Windows)."""
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
        print(f"source missing: {src}", file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parents[1]
    repo = root.parent
    out_dir = root / "out"
    deliver = repo / "산출물" / "운영PC" / "visualstudio"
    out_dir.mkdir(parents=True, exist_ok=True)
    deliver.mkdir(parents=True, exist_ok=True)
    for dest_dir in (out_dir, deliver):
        dest = dest_dir / name
        shutil.copy2(src, dest)
        print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
