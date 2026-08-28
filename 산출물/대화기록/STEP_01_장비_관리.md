# STEP 1. 장비 관리

> **범위**: Cursor 메인 개발 대화 turn **#2 ~ #2** （1턴）
> **이 STEP 요지**: 장비 등록·조회 등 장비 관리 API/화면

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #2 — PROJECT_SPEC.md를 기준으로 STEP 1 장비 관리 기능만 구현해. STEP 0에서 구현한 구조와 기능을 유지하고, …

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 1 — 장비 관리                                                       ║
║  메인 turn #2  |  Monday, Jul 6, 2026, 11:40 AM (UTC+9)                        ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
PROJECT_SPEC.md를 기준으로 STEP 1 장비 관리 기능만 구현해.

STEP 0에서 구현한 구조와 기능을 유지하고, 불필요한 리팩터링은 하지 마.

이번 STEP의 범위는 다음과 같다.

1. equipment 테이블 구현

* id
* name
* git_path
* document_path
* created_at
* updated_at

2. 장비 CRUD API 구현

* GET /api/equipment
* GET /api/equipment/{id}
* POST /api/equipment
* PUT /api/equipment/{id}
* DELETE /api/equipment/{id}

3. Git 경로 검증 구현

* git -C "{repo_path}" rev-parse --is-inside-work-tree 사용
* Python subprocess는 shell=True를 사용하지 말고 Argument List 방식으로 실행
* 한글 및 공백이 포함된 Windows 경로를 고려
* Git Repository가 아닌 경우 사용자에게 이해 가능한 오류 메시지 반환

4. 변경내역서 경로 검증 구현

* 폴더 존재 여부
* 읽기 가능 여부
* .pptx 파일 수 확인
* .ppt 파일은 현재 지원 대상에서 제외
* PPT 내용 분석 기능은 아직 구현하지 마

5. 장비 관리 Frontend 구현

* 장비 목록
* 장비 추가
* 장비 수정
* 장비 삭제
* Git 경로 검증 결과 표시
* 변경내역서 경로 검증 결과 표시

중요:
웹 브라우저에서 운영 PC의 폴더를 선택하는 기능으로 구현하지 마.
입력되는 경로는 Backend가 실행되는 서버 PC 기준 경로다.
따라서 직접 경로 입력 방식을 기본으로 구현해.

6. 테스트 데이터 준비

* tests/test-data/device-a/repository
* tests/test-data/device-a/documents
* tests/test-data/device-b/repository
* tests/test-data/device-b/documents

device-a와 device-b repository는 서로 독립적인 Git Repository로 생성해.

이번 STEP에서는 Git Commit 이력 수집 기능은 구현하지 마.
테스트 Repository에는 초기 Commit 1개 정도만 생성해도 된다.

documents 폴더는 경로 검증 테스트가 가능하도록 준비해.
PPT 내용 분석용 테스트 데이터는 STEP 4에서 확장한다.

7. 테스트 구현
   다음 항목을 반드시 검증해.

* 정상 Git Repository 등록
* 일반 폴더를 Git 경로로 등록할 경우 실패
* 존재하지 않는 경로 등록 실패
* 정상 documents 폴더 등록
* 장비 수정
* 장비 삭제
* Backend 재시작 후 장비 데이터 유지
* 서로 다른 두 장비 등록
* 장비명 중복 처리 정책 확인

장비명 중복은 허용하지 않는 방향으로 구현해.
DB Unique Constraint와 API 오류 처리를 모두 적용해.

STEP 1 범위를 벗어난 다음 기능은 구현하지 마.

* Git Commit 수집
* Git Diff 분석
* PPT Text 추출
* Git-PPT 연계
* Ollama 분석
* AI 검색

구현 완료 후 md파일의 Cursor 단계별 수행 지시 형식에 따라 다음 내용을 보고해.

1. 구현한 기능
2. 생성 또는 수정한 파일
3. 핵심 구현 방식
4. 실행 방법
5. 테스트 방법
6. 테스트 결과
7. 현재 제한 사항
8. 다음 STEP 진행 전 확인 사항

테스트 실패가 발생했다면 실패 내용을 숨기지 말고 원인과 수정 내용을 함께 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 1 완료 보고

## 1. 구현한 기능

- **equipment 테이블** — `id`, `name`(UNIQUE), `git_path`, `document_path`, `created_at`, `updated_at`
- **장비 CRUD API** — 목록/조회/등록/수정/삭제
- **경로 검증 API** — `POST /api/equipment/validate/git`, `POST /api/equipment/validate/document`
- **Git 경로 검증** — `git -C "{path}" rev-parse --is-inside-work-tree` (argument list, UTF-8)
- **변경내역서 경로 검증** — 폴더 존재·읽기 가능·`.pptx` 개수 (`.ppt` 제외, 내용 분석 없음)
- **장비명 중복 방지** — DB `UNIQUE` + API `409` 응답
- **Frontend 장비 관리** — 목록/추가/수정/삭제, 서버 PC 경로 직접 입력, 경로 확인 버튼
- **테스트 데이터** — `device-a`, `device-b` 독립 Git repo + documents 폴더

