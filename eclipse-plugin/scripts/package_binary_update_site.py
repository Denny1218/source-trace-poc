# -*- coding: utf-8 -*-
"""Zip Tycho p2 repository into 산출물/운영PC/eclipse binary Update Site ZIP."""
from pathlib import Path
import zipfile
import sys

repo = Path(__file__).resolve().parents[1] / "update-site" / "target" / "repository"
if not repo.is_dir():
    print("ERROR: repository missing:", repo)
    sys.exit(1)
out_dir = Path(__file__).resolve().parents[2] / "산출물" / "운영PC" / "eclipse"
out_dir.mkdir(parents=True, exist_ok=True)
zip_path = out_dir / "source-trace-eclipse-update-site-0.1.1.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for f in repo.rglob("*"):
        if f.is_file():
            z.write(f, f.relative_to(repo).as_posix())
names = zipfile.ZipFile(zip_path).namelist()
for key in ("content.jar", "artifacts.jar"):
    if not any(n == key or n.endswith("/" + key) for n in names):
        # allow xml
        base = key.replace(".jar", "")
        if not any(base in n for n in names):
            print("ERROR: zip missing", key)
            sys.exit(1)
if not any(n.startswith("plugins/") for n in names):
    print("ERROR: zip missing plugins/")
    sys.exit(1)
if not any(n.startswith("features/") for n in names):
    print("ERROR: zip missing features/")
    sys.exit(1)
print("Created", zip_path, zip_path.stat().st_size, "bytes")
