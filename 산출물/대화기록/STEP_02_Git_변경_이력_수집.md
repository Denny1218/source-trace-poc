# STEP 2. Git 변경 이력 수집

> **범위**: Cursor 메인 개발 대화 turn **#3 ~ #3** （1턴）
> **이 STEP 요지**: 장비별 Git Repository 연동 및 Commit 이력 수집

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #3 — PROJECT_SPEC.md를 기준으로 STEP 2 Git 변경 이력 수집 기능만 구현해. STEP 0과 STEP 1에서 구현한…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 2 — Git 변경 이력 수집                                                ║
║  메인 turn #3  |  Monday, Jul 6, 2026, 12:07 PM (UTC+9)                        ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
PROJECT_SPEC.md를 기준으로 STEP 2 Git 변경 이력 수집 기능만 구현해.

STEP 0과 STEP 1에서 구현한 구조와 기존 기능을 유지해.
기존 CRUD, 경로 검증, Frontend 기능을 불필요하게 리팩터링하지 마.

먼저 현재 STEP 1 문서의 제한 사항 중 다음 표현을 수정해.

기존:
장비 경로는 서버 PC 로컬 경로 — 원격 PC 경로 접근 불가

변경:
장비 경로는 Backend 서버에서 접근 가능한 경로를 기준으로 한다.
서버 로컬 경로를 기본 지원한다.
UNC 네트워크 경로는 서버 실행 계정의 접근 권한 및 Git 동작 여부에 따라 사용할 수 있으며 실제 운영 환경에서 별도 검증이 필요하다.

UNC 경로 지원 기능을 이번 STEP에서 별도로 구현하거나 강제하지는 마.

이번 STEP의 범위는 Git Commit 및 파일 변경 이력 수집이다.

1. DB Schema 구현

git_commit 테이블을 구현해.

필드:

* id
* equipment_id
* commit_hash
* commit_date
* author
* message
* parent_hash

제약 조건:

* equipment_id는 equipment.id 참조
* equipment_id + commit_hash UNIQUE

git_change 테이블을 구현해.

필드:

* id
* commit_id
* file_path
* change_type
* additions
* deletions
* diff

commit_id는 git_commit.id를 참조해.

장비 삭제 시 관련 Git 데이터 처리 정책을 명확히 정해.
POC 단계에서는 equipment 삭제 시 관련 git_commit과 git_change도 함께 삭제되는 CASCADE 방식을 우선 검토해.

SQLite Foreign Key가 실제로 활성화되어 있는지 반드시 확인해.

2. Git 동기화 API 구현

다음 API를 구현해.

POST /api/equipment/{id}/sync/git

응답에는 최소 다음 정보를 포함해.

* equipment_id
* scanned_commits
* new_commits
* skipped_commits
* new_changes
* status

예:

{
"equipment_id": 1,
"scanned_commits": 5,
"new_commits": 5,
"skipped_commits": 0,
"new_changes": 7,
"status": "completed"
}

동기화 실패 시 전체 Python Stack Trace를 사용자에게 반환하지 마.
상세 오류는 로그에 기록하고 API에는 이해 가능한 메시지를 반환해.

3. Git Commit 수집

Git CLI를 사용해.

Python subprocess는 계속 다음 원칙을 유지해.

* shell=True 사용 금지
* Argument List 사용
* capture_output=True
* text=True
* 명시적인 encoding 처리
* Windows 한글 및 공백 경로 고려

Commit에서 다음 정보를 수집해.

* commit hash
* commit date
* author
* commit message
* parent hash

Merge Commit은 parent가 여러 개일 수 있다는 점을 고려해.

현재 DB Schema가 parent_hash 단일 필드이므로 이번 STEP에서는 다음 정책 중 단순한 방식을 선택해.

권장:
첫 번째 Parent Hash만 parent_hash에 저장한다.

단, 이 제한 사항을 코드 주석과 STEP 결과 보고에 명확히 기록해.

Merge Commit 전체 Parent 구조 지원을 위해 별도 테이블을 추가하지 마.

4. Git 변경 파일 수집

각 신규 Commit에 대해 변경 파일 정보를 수집해.

수집 정보:

