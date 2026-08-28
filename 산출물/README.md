# Source Trace 운영 산출물

내부망 **서버 PC** / **운영 PC** 배포용 최종 산출물입니다.

## 폴더

| 폴더 | 대상 | 내용 |
|------|------|------|
| `서버PC/` | 서버 PC | `SourceTrace_Server_Deploy.zip`, 설치 bat, 가이드 |
| `운영PC/` | 운영·개발자 PC | 사용 매뉴얼, IDE 설치 파일, 테스트 스크립트 |

## 먼저 읽을 문서

→ **`운영PC/SourceTrace_POC_전체_사용_매뉴얼.md`** (서버 설치 ~ IDE 조회 통합)

## 패키징 (개발 PC)

```bat
scripts\build-frontend.bat
scripts\package-deploy.bat
```

VS Code Extension 변경 시:

```bat
cd vscode-extension
npm install
npm run package:vsix
```

## 배포 순서 (요약)

1. `서버PC/SourceTrace_Server_Deploy.zip` → 서버에 `deploy/` 배치 → bat 순서대로 설치·기동
2. 운영 PC: `운영PC/server_host.txt`에 서버 IP → Browser `http://<서버IP>:8010`
3. (선택) IDE: `운영PC` 가이드 + `VSCode-Extension/` · `eclipse/` · `visualstudio/` 설치 파일

## 상세 가이드

- 서버: `서버PC/00_읽어보세요.md`
- 운영: `운영PC/00_읽어보세요.md`
- 사용자 절차 요약: `운영PC/사용자_사용_매뉴얼.md`
