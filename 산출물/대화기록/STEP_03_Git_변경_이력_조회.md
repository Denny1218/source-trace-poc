# STEP 3. Git 변경 이력 조회

> **범위**: Cursor 메인 개발 대화 turn **#4 ~ #4** （1턴）
> **이 STEP 요지**: 수집된 Git 변경 이력 Web 조회

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #4 — PROJECT_SPEC.md를 기준으로 STEP 3 Git 이력 조회 화면만 구현해. STEP 0~2에서 구현한 기존 구조와 기…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 3 — Git 변경 이력 조회                                                ║
║  메인 turn #4  |  Monday, Jul 6, 2026, 12:22 PM (UTC+9)                        ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
PROJECT_SPEC.md를 기준으로 STEP 3 Git 이력 조회 화면만 구현해.

STEP 0~2에서 구현한 기존 구조와 기능을 유지해.
불필요한 대규모 리팩터링은 하지 마.

이번 STEP의 목적은 Ollama 또는 PPT 기능 없이 DB에 수집된 Git 변경 이력을 사용자가 검색하고 Commit 상세 및 파일별 Diff를 확인할 수 있도록 하는 것이다.

먼저 Commit 상세 API 식별자 정책을 다음과 같이 적용해.

현재 제안된:

GET /api/git/commits/{commit_hash}

방식은 사용하지 마.

현재 DB는 equipment_id + commit_hash UNIQUE 구조이므로 동일 Commit Hash가 서로 다른 장비 Repository에 존재할 수 있다.

따라서 Commit 상세 API는 git_commit 테이블의 DB id를 사용해.

GET /api/git/commits/{commit_id}

Frontend 화면에는 Commit Hash를 표시하되 내부 상세 조회 API에서는 commit_id를 사용해.

Commit Hash가 시스템 전체에서 UNIQUE하다고 가정하지 마.

---

1. Git Commit 목록 API 구현

다음 API를 구현해.

GET /api/equipment/{equipment_id}/git/commits

지원 Query Parameter:

* q
* date_from
* date_to
* file_path
* author
* page
* page_size

최소 검색 대상:

* git_commit.message
* git_commit.commit_hash
* git_commit.author
* git_change.file_path
* git_change.diff

q 검색은 하나의 검색어로 위 필드를 조회할 수 있도록 해.

예:

q=CHILD_FARE

예상:
Diff에 CHILD_FARE가 포함된 Commit 반환

q=CalcFare

예상:
Diff 또는 관련 파일 변경에 CalcFare가 포함된 Commit 반환

q=어린이 카드

예상:
Commit Message에 해당 문자열이 포함된 Commit 반환

같은 Commit에 여러 git_change가 검색 조건에 일치하더라도 Commit 목록에는 중복 표시하지 마.

SQL JOIN으로 인한 중복 결과를 주의해.

---

2. Pagination 구현

Commit 이력은 실제 Repository에서 많아질 수 있으므로 목록 API에 Pagination을 적용해.

기본값 예:

page=1
page_size=50

page_size 최대값을 설정해.

권장:

최대 200

응답 예:

{
"items": [
{
"id": 1,
"commit_hash": "...",
"commit_date": "...",
"author": "...",
"message": "...",
"changed_file_count": 2,
"additions": 10,
"deletions": 3
}
],
"page": 1,
"page_size": 50,
"total": 120,
"total_pages": 3
}

total은 중복 Commit을 제외한 실제 Commit 수 기준으로 계산해.

---

3. Commit 목록 정렬

기본 정렬:

commit_date DESC

최신 Commit이 위에 표시되게 해.

현재 Git 동기화가 --reverse 순서로 수집되었다고 해서 DB id 순서로 화면 정렬하지 마.

화면 조회 정렬은 commit_date 기준으로 처리해.

---

4. Commit 상세 API

다음 API를 구현해.

GET /api/git/commits/{commit_id}

응답에는 다음 정보를 포함해.

Commit:

* id
* equipment_id
* commit_hash
* commit_date
* author
* message
* parent_hash

Changes:

* id
* file_path
* change_type
* additions
* deletions
* diff

예:

{
"id": 3,
"equipment_id": 1,
"commit_hash": "...",
"commit_date": "...",
"author": "...",
"message": "어린이 카드 요금 처리 추가",
"parent_hash": "...",
"changes": [
{
"id": 5,
"file_path": "FareCalc.c",
"change_type": "modified",
"additions": 4,
"deletions": 1,
"diff": "..."
}
]
}

존재하지 않는 commit_id는 404를 반환해.

---

5. Git 이력 Frontend 구현

Git 이력 조회 화면을 추가해.

메뉴 또는 Tab 이름:

변경 이력

화면 기본 구조:

장비 선택
↓
검색 조건
↓
Commit 목록
↓
Commit 상세

검색 조건:

* 통합 검색어
* 기간 시작일
* 기간 종료일
* 파일 경로
* 작성자

초기 화면에서는 지나치게 복잡한 Advanced Search UI를 만들지 마.

통합 검색어를 가장 크게 표시하고 나머지 조건은 단순 Filter 형태로 배치해.

---

6. Commit 목록 화면

Commit 목록에는 최소 다음 항목을 표시해.

* Commit Message
* Commit Hash 축약형
* Commit Date
* Author
* 변경 파일 수
* additions
* deletions

Commit Hash는 화면에서 7~10자리 축약 표시해.

예:

a82bc93

단, Tooltip 또는 상세 화면에서는 전체 Hash를 확인할 수 있게 해.

목록에서 Commit을 선택하면 Commit 상세 정보를 조회해.

---

7. Commit 상세 화면

Commit 상세에는 다음을 표시해.

* 전체 Commit Hash
* Date
* Author
* Message
* Parent Hash

변경 파일 목록:

FareCalc.c
modified
+4
-1

README.md
modified
+2
-0

변경 파일을 선택하면 해당 git_change.diff를 표시해.

한 Commit의 모든 Diff를 한 번에 펼쳐서 표시하지 마.

기본 흐름:

Commit 선택
↓
변경 파일 목록
↓
파일 선택
↓
선택 파일 Diff 표시

실제 Commit에서 변경 파일이 많을 수 있기 때문이다.

---

8. Diff 표시

Diff는 최소 다음 라인을 시각적으로 구분해.

* 추가 라인

- 삭제가 아니라 Git 기준 + 추가 라인

* 삭제 라인

@@ hunk header

context line

주의:
CSS에서 단순히 line.includes("+") 방식으로 판별하지 마.

라인 시작 기준으로 처리해.

단 다음 Header를 실제 추가/삭제 코드로 잘못 표시하지 않도록 고려해.

## +++

현재 STEP 2 Diff에 Git Header가 최소화되어 있을 가능성이 있지만 안정적으로 처리해.

권장 판별 순서:

1. +++ / --- header
2. @@ hunk
3. * added
4. * deleted
5. context

Binary Diff:

[binary file]

이면 코드 Diff처럼 렌더링하지 말고 다음과 같이 표시해.

Binary 파일 변경입니다.
내용 Diff는 저장하지 않습니다.

---

9. 검색 UX

검색은 버튼 방식 또는 Enter 방식 모두 가능하다.

검색 조건이 변경될 때마다 API를 과도하게 호출하지 마.

통합 검색어 실시간 검색을 구현할 경우 debounce를 적용해.

다만 이번 POC에서는 단순하게:

검색어 입력
↓
검색 버튼

방식을 사용해도 된다.

검색 결과가 없으면:

검색 결과가 없습니다.

라고 표시해.

API Error와 검색 결과 0건을 동일하게 표시하지 마.

---

10. 장비 데이터가 없는 경우

등록 장비가 없으면:

먼저 장비 관리에서 장비를 등록하십시오.

라고 표시해.

장비는 있지만 Git 동기화 데이터가 없다면:

Git 변경 이력이 없습니다.
장비 관리 또는 동기화 기능을 확인하십시오.

라고 표시해.

현재 Frontend에 Git 동기화 버튼이 없다면 이번 STEP에서 Git 이력 화면에 단순한:

Git 동기화

버튼을 추가해도 된다.

버튼은 기존:

POST /api/equipment/{id}/sync/git

API를 호출한다.

동기화 완료 후 목록을 다시 조회해.

동기화 진행 중에는 중복 클릭을 방지해.

---