* file_path
* change_type
* additions
* deletions
* diff

change_type은 최소 다음 상태를 구분해.

* added
* modified
* deleted
* renamed

가능하면 Git의 name-status 또는 numstat 결과를 활용해.

중요:
Binary 파일은 일반 Text Diff로 처리하려고 하지 마.

Binary 파일인 경우:

* 파일 변경 정보는 저장
* additions / deletions는 nullable 또는 0 정책 중 일관된 방식을 사용
* diff에는 전체 바이너리 내용을 저장하지 않음

Binary 처리 정책을 결과 보고에 기록해.

5. Diff 저장

Text 파일 변경에 대해 Commit Diff를 저장해.

Diff는 검색 기능에서 사용할 예정이므로 실제 변경 라인을 포함해야 해.

단, 다음은 피해야 해.

* git show 전체 결과를 commit마다 그대로 중복 저장
* Commit Metadata를 diff 필드에 반복 저장

git_change.diff에는 해당 파일 변경 Diff만 저장해.

가능하면 다음 형태를 유지해.

diff --git 등 Git Header는 최소화하거나 제거 가능하지만,
다음 변경 표시는 유지해.

@@

* 삭제 라인

- 추가 라인
  context

Diff Parsing 구현이 지나치게 복잡해지면 Git file별 diff 명령을 호출하는 단순한 방식을 우선 사용해.

현재 단계에서는 성능 최적화보다 정확성과 테스트 가능성을 우선해.

6. 증분 동기화

첫 동기화:
Repository의 기존 Commit 전체 수집

재동기화:
이미 DB에 존재하는 equipment_id + commit_hash Commit은 중복 저장하지 마.

중요:
단순히 DB의 마지막 Commit 하나 이후만 조회하는 구현은 우선 피하는 것을 권장해.

Git Repository에서 branch가 변경되거나 새로운 branch 이력이 추가될 수 있기 때문이다.

이번 STEP에서는 다음 방식을 우선 검토해.

git log --all
↓
Commit Hash 목록 확인
↓
DB에 존재하는 Commit Skip
↓
신규 Commit만 상세 분석

테스트 Repository 규모에서는 이 방식으로 충분하다.

향후 대규모 Repository 성능 문제가 확인되면 최적화한다.

7. 테스트 Git Repository 확장

device-a Repository에 최소 다음 Commit 이력을 구성해.

Commit 1
FareCalc.c 최초 생성

Commit 2
DEFAULT_FARE 추가

Commit 3
CHILD_FARE 처리 추가

Commit 4
CalcFare 조건 수정

Commit 5
README 수정

예시 코드 흐름이 실제 Diff 검색 테스트에 사용할 수 있도록
FareCalc.c에 CHILD_FARE와 CalcFare 문자열이 실제로 포함되게 해.

가능하면 Commit Message는 일부 한글을 사용해.

예:

FareCalc 최초 생성
기본 요금 처리 추가
어린이 카드 요금 처리 추가
CalcFare 조건 수정
README 수정

device-b도 독립 Repository 상태를 유지해.

device-a와 동일 Commit Hash 또는 데이터에 의존하지 마.

8. 테스트 구현

다음 테스트를 반드시 구현해.

* 최초 Git 동기화
  예상: Commit 5개 수집

* 동일 Repository 재동기화
  예상: 신규 Commit 0
  중복 Commit 0
  중복 git_change 0

* 신규 Commit 생성 후 재동기화
  예상: 신규 Commit 1

* Commit Message 한글 처리
  예상: 문자 깨짐 없음

* 공백 포함 Repository 경로
  예상: 정상 동기화

* Git Repository가 아닌 경로 동기화
  예상: 사용자 친화 오류

* 존재하지 않는 equipment ID
  예상: 404

* 두 장비 독립 동기화
  예상: equipment별 데이터 분리

* equipment 삭제
  예상: 관련 git_commit, git_change 데이터 처리 정책 검증

* Binary 파일 Commit
  예상: 동기화 실패 없음
  Binary Diff 전체 저장 없음

* renamed 파일
  예상: change_type renamed 처리 확인

가능하면 Service Unit Test와 API Test를 구분해.

9. Logging

