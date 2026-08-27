# STEP 6 운영환경 1차 테스트 — 산출물

내부망 **서버 PC**와 **운영 PC** 분리 배포용 패키지입니다.

## 폴더 구성

| 폴더 | 대상 | 내용 |
|---|---|---|
| `서버PC/` | 내부망 서버 | 설치·실행 스크립트, 체크리스트, `deploy/` 배포본 |
| `운영PC/` | 운영 담당자 PC | Browser 접속, API 테스트 스크립트, 체크리스트 |
| `운영PC/VSCode-Extension/` | 운영 담당자/개발자 개인 PC (VS Code) | STEP 9-2 VS Code Extension `.vsix` + 설치 가이드 (서버 설치 아님) |

## 패키징 (개발 PC)

```bat
scripts\build-frontend.bat
scripts\prepare-offline-python.bat
scripts\package-deploy.bat
```

`package-deploy.bat`은 `scripts\package-deploy.py`를 실행하여 `서버PC\deploy\`에 실행 파일을 모읍니다.

> **개발 작업 후** Backend/Frontend/문서 변경 시 `package-deploy.bat`을 재실행하여 deploy를 현행화하세요.

VS Code Extension(`vscode-extension/`) 변경 시에는 별도로 아래 명령을 실행해 `.vsix`를
재생성하세요 (`package-deploy.py`에는 포함되어 있지 않습니다 — 서버 배포와 무관한
개인 PC용 산출물이기 때문입니다).

```bat
cd vscode-extension
npm install
npm run package:vsix
```

## 배포 순서

1. **서버 PC** — `서버PC\deploy` 전체를 `C:\apps\equipment-change-trace\` 등에 복사
2. 서버에서 `scripts\02_오프라인설치.bat` → `scripts\03_서버시작.bat`
3. **운영 PC** — `운영PC\` 폴더 복사 후 `server_host.txt`에 서버 IP 입력
4. 운영 PC Browser: `http://<서버IP>:8010` (또는 `open_browser.bat`)
5. (선택) **VS Code 사용자** — `운영PC\VSCode-Extension\` 폴더를 개인 PC로 복사 후
   `00_읽어보세요.md`대로 `source-trace-vscode-0.5.4.vsix` 설치
6. (선택) **Eclipse** — `운영PC\eclipse\source-trace-eclipse-update-site-0.1.1.zip`
7. (선택) **Visual Studio 2017** — `운영PC\visualstudio\source-trace-visualstudio2017-0.1.3.vsix`
8. (선택) **Visual Studio 2010** — `운영PC\visualstudio\source-trace-visualstudio2010-0.1.3.vsix`

Visual Studio 2022용 VSIX와 MenuProbe 등 진단 패키지는 공식 운영 설치 대상이 아닙니다.

> 운영 PC **실행 스크립트/설정**만 영문 파일명 (`server_host.txt`, `api_test.ps1`,
> `open_browser.bat`). 안내 문서(`.md`)는 한글 파일명을 사용합니다.
> `api_test.ps1`은 UTF-8 BOM으로 저장되어 있습니다.

## 상세 가이드

- **사용자 절차(서버 설치 완료 후)**: `운영PC\사용자_사용_매뉴얼.md`
- 서버: `서버PC\00_읽어보세요.md`
- 운영: `운영PC\00_읽어보세요.md`
- VS Code Extension: `운영PC\VSCode-Extension\00_읽어보세요.md`
- 전체: `OPERATING_TEST_STEP6.md` (deploy 폴더에 포함)
