# Source Trace POC

AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC (PROJECT_SPEC **v2.6**)

장비 Git 변경 이력과 PPT 변경내역서를 연계해, 유지보수 시 **언제·무엇이·왜** 바뀌었는지 Web 또는 IDE Client로 조회합니다.

## 저장소 구성

| 경로 | 내용 |
|------|------|
| `backend/`, `frontend/` | 서버·Web UI 소스 |
| `vscode-extension/`, `eclipse-plugin/`, `visualstudio-extension/` | IDE Client 소스 |
| `scripts/` | 빌드·배포·개발 스크립트 |
| `산출물/서버PC/` | 서버 설치 패키지·실행 bat·가이드 |
| `산출물/운영PC/` | 운영/사용 매뉴얼·IDE 설치 파일·테스트 스크립트 |
| `AI_…_PROJECT_SPEC_v2.6.md` | 현행 프로젝트 명세 |

> 제출용 ZIP·대화기록·개발 중 테스트 산출물은 이 저장소에 포함하지 않습니다.

## 빠른 시작 (개발)

```bat
scripts\check-environment.bat
scripts\start-dev.bat
```

- Backend: http://localhost:8010  
- Frontend (dev): http://localhost:5173  

## 운영 배포 (내부망)

```bat
scripts\build-frontend.bat
scripts\package-deploy.bat
```

산출물은 `산출물/서버PC/`, `산출물/운영PC/`에 생성됩니다.

**먼저 읽을 문서**

1. **전체 사용 절차**: `산출물/운영PC/SourceTrace_POC_전체_사용_매뉴얼.md`
2. 서버 설치: `산출물/서버PC/00_읽어보세요.md`
3. 운영·Web: `산출물/운영PC/00_읽어보세요.md`
4. IDE별: `산출물/운영PC/*_설치_사용_가이드.md`

## 공식 Client

| Client | 설치 파일 (산출물/운영PC) |
|--------|---------------------------|
| VS Code | `VSCode-Extension/source-trace-vscode-0.5.5.vsix` |
| Eclipse | `eclipse/source-trace-eclipse-update-site-0.1.1.zip` |
| VS 2017 | `visualstudio/source-trace-visualstudio2017-0.1.3.vsix` |
| VS 2010 | `visualstudio/source-trace-visualstudio2010-0.1.3.vsix` |

Visual Studio 2022는 공식 지원 대상이 아닙니다.

## 환경 설정

`.env.example` → `.env` 복사 후 `DATABASE_PATH` 등 설정.

## 상세 명세

`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.6.md`
