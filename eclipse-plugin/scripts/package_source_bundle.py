# -*- coding: utf-8 -*-
from pathlib import Path
import zipfile
import shutil
import tempfile

repo = Path(__file__).resolve().parents[2]
src = repo / "eclipse-plugin"
out_dir = repo / "산출물" / "운영PC" / "eclipse"
out_dir.mkdir(parents=True, exist_ok=True)
zip_path = out_dir / "source-trace-eclipse-update-site-0.1.0-SOURCE.zip"
if zip_path.exists():
    zip_path.unlink()
stage = Path(tempfile.mkdtemp(prefix="st-eclipse-"))
try:
    for name in [
        "com.atec.sourcetrace.eclipse",
        "feature",
        "unit-tests",
        "update-site",
        "README.md",
        "scripts",
    ]:
        p = src / name
        if p.is_dir():
            shutil.copytree(
                p,
                stage / name,
                ignore=shutil.ignore_patterns("bin", "out", ".git", "__pycache__"),
            )
        elif p.is_file():
            shutil.copy2(p, stage / name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in stage.rglob("*"):
            if f.is_file():
                z.write(f, f.relative_to(stage).as_posix())
    print("Created", zip_path, zip_path.stat().st_size, "bytes")
finally:
    shutil.rmtree(stage, ignore_errors=True)