다음 로그를 추가해.

Git sync started
equipment_id
equipment_name

Git sync completed
scanned_commits
new_commits
skipped_commits
new_changes

Git command error
command 종류
return code

Full Diff 전체 내용을 로그에 출력하지 마.

Commit Message 전체 로그 출력도 필수는 아니다.

10. 이번 STEP에서 구현하지 않을 기능

다음은 구현하지 마.

* Git 검색 UI
* Commit 상세 Frontend
* Diff 시각화
* PPT Text 추출
* PPT 동기화
* Git-PPT 연계
* Ollama
* AI 검색
* Vector DB
* git blame

Git 이력 조회 화면은 STEP 3에서 구현한다.

11. 완료 후 보고

PROJECT_SPEC.md의 Cursor 단계별 수행 지시 형식에 따라 다음 내용을 보고해.

1. 구현한 기능
2. 생성 또는 수정한 파일
3. 핵심 구현 방식
4. 실행 방법
5. 테스트 방법
6. 테스트 결과
7. 현재 제한 사항
8. 다음 STEP 진행 전 확인 사항

추가로 STEP 2에서는 다음 내용을 반드시 보고해.

* 실제 사용한 Git 명령
* Merge Commit parent_hash 처리 정책
* Binary 파일 처리 정책
* Rename 처리 방식
* 증분 동기화 방식
* SQLite Foreign Key 활성화 여부 및 CASCADE 동작 테스트 결과
* 테스트 실패 이력과 수정 내용

테스트 실패가 발생했다면 실패 내용을 숨기지 말고 원인과 수정 내용을 함께 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 2 완료 보고

## 1. 구현한 기능

- **DB Schema**: `git_commit`, `git_change` 테이블 + FK CASCADE
- **Git 동기화 API**: `POST /api/equipment/{id}/sync/git`
- **Commit 수집**: hash, date, author, message, parent_hash
- **변경 파일 수집**: file_path, change_type, additions, deletions, diff
- **증분 동기화**: `git log --all` → DB 미존재 hash만 수집
- **장비 삭제 시 CASCADE**: `git_commit` / `git_change` 함께 삭제
- **테스트 데이터**: device-a 5-commit 이력, device-b 독립 repo
- **STEP 1 경로 정책 문구 수정** (`README.md`)

## 2. 생성 또는 수정한 파일

| 구분 | 파일 |
|---|---|
| DB | `backend/app/db/migrations.py` |
| Service | `backend/app/services/git_service.py` |
| API | `backend/app/api/git_history.py`, `main.py` |
| Schema | `backend/app/schemas/git_history.py` |
| Tests | `backend/tests/test_git_sync.py`, `conftest.py` |
| Test data | `tests/test-data/setup_repositories.py` |
| Scripts | `scripts/setup-test-data.bat` |
| Docs | `README.md`, `TEST_PLAN.md` |

## 3. 핵심 구현 방식

### 실제 사용한 Git 명령

| 용도 | 명령 |
|---|---|
| Commit 목록 | `git -C {repo} log --all --pretty=format:%H --reverse` |
| Commit 메타 | `git log -1 --pretty=format:%aI / %an / %B / %P` |
| 변경 파일 | `git show --name-status --pretty=format: {hash}` |
| 라인 통계 | `git show --numstat --pretty=format: {hash}` |
| 파일 Diff | `git show {hash} --pretty=format: --no-color --unified=3 -- {path}` |

### Merge Commit `parent_hash` 정책

- `%P` 결과의 **첫 번째 parent만** 저장
- 별도 parent 테이블 없음 (`git_service.py` 모듈 주석에 명시)

### Binary 파일 처리 정책

- `numstat`이 `- - path`이면 binary로 판단
- `additions` / `deletions` → **NULL**
- `diff` → **`[binary file]`** (바이너리 내용 미저장)

### Rename 처리

- `git show --name-status`의 `R100 old new` 파싱
- `change_type = renamed`, `file_path = 새 경로`
- numstat `old => new` 키 매칭

### 증분 동기화

```
git log --all → hash 목록
→ DB에 있는 equipment_id + commit_hash Skip
→ 신규 hash만 메타·변경·diff 수집
```