11. 테스트 구현

Backend 테스트:

* Commit 목록 조회
* 최신 날짜 순 정렬
* Pagination
* page_size 최대 제한
* q=CHILD_FARE 검색
* q=CalcFare 검색
* 한글 Commit Message 검색
* file_path Filter
* author Filter
* date_from Filter
* date_to Filter
* JOIN으로 인한 Commit 중복 없음
* total 값 정확성
* Commit 상세 조회
* 존재하지 않는 commit_id 404
* 동일 Commit Hash가 서로 다른 equipment에 존재하더라도 DB id 기준 상세 조회 정상

마지막 테스트는 중요하다.

동일 Git 이력을 가진 Repository 또는 테스트 데이터를 만들어 동일 commit_hash가 equipment A와 B에 존재하는 상황을 검증해.

Frontend build도 반드시 확인해.

---

12. 현재 Test Data 확인

device-a의 FareCalc.c Commit 이력이 실제 검색에 사용할 수 있는지 확인해.

다음 검색 결과가 존재해야 해.

CHILD_FARE
CalcFare
어린이 카드

테스트 데이터가 현재 조건을 충족하지 않는다면 최소 범위에서 setup_repositories.py를 수정해.

테스트를 맞추기 위해 Production 검색 코드를 왜곡하지 마.

---

13. Logging

다음 로그를 추가해.

Git history search

* equipment_id
* 검색 조건 존재 여부
* result_count

Commit detail read

* commit_id

사용자가 입력한 전체 검색어를 로그에 반드시 저장할 필요는 없어.
민감 코드 문자열이 검색어에 포함될 가능성을 고려해.

Full Diff를 로그에 출력하지 마.

---

14. 이번 STEP에서 구현하지 않을 기능

다음 기능은 구현하지 마.

* PPT 분석
* PPT 검색
* Git-PPT 연계
* Ollama
* AI 검색
* Vector DB
* git blame
* 코드 파일 Viewer
* Line 선택 기능

이번 STEP은 Git 변경 이력 조회까지만 구현해.

---

15. 완료 후 보고

PROJECT_SPEC.md의 Cursor 단계별 수행 지시 형식으로 결과를 보고해.

1. 구현한 기능
2. 생성 또는 수정한 파일
3. 핵심 구현 방식
4. 실행 방법
5. 테스트 방법
6. 테스트 결과
7. 현재 제한 사항
8. 다음 STEP 진행 전 확인 사항

추가로 STEP 3에서는 다음 내용을 반드시 보고해.

* Commit 목록 SQL 검색 구조
* JOIN 중복 Commit 제거 방식
* Pagination total 계산 방식
* Commit 상세 API가 DB commit_id를 사용하는지
* 동일 commit_hash 다중 equipment 테스트 결과
* Diff Line 분류 방식
* Binary Diff 표시 방식
* Frontend build 결과
* 테스트 실패 이력 및 수정 내용

테스트 실패가 발생했다면 실패 내용을 숨기지 말고 원인과 수정 내용을 함께 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 3 완료 보고

## 1. 구현한 기능

- **Commit 목록 API**: `GET /api/equipment/{equipment_id}/git/commits`
  - Query: `q`, `date_from`, `date_to`, `file_path`, `author`, `page`, `page_size`
- **Commit 상세 API**: `GET /api/git/commits/{commit_id}` (DB id 사용)
- **Pagination**: 기본 `page_size=50`, 최대 200
- **정렬**: `commit_date DESC`
- **Frontend "변경 이력" 탭**: 장비 선택, 검색, 목록, 상세, 파일별 Diff
- **Git 동기화 버튼**: `POST /api/equipment/{id}/sync/git` 호출
- **Logging**: 검색/상세 조회 로그

## 2. 생성 또는 수정한 파일

| 구분 | 파일 |
|---|---|
| Service | `backend/app/services/git_history_service.py` |
| Schema | `backend/app/schemas/git_history.py` |
| API | `backend/app/api/git_history.py`, `main.py` |
| Tests | `backend/tests/test_git_history.py` |
| Frontend | `api/gitHistory.ts`, `components/GitHistory.tsx`, `DiffViewer.tsx`, `App.tsx` |
| Docs | `README.md`, `TEST_PLAN.md` |

