import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
resolve_bat = root / "산출물" / "서버PC" / "deploy" / "scripts" / "_resolve_root.bat"
check_bat = root / "산출물" / "서버PC" / "deploy" / "scripts" / "01_환경점검.bat"

for label, bat in [("resolve_root", resolve_bat), ("env_check", check_bat)]:
    if not bat.is_file():
        print(f"[SKIP] {label}: {bat} not found")
        continue
    out_file = bat.parent / "_test_out.txt"
    script = f'@echo off\r\ncall "{bat}"\r\n'
    if label == "resolve_root":
        script += "if errorlevel 1 (echo FAIL>>\"%s\" & exit /b 1)\r\necho DEPLOY_ROOT=%%DEPLOY_ROOT%%>>\"%s\"\r\n" % (out_file, out_file)
    else:
        script += "echo DONE>>\"%s\"\r\n" % out_file
    r = subprocess.run(
        ["cmd", "/c", script],
        capture_output=True,
        text=True,
        cwd=str(bat.parent),
        input="\n",
        timeout=5,
    )
    print(f"=== {label} ===")
    if out_file.is_file():
        print(out_file.read_text(encoding="utf-8", errors="replace").strip())
        out_file.unlink()
    print("rc:", r.returncode)
