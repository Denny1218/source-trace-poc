# Packager for 최종제출본/SourceTrace_POC_Final_20260823
# Never includes SQLite DB / WAL / SHM (empty DB must not overwrite ops).
from __future__ import annotations

import hashlib
import os
import shutil
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(r"c:\sourcechangeTrace")
DEST = ROOT / "최종제출본" / "SourceTrace_POC_Final_20260823"
OPS = ROOT / "산출물" / "운영PC"
SVR = ROOT / "산출물" / "서버PC"
CONV = ROOT / "산출물" / "대화기록"

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "bin",
    "obj",
    ".vs",
    "out",
    "target",
    ".tools",
    "diag-tools",
    "산출물",
    "최종제출본",
    "logs",
    ".cursor",
    ".vscode",
    "_step10_backup_20260810_1139",
    "offline_packages",
    "deploy",
    "data",
    "image",
    "sample",
    "test_sample",
    "dist",
}

SKIP_FILE_SUFFIX = {".db", ".pyc", ".vsix", ".db-wal", ".db-shm"}
SKIP_FILE_NAMES = {".env"}
DB_SUFFIXES = {".db", ".db-wal", ".db-shm"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.endswith(".egg-info")


def is_db_path(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".db") or name.endswith(".db-wal") or name.endswith(".db-shm"):
        return True
    return path.suffix.lower() in DB_SUFFIXES


def vs_skip(rel: Path) -> bool:
    parts = [p.lower() for p in rel.parts]
    joined = "/".join(parts)
    if "menuprobe" in joined or "controltest" in joined:
        return True
    if "build-menuprobe" in joined or "build-controltest" in joined:
        return True
    if "build-resourcev2" in joined or "build-group-parent" in joined:
        return True
    if parts[:2] == ["visualstudio-extension", "src"]:
        return True
    if "visualstudio-extension" in parts and "out" in parts:
        return True
    return False


def add_tree_to_zip(zf: zipfile.ZipFile, src_root: Path, arc_prefix: str) -> int:
    added = 0
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for fn in filenames:
            if fn in SKIP_FILE_NAMES:
                continue
            path = Path(dirpath) / fn
            if is_db_path(path):
                continue
            rel = path.relative_to(src_root)
            if any(p in SKIP_DIR_NAMES for p in rel.parts):
                continue
            if path.suffix.lower() in SKIP_FILE_SUFFIX and path.suffix.lower() != ".md":
                if path.suffix.lower() == ".vsix":
                    continue
            zip_rel = Path(arc_prefix) / rel
            if vs_skip(Path(arc_prefix) / rel):
                continue
            if path.name.endswith(".ps1") and "probe" in path.name.lower():
                continue
            zf.write(path, zip_rel.as_posix())
            added += 1
    return added


def zip_deploy_no_db(deploy_root: Path, zip_path: Path) -> None:
    """Zip server deploy tree; refuse to include any SQLite files."""
    if not deploy_root.is_dir():
        raise FileNotFoundError(f"deploy missing: {deploy_root}")
    leaked = [p for p in deploy_root.rglob("*") if p.is_file() and is_db_path(p)]
    if leaked:
        for p in leaked:
            p.unlink()
        print("[WARN] stripped DB from deploy before zip:", ", ".join(str(p) for p in leaked))
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(deploy_root):
            dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git"}]
            for fn in filenames:
                path = Path(dirpath) / fn
                if is_db_path(path) or fn == ".env":
                    continue
                arc = Path("deploy") / path.relative_to(deploy_root)
                zf.write(path, arc.as_posix())


def assert_zip_has_no_db(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = [
            n
            for n in zf.namelist()
            if n.lower().endswith(".db")
            or n.lower().endswith(".db-wal")
            or n.lower().endswith(".db-shm")
        ]
    if bad:
        raise RuntimeError(f"DB leaked into zip {zip_path}: {bad}")


def main() -> None:
    deploy_root = SVR / "deploy"
    if DEST.exists():
        shutil.rmtree(DEST)
    for sub in [
        "00_최종안내",
        "01_PROJECT_SPEC/이전버전",
        "02_설치및실행파일/VSCode",
        "02_설치및실행파일/Eclipse",
        "02_설치및실행파일/VisualStudio",
        "02_설치및실행파일/Server",
        "03_설치운영가이드",
        "04_소스코드",
        "05_대화기록",
    ]:
        (DEST / sub).mkdir(parents=True, exist_ok=True)

    spec = "AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC"
    copy_file(ROOT / f"{spec}_v2.6.md", DEST / "01_PROJECT_SPEC" / f"{spec}_v2.6.md")
    prev_dir = DEST / "01_PROJECT_SPEC" / "이전버전"
    for name in [
        f"{spec}.md",
        f"{spec}_v2.md",
        f"{spec}_v2.1.md",
        f"{spec}_v2.2.md",
        f"{spec}_v2.3.md",
        f"{spec}_v2.4.md",
        f"{spec}_v2.5.md",
    ]:
        src = ROOT / name
        if src.is_file():
            copy_file(src, prev_dir / name)

    vsix = OPS / "VSCode-Extension" / "source-trace-vscode-0.5.4.vsix"
    if vsix.is_file():
        copy_file(vsix, DEST / "02_설치및실행파일" / "VSCode" / vsix.name)
    eclipse = OPS / "eclipse" / "source-trace-eclipse-update-site-0.1.1.zip"
    if eclipse.is_file():
        copy_file(eclipse, DEST / "02_설치및실행파일" / "Eclipse" / eclipse.name)
    for name in (
        "source-trace-visualstudio2010-0.1.3.vsix",
        "source-trace-visualstudio2017-0.1.3.vsix",
    ):
        src = OPS / "visualstudio" / name
        if src.is_file():
            copy_file(src, DEST / "02_설치및실행파일" / "VisualStudio" / name)

    server_zip = DEST / "02_설치및실행파일" / "Server" / "SourceTrace_Server_Deploy.zip"
    zip_deploy_no_db(deploy_root, server_zip)
    assert_zip_has_no_db(server_zip)

    guides = [
        (SVR / "00_읽어보세요.md", "서버PC_00_읽어보세요.md"),
        (OPS / "00_읽어보세요.md", "운영PC_00_읽어보세요.md"),
        (OPS / "사용자_사용_매뉴얼.md", "사용자_사용_매뉴얼.md"),
        (OPS / "VSCode-Extension" / "00_읽어보세요.md", "VSCode_Source_Trace_설치_사용_가이드.md"),
        (OPS / "Eclipse_Source_Trace_설치_사용_가이드.md", "Eclipse_Source_Trace_설치_사용_가이드.md"),
        (OPS / "VisualStudio_Source_Trace_설치_사용_가이드.md", "VisualStudio_Source_Trace_설치_사용_가이드.md"),
        (OPS / "VisualStudio2010_Source_Trace_설치_사용_가이드.md", "VisualStudio2010_Source_Trace_설치_사용_가이드.md"),
        (OPS / "VisualStudio2017_Source_Trace_설치_사용_가이드.md", "VisualStudio2017_Source_Trace_설치_사용_가이드.md"),
    ]
    for src, name in guides:
        if src.is_file():
            copy_file(src, DEST / "03_설치운영가이드" / name)

    if CONV.is_dir():
        for md in CONV.glob("*.md"):
            copy_file(md, DEST / "05_대화기록" / md.name)

    zip_path = DEST / "04_소스코드" / "SourceTrace_POC_Source.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        add_tree_to_zip(zf, ROOT / "backend", "backend")
        add_tree_to_zip(zf, ROOT / "frontend", "frontend")
        add_tree_to_zip(zf, ROOT / "vscode-extension", "vscode-extension")
        add_tree_to_zip(zf, ROOT / "eclipse-plugin", "eclipse-plugin")
        add_tree_to_zip(zf, ROOT / "visualstudio-extension", "visualstudio-extension")
        add_tree_to_zip(zf, ROOT / "scripts", "scripts")
        for extra in ["README.md", ".env.example", "OPERATING_TEST_STEP6.md"]:
            p = ROOT / extra
            if p.is_file():
                zf.write(p, extra)
    assert_zip_has_no_db(zip_path)

    readme = DEST / "00_최종안내" / "README_최종제출본.md"
    today = date.today().isoformat()
    readme.write_text(
        f"""# README — Source Trace POC 최종 제출본

- 프로젝트명: AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC (Source Trace)
- 기준 명세: `01_PROJECT_SPEC/AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.6.md`
- 패키지 갱신일: {today}
- 폴더: `최종제출본/SourceTrace_POC_Final_20260823/`

## 중요 — DB 미포함

- `SourceTrace_Server_Deploy.zip` / 소스 ZIP에 **`.db` / `.db-wal` / `.db-shm`를 넣지 않습니다.**
- 운영 서버에 덮어쓸 때 기존 `equipment_change_trace.db`를 지우거나 빈 DB로 교체하지 마세요.
- 서버 기동 시 DB가 없으면 새로 생성됩니다.

## 폴더

| 폴더 | 내용 |
|---|---|
| `00_최종안내/` | 이 README, SHA256 Manifest |
| `01_PROJECT_SPEC/` | 공식 v2.6 + 이전버전 |
| `02_설치및실행파일/` | Server ZIP + VS Code / Eclipse / VS2010 / VS2017 |
| `03_설치운영가이드/` | 서버·Web·IDE 설치/사용 안내 |
| `04_소스코드/` | `SourceTrace_POC_Source.zip` |
| `05_대화기록/` | STEP 0~10 대화 Prompt 아카이브 (IDE·운영 후속 포함) |

## 설치 시작

1. 서버: `02_설치및실행파일/Server/SourceTrace_Server_Deploy.zip` → `deploy/` 복사 (`03_설치운영가이드/서버PC_00_읽어보세요.md`)
2. Web: `사용자_사용_매뉴얼.md`
3. IDE: 동일 가이드 폴더 + `02_설치및실행파일` 설치 파일
""",
        encoding="utf-8",
    )

    binaries = [
        server_zip,
        DEST / "02_설치및실행파일" / "VSCode" / "source-trace-vscode-0.5.4.vsix",
        DEST / "02_설치및실행파일" / "Eclipse" / "source-trace-eclipse-update-site-0.1.1.zip",
        DEST / "02_설치및실행파일" / "VisualStudio" / "source-trace-visualstudio2010-0.1.3.vsix",
        DEST / "02_설치및실행파일" / "VisualStudio" / "source-trace-visualstudio2017-0.1.3.vsix",
        zip_path,
    ]
    report = DEST / "00_최종안내" / "FILE_MANIFEST_SHA256.md"
    lines = ["# SHA256 Manifest", "", f"- generated: {today}", ""]
    for p in binaries:
        if not p.is_file():
            lines.append(f"- MISSING `{p.relative_to(DEST)}`")
            continue
        lines.append(
            f"- `{p.relative_to(DEST).as_posix()}`  \n  size={p.stat().st_size}  \n  sha256={sha256(p)}"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