## 3. 핵심 구현 방식

### Commit 목록 SQL 검색 구조

```sql
-- WHERE: equipment_id + 선택 필터
-- q 검색: message, commit_hash, author + EXISTS(git_change file_path/diff)
-- file_path: EXISTS(git_change ...)
-- COUNT: SELECT COUNT(*) FROM (SELECT gc.id ... GROUP BY gc.id)
-- LIST: LEFT JOIN git_change + GROUP BY gc.id + ORDER BY commit_date DESC
```

### JOIN 중복 Commit 제거

- 목록/집계 모두 `GROUP BY gc.id`
- `q` 검색 시 `EXISTS` 서브쿼리로 `git_change` JOIN 중복 방지

### Pagination total 계산

- `GROUP BY gc.id` 서브쿼리의 `COUNT(*)` → 중복 없는 Commit 수

### Commit 상세 API 식별자

- **`GET /api/git/commits/{commit_id}`** — `git_commit.id` 사용
- `commit_hash`는 화면 표시용, API 식별자로 사용하지 않음

### Diff Line 분류 (Frontend)

라인 **시작 기준** 순서:

1. `+++ ` / `--- ` → file-header
2. `@@` → hunk
3. `+` → added
4. `-` → deleted
5. ` ` (공백) → context

### Binary Diff 표시

- `diff === "[binary file]"` → 코드 Diff 미렌더링
- "Binary 파일 변경입니다. 내용 Diff는 저장하지 않습니다." 표시

## 4. 실행 방법

```bat
scripts\start-dev.bat
```

1. **장비 관리** → 장비 등록
2. **변경 이력** → 장비 선택 → **Git 동기화**
3. 검색어 입력 후 **검색** (예: `CHILD_FARE`, `CalcFare`, `어린이 카드`)

## 5. 테스트 방법

```bat
scripts\test-backend.bat          # 54 passed
cd frontend && npm run build      # build 성공
```

## 6. 테스트 결과

| 테스트 | 결과 |
|---|---|
| Commit 목록 / 정렬 / Pagination | **PASS** |
| q=CHILD_FARE / CalcFare / 어린이 카드 | **PASS** |
| file_path, author, date Filter | **PASS** |
| JOIN 중복 없음 / total 정확성 | **PASS** |
| Commit 상세 / 404 | **PASS** |
| **동일 commit_hash 다중 equipment** | **PASS** |
| pytest 전체 | **54 passed** |
| Frontend build | **PASS** |

### 동일 commit_hash 다중 equipment 테스트

- 동일 `.git` 복사본으로 equipment A/B 등록 후 각각 sync
- 같은 `commit_hash`에 대해 **서로 다른 DB `id`**
- `GET /api/git/commits/{id}`로 equipment별 상세 조회 정상

### 테스트 실패 이력

| 문제 | 수정 |
|---|---|
| Frontend `Equipment` unused import | import 제거 후 build 성공 |

## 7. 현재 제한 사항

- PPT, Git-PPT 연계, Ollama, AI 검색 — **미구현**
- git blame, 코드 Viewer, Line 선택 — **미구현**
- 검색은 **검색 버튼** 방식 (실시간 debounce 없음)
- Full-text search 인덱스 없음 (LIKE 기반)

## 8. 다음 STEP 진행 전 확인 사항

STEP 4(PPT 변경내역서 분석) 전 확인:

1. `document`, `document_slide` 테이블
2. `POST /api/equipment/{id}/sync/documents`
3. python-pptx Text 추출
4. device-a `documents/` 폴더에 실제 PPTX 테스트 데이터 확장

---

**검색 확인 (device-a FareCalc 이력)**

| 검색어 | 결과 |
|---|---|
| CHILD_FARE | Diff 매칭 Commit 존재 |
| CalcFare | Diff/파일 매칭 Commit 존재 |
| 어린이 카드 | Commit Message 매칭 존재 |

### ◇ 진행 과정 요약（도구·짧은 안내만）

- STEP 3 Git 이력 조회 구현을 시작합니다. 기존 백엔드·프론트엔드 구조를 확인합니다.

- 사용 도구: Read×8, Write×9, StrReplace×8, Shell×3 (총 28회)

---