## 2. 생성 또는 수정한 파일

| 구분 | 파일 |
|---|---|
| DB | `backend/app/db/migrations.py`, `backend/app/db/database.py` |
| Schema | `backend/app/schemas/equipment.py` |
| Service | `backend/app/services/equipment_service.py`, `path_validation_service.py` |
| API | `backend/app/api/equipment.py`, `backend/app/main.py` |
| Tests | `backend/tests/conftest.py`, `backend/tests/test_equipment.py` |
| Frontend | `frontend/src/api/equipment.ts`, `components/EquipmentManager.tsx`, `App.tsx` |
| Scripts | `scripts/setup-test-data.bat` |
| Test data | `tests/test-data/device-a/`, `tests/test-data/device-b/` |
| Docs | `TEST_PLAN.md`, `README.md` |

## 3. 핵심 구현 방식

**등록/수정 시 경로 검증** — 저장 전 Git·documents 경로를 검증하고, 실패 시 사용자 친화 메시지 반환:

```text
Git Repository가 아닙니다.
경로를 찾을 수 없습니다.
```

**Git 검증** — `subprocess.run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"], ...)`
공백·한글 Windows 경로는 `str(path)`로 전달 (shell 미사용).

**장비명 중복** — SQLite `name TEXT NOT NULL UNIQUE` + `IntegrityError` → HTTP 409 `"이미 등록된 장비명입니다."`

**Frontend** — 브라우저 폴더 선택 없음. 서버 PC 절대 경로 직접 입력 + "경로 확인"으로 사전 검증.

## 4. 실행 방법

```bat
# 테스트 데이터 생성 (최초 1회)
scripts\setup-test-data.bat

# 개발 서버
scripts\start-dev.bat
```

- Frontend → **장비 관리** 탭
- 예시 경로 (본인 PC 기준으로 입력):
  - Git: `C:\sourcechangeTrace\tests\test-data\device-a\repository`
  - Documents: `C:\sourcechangeTrace\tests\test-data\device-a\documents`

## 5. 테스트 방법

```bat
scripts\test-backend.bat
# 또는
cd backend
python -m pytest tests\ -v
```

## 6. 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 정상 Git Repository 등록 | 등록 성공 | **PASS** |
| 일반 폴더를 Git 경로로 등록 | Git Repository가 아닙니다. | **PASS** |
| 존재하지 않는 경로 등록 | 경로를 찾을 수 없습니다. | **PASS** |
| 정상 documents 폴더 등록 | PPTX 개수 확인 | **PASS** |
| 장비 수정 | 반영 | **PASS** |
| 장비 삭제 | 삭제 후 404 | **PASS** |
| Backend 재시작 후 데이터 유지 | 유지 | **PASS** |
| 서로 다른 두 장비 등록 | 각각 등록 | **PASS** |
| 장비명 중복 | 409 오류 | **PASS** |
| 공백 포함 경로 Git 검증 | 성공 | **PASS** |
| pytest 전체 | 22 passed | **PASS** |
| Frontend build | 성공 | **PASS** |

**테스트 실패 이력 (수정 완료)**

| 문제 | 원인 | 수정 |
|---|---|---|
| `test_git_path_with_spaces` exit 128 | git user 미설정 | `-c user.email/name` 추가 |
| 동일 테스트 재실행 exit 1 | 고정 경로 repo 상태 공유 | `tmp_path` 격리 사용 |

## 7. 현재 제한 사항

- Git Commit 수집, Diff, PPT Text 추출, Git-PPT 연계, Ollama 분석 — **미구현**
- documents 검증은 `.pptx` **개수만** 확인 (내용·유효성 검사 없음)
- `.ppt` 파일은 무시 (오류 아님)
- 장비 경로는 서버 PC 로컬 경로 — 원격 PC 경로 접근 불가

## 8. 다음 STEP 진행 전 확인 사항

STEP 2(Git 변경 이력 수집) 전 확인:

1. `git_commit`, `git_change` 테이블 스키마 설계
2. `POST /api/equipment/{id}/sync/git` API
3. 증분 동기화 — `equipment_id + commit_hash` UNIQUE
4. 테스트 repo에 Commit 5개 이력 준비 (FareCalc.c 시나리오)
5. `subprocess` encoding=`utf-8"` — 한글 commit message 처리

STEP 2 진행을 원하시면 말씀해 주세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- STEP 1 장비 관리만 구현합니다. 먼저 STEP 0 코드 구조를 확인합니다.
- STEP 1 구현을 시작합니다. 백엔드(DB·API·검증)부터 진행합니다.
- Frontend 장비 관리 UI 구현 중.
- 공백 경로 테스트가 이전 실행 상태에 의존해 실패합니다. `tmp_path`로 격리해 수정합니다.

- 사용 도구: Read×6, Glob, TodoWrite×2, Write×14, StrReplace×12, Shell×6 (총 41회)

---
