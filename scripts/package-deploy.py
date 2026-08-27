"""Package STEP 6 deploy artifacts into 산출물 folder."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _strip_runtime_db(deploy_root: Path) -> list[str]:
    """Never ship SQLite files. Smoke-test of deploy creates an empty DB."""
    removed: list[str] = []
    for pattern in ("**/*.db", "**/*.db-wal", "**/*.db-shm"):
        for path in deploy_root.glob(pattern):
            if path.is_file():
                rel = str(path.relative_to(deploy_root))
                path.unlink()
                removed.append(rel)
    gitkeep = deploy_root / "data" / ".gitkeep"
    gitkeep.parent.mkdir(parents=True, exist_ok=True)
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    return removed


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    # Regenerate ASCII-safe batch files
    import generate_server_bats

    generate_server_bats.main()

    out = root / "산출물"
    server_deploy = out / "서버PC" / "deploy"
    client_dir = out / "운영PC"

    dist_index = root / "frontend" / "dist" / "index.html"
    if not dist_index.is_file():
        print("[ERROR] frontend/dist 없음. scripts/build-frontend.bat 실행")
        return 1

    print("=" * 40)
    print(" STEP 6 산출물 패키징")
    print("=" * 40)

    # Clean deploy
    if server_deploy.exists():
        shutil.rmtree(server_deploy)

    # Backend
    _copy_tree(root / "backend" / "app", server_deploy / "backend" / "app")
    _copy_file(root / "backend" / "requirements.txt", server_deploy / "backend" / "requirements.txt")
    _copy_file(root / "backend" / "requirements-lock.txt", server_deploy / "backend" / "requirements-lock.txt")

    # Frontend dist
    _copy_tree(root / "frontend" / "dist", server_deploy / "frontend" / "dist")

    # Offline wheels
    wheels_src = root / "offline_packages" / "python"
    wheels_dst = server_deploy / "offline_packages" / "python"
    wheels_dst.mkdir(parents=True, exist_ok=True)
    wheel_count = 0
    if wheels_src.is_dir():
        for whl in wheels_src.glob("*.whl"):
            shutil.copy2(whl, wheels_dst / whl.name)
            wheel_count += 1
    else:
        print("[WARN] offline_packages/python 비어 있음")

    # Empty data/logs
    (server_deploy / "data").mkdir(parents=True, exist_ok=True)
    (server_deploy / "logs").mkdir(parents=True, exist_ok=True)

    # Config & docs
    _copy_file(root / ".env.example", server_deploy / ".env.example")
    for name in ("00_읽어보세요.md", "테스트_체크리스트.md", "STEP10_운영환경_최종배포_검증결과.md"):
        src = out / "서버PC" / name
        if src.is_file():
            _copy_file(src, server_deploy / name)
    op_guide = root / "OPERATING_TEST_STEP6.md"
    if op_guide.is_file():
        _copy_file(op_guide, server_deploy / op_guide.name)

    # Server scripts into deploy/scripts
    scripts_dst = server_deploy / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "01_env_check.bat",
        "02_offline_install.bat",
        "03_start_server.bat",
        "04_status_check.bat",
        "05_stop_server.bat",
        "01_환경점검.bat",
        "02_오프라인설치.bat",
        "03_서버시작.bat",
        "04_상태확인.bat",
        "05_서버중지.bat",
    ):
        src = out / "서버PC" / name
        if src.is_file():
            _copy_file(src, scripts_dst / name)

    for name in ("setup-yona-credential.bat", "setup-yona-credential.ps1"):
        src = root / "scripts" / name
        if src.is_file():
            _copy_file(src, scripts_dst / name)

    stripped = _strip_runtime_db(server_deploy)
    if stripped:
        print("[INFO] removed runtime DB from deploy: " + ", ".join(stripped))

    print()
    print(f" 서버 PC  : {server_deploy}")
    print(f" 운영 PC  : {client_dir}")
    print(f" wheel    : {wheel_count} 개")
    print()
    print(" USB 복사:")
    print("   서버PC\\deploy  -> 내부망 서버")
    print("   운영PC\\        -> 운영 담당 PC")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