### SQLite Foreign Key

- `get_connection()` / `init_database()`에서 `PRAGMA foreign_keys=ON`
- 테스트 `test_foreign_keys_enabled`: **PRAGMA foreign_keys = 1** 확인
- `test_equipment_delete_cascades_git_data`: equipment 삭제 후 git 데이터 **0건** 확인

### 장비 경로 정책 (STEP 1 수정)

> 장비 경로는 Backend 서버에서 접근 가능한 경로를 기준으로 한다. 서버 로컬 경로를 기본 지원한다. UNC 네트워크 경로는 서버 실행 계정의 접근 권한 및 Git 동작 여부에 따라 사용할 수 있으며, 실제 운영 환경에서 별도 검증이 필요하다.

## 4. 실행 방법

```bat
# 테스트 데이터 (공유 repo — Windows 잠금 시 경고만 출력)
scripts\setup-test-data.bat

# 개발 서버
scripts\start-dev.bat

# Git 동기화 (equipment id=1 예시)
curl -X POST http://localhost:8010/api/equipment/1/sync/git
```

## 5. 테스트 방법

```bat
scripts\test-backend.bat
# 37 passed
```

## 6. 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 최초 동기화 | Commit 5 | **PASS** |
| 재동기화 | 신규 0, 중복 0 | **PASS** |
| 신규 Commit 후 | 신규 1 | **PASS** |
| 한글 Message | 깨짐 없음 | **PASS** |
| 공백 경로 | 정상 | **PASS** |
| Git 아닌 경로 | 400 | **PASS** |
| equipment 없음 | 404 | **PASS** |
| 두 장비 독립 | 분리 | **PASS** |
| CASCADE 삭제 | git 데이터 삭제 | **PASS** |
| Binary | diff 미저장 | **PASS** |
| renamed | change_type renamed | **PASS** |
| **pytest 전체** | | **37 passed** |

### 테스트 실패 이력 및 수정

| 문제 | 원인 | 수정 |
|---|---|---|
| Windows `PermissionError` (rmtree) | Git 객체 파일 잠금 | 테스트 repo를 `tmp_path` 격리 |
| rename 미감지 | `diff-tree`가 A+D로 분리 | `git show --name-status` 사용 |
| commit 수 5 초과 | 공유 repo 오염 | 격리 fixture + `mkdir` 추가 |

## 7. 현재 제한 사항

- Merge Commit은 **첫 parent만** 저장
- Git 검색 UI / Commit 상세 / Diff 시각화 — **STEP 3**
- PPT, Git-PPT 연계, Ollama — **미구현**
- 대규모 repo 성능 최적화 없음 (POC 규모 기준)
- UNC 경로 — 별도 구현·검증 없음 (정책만 문서화)
- 공유 `tests/test-data` repo는 Windows에서 재빌드 실패 가능 (테스트는 격리 repo 사용)

## 8. 다음 STEP 진행 전 확인 사항

STEP 3(Git 이력 조회 화면) 전 확인:

1. `GET /api/equipment/{id}/git/commits` API
2. `GET /api/git/commits/{commit_hash}` API
3. Frontend: 장비 선택, 검색, Commit 목록/상세, Diff 표시
4. AI 없이 `CHILD_FARE`, `CalcFare` 검색 가능해야 함
5. device-a FareCalc.c diff가 검색 테스트에 사용 가능한지 확인

STEP 3 진행을 원하시면 말씀해 주세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- STEP 2 Git 이력 수집 구현을 시작합니다. STEP 1 코드와 스펙을 확인합니다.
- 구현을 진행합니다. DB 스키마·Git 서비스·API·테스트 데이터부터 추가합니다.
- Windows 권한 오류와 초기 커밋 파싱 문제를 수정 중입니다.
- `git show --name-status`로 변경 파일 파싱을 전환합니다.
- 공유 테스트 저장소가 오염되어 `fresh_device_a` 픽스처로 격리합니다.
- Windows 파일 잠금을 피하기 위해 Git 테스트를 `tmp_path` 격리 저장소로 전환합니다.

- 사용 도구: Read×11, Grep×3, Write×8, StrReplace×38, Shell×13, Await (총 74회)

---
