# README — Source Trace POC 최종 제출본

- 프로젝트명: AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC (Source Trace)
- 기준 명세: `01_PROJECT_SPEC/AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.6.md`
- 패키지 갱신일: 2026-08-27
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
