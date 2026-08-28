# STEP 0. 프로젝트 기본 실행 환경 구축

> **범위**: Cursor 메인 개발 대화 turn **#1 ~ #1** （1턴）
> **이 STEP 요지**: 프로젝트 스펙 이해 및 실행 환경(Backend/Frontend) 기본 구축

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #1 — @AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC.md md 파일을 전체적으로 검토하고 프…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 0 — 프로젝트 기본 실행 환경 구축                                            ║
║  메인 turn #1  |  Monday, Jul 6, 2026, 11:26 AM (UTC+9)                        ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
@AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC.md  md 파일을 전체적으로 검토하고 프로젝트 요구사항과 개발 원칙을 이해해.

현재 프로젝트는 신규 프로젝트다.

 18. 최초 개발 시작 지시에 따라 STEP 0만 구현해.
아직 STEP 1 이후 기능은 구현하지 마.

구현 완료 후  15. Cursor 단계별 수행 지시 형식에 맞춰 구현 내용과 테스트 결과를 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 0 완료 보고

## 1. 구현한 기능

- 프로젝트 기본 디렉터리 구조 생성 (`backend/`, `frontend/`, `scripts/`, `data/`, `logs/`, `deploy/`, `tests/`)
- FastAPI 기본 Application 및 `GET /api/health` API
- SQLite 초기화 구조 (`data/equipment_change_trace.db`)
- React + TypeScript + Vite Dashboard (Backend/DB/Git/Ollama 상태 표시)
- 환경 점검 스크립트 (`check-environment.bat`)
- 개발 서버 실행 스크립트 (`start-dev.bat`)
- 로깅 구성 (`logs/app.log`, RotatingFileHandler)
- STEP 0 pytest 테스트 (6건)

## 2. 생성 또는 수정한 파일

| 구분 | 파일 |
|---|---|
| Backend | `backend/app/main.py`, `api/health.py`, `core/config.py`, `core/logging.py`, `db/database.py`, `services/health_service.py` |
| Backend deps | `requirements.txt`, `requirements-lock.txt`, `requirements-dev.txt` |
| Frontend | `frontend/package.json`, `vite.config.ts`, `src/components/Dashboard.tsx`, `src/api/health.ts` 등 |
| Scripts | `scripts/check-environment.bat`, `start-dev.bat`, `test-backend.bat`, `build-frontend.bat`, `start-server.bat` |
| Docs | `README.md`, `TEST_PLAN.md`, `deploy/README.md`, `deploy/OFFLINE_INSTALL.md` |
| Tests | `backend/tests/test_health.py`, `backend/tests/test_database.py` |

## 3. 핵심 구현 방식

**Health API** — DB/Git/Ollama를 각각 점검하고, Ollama 실패 시에도 `status: "ok"` 유지:

```json
{"status":"ok","database":"ok","git":"available","ollama":"unavailable"}
```

- **Database**: SQLite 파일 생성 + `SELECT 1` 확인
- **Git**: `git --version` subprocess (argument list)
- **Ollama**: `httpx`로 `/api/tags` 호출, 실패 시 `unavailable` (시스템 중단 없음)
- **Logging**: 앱 시작/DB 초기화/Ollama 상태를 `logs/app.log`에 기록
- **Frontend**: Vite proxy로 `/api` → `localhost:8010` 연동, 30초마다 자동 새로고침

## 4. 실행 방법

```bat
# 1. 환경 점검
scripts\check-environment.bat

# 2. 의존성 설치 (최초 1회)
cd backend
pip install -r requirements.txt -r requirements-dev.txt

cd ..\frontend
npm install

# 3. 개발 서버 실행
scripts\start-dev.bat
```

- Backend: http://localhost:8010
- Frontend: http://localhost:5173
- Health: http://localhost:8010/api/health

## 5. 테스트 방법

```bat
# Backend 자동 테스트
scripts\test-backend.bat

# Health API 수동 확인
powershell -Command "(Invoke-WebRequest http://localhost:8010/api/health).Content"

# Frontend 빌드 확인
scripts\build-frontend.bat
```

## 6. 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| `check-environment.bat` | Python/Git/Node 확인 | **PASS** |
| Backend 실행 | 포트 8010 응답 | **PASS** |
| `GET /api/health` | `status: ok` | **PASS** |
| Ollama 미실행 | `ollama: unavailable`, 시스템 정상 | **PASS** |
| Frontend build | 빌드 성공 | **PASS** |
| pytest | 전체 PASS | **6 passed** |
| 로그 기록 | `logs/app.log` 생성 | **PASS** |

**환경 점검 요약**: Python 3.12.10, Git 2.54.0, Node v24.18.0, Ollama unavailable (선택), Port 8010 available

## 7. 현재 제한 사항

- 장비 CRUD, Git 수집, PPT 분석, 검색, AI 분석 — **미구현** (STEP 1 이후)
- Frontend는 개발 모드에서 Vite dev server 필요 (배포 정적 서빙은 STEP 10)
- `TEST-OFFLINE` / `SERVER` / `CLIENT` 환경 수동 검증은 아직 미수행 (DEV 환경만 검증)
- Ollama 연결 테스트는 Integration Test로 분리 예정 (현재 Unit Test는 Mock 사용)

## 8. 다음 STEP 진행 전 확인 사항

STEP 1(장비 관리) 진행 전 확인:

1. `equipment` 테이블 스키마 및 CRUD API 설계
2. `tests/test-data/device-a`, `device-b` 테스트 Git/PPT 폴더 준비
3. Git 경로 검증: `git -C "{repo_path}" rev-parse --is-inside-work-tree`
4. 장비 경로는 **DB 관리** (코드/환경설정 하드코딩 금지)

---

STEP 1 진행을 원하시면 말씀해 주세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 프로젝트 스펙을 먼저 읽고 STEP 0 범위만 확인한 뒤 구현하겠습니다.
- 프로젝트가 비어 있어 STEP 0 전체 구조를 구현합니다.
- 로깅 초기화 순서를 수정한 뒤 의존성 설치와 테스트를 실행합니다.

- 사용 도구: Read×3, Glob, TodoWrite×2, Write×42, StrReplace×5, Shell×13, Await, Grep×2 (총 69회)

---
