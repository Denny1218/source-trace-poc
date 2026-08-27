## STEP 0 프로젝트 기본 실행 환경

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| check-environment.bat | Python/Git/Node 확인 | PASS |
| Backend 실행 | 포트 8010 응답 | PASS |
| GET /api/health | status ok 응답 | PASS |
| Ollama 미실행 시 | ollama unavailable, status ok | PASS |
| Frontend build | 빌드 성공 | PASS |
| pytest | 6 passed | PASS |
| 로그 기록 | logs/app.log 생성 | PASS |

### 문제

없음

### 원인

-

### 수정

-

### 재테스트

-

---

## STEP 1 장비 관리

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

TEST_DEVICE_A, TEST_DEVICE_B (`tests/test-data/`)

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 정상 Git Repository 등록 | 등록 성공 | PASS |
| 일반 폴더를 Git 경로로 등록 | Git Repository가 아닙니다. | PASS |
| 존재하지 않는 경로 등록 | 경로를 찾을 수 없습니다. | PASS |
| 정상 documents 폴더 등록 | PPTX 개수 확인 | PASS |
| 장비 수정 | 이름 변경 반영 | PASS |
| 장비 삭제 | 404 after delete | PASS |
| Backend 재시작 후 데이터 유지 | 데이터 유지 | PASS |
| 서로 다른 두 장비 등록 | 각각 등록 | PASS |
| 장비명 중복 | 409 오류 | PASS |
| 공백 포함 경로 Git 검증 | 검증 성공 | PASS |
| pytest 전체 | 22 passed | PASS |
| Frontend build | 빌드 성공 | PASS |

### 문제

1. `test_git_path_with_spaces` 초기 실패 — git commit 시 user.name/email 미설정 (exit 128)
2. 동일 테스트 재실행 실패 — 프로젝트 내 고정 경로에 이미 커밋된 repo 존재 (exit 1, nothing to commit)

### 원인

1. 테스트용 Git 저장소에서 사용자 정보 없이 commit 실행
2. 고정 경로 재사용으로 테스트 간 상태 공유

### 수정

1. commit 명령에 `-c user.email` / `-c user.name` 옵션 추가
2. `tmp_path` 격리 경로 사용으로 테스트 독립성 확보

### 재테스트

PASS

---

## STEP 2 Git 변경 이력 수집

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

TEST_DEVICE_A (격리 tmp repo 5 commits), TEST_DEVICE_B

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 최초 Git 동기화 | Commit 5 | PASS |
| 재동기화 | 신규 0, 중복 0 | PASS |
| 신규 Commit 후 동기화 | 신규 1 | PASS |
| 한글 Commit Message | 깨짐 없음 | PASS |
| 공백 포함 경로 | 정상 동기화 | PASS |
| Git Repository 아님 | 400 오류 | PASS |
| 존재하지 않는 equipment | 404 | PASS |
| 두 장비 독립 동기화 | 데이터 분리 | PASS |
| equipment 삭제 CASCADE | git 데이터 삭제 | PASS |
| Binary 파일 | diff 미저장, 동기화 성공 | PASS |
| renamed 파일 | change_type renamed | PASS |
| Foreign Key 활성화 | PRAGMA foreign_keys=1 | PASS |
| pytest 전체 | 37 passed | PASS |

### 문제

1. Windows `shutil.rmtree` PermissionError (공유 test-data repo)
2. `diff-tree`가 rename을 A+D로 분리 표시
3. 공유 repo 오염으로 commit 수 5 초과

### 원인

1. Git 객체 파일 잠금
2. `git diff-tree` vs `git show --name-status` 출력 차이
3. 테스트가 공유 repo에 commit 추가

### 수정

1. Git 테스트는 `tmp_path` 격리 repo 사용
2. 파일 목록 수집을 `git show --name-status`로 변경
3. `_apply_commits`에 `mkdir` 추가, `fresh` fixture로 격리

### 재테스트

PASS

---

## STEP 3 Git 이력 조회

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| Commit 목록 조회 | 5건 | PASS |
| commit_date DESC 정렬 | 최신 우선 | PASS |
| Pagination | page/total | PASS |
| page_size 최대 200 | 제한 | PASS |
| q=CHILD_FARE | 1건 이상 | PASS |
| q=CalcFare | 1건 이상 | PASS |
| q=어린이 카드 | 한글 검색 | PASS |
| file_path/author/date Filter | PASS | PASS |
| JOIN 중복 없음 | unique id | PASS |
| Commit 상세 (commit_id) | 200 | PASS |
| commit_id 404 | 404 | PASS |
| 동일 hash 다중 equipment | id별 상세 | PASS |
| pytest 전체 | 54 passed | PASS |
| Frontend build | 성공 | PASS |

### 문제

Frontend build: `Equipment` unused import

### 원인

re-export와 import 중복

### 수정

불필요 import 제거

### 재테스트

PASS

---

## STEP 4 변경 추적 요청 API 및 Trace 흐름

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| POST /api/trace/search | 200 | PASS |
| q=CHILD_FARE | Top 5 후보 | PASS |
| q=CalcFare | Commit 후보 | PASS |
| q=어린이 카드 | 한글 검색 | PASS |
| file_path 우선 | FareCalc.c | PASS |
| selected_code Symbol | CHILD_FARE 추출 | PASS |
| search_context | keywords/date | PASS |
| match_reasons | score 근거 | PASS |
| equipment 404 | 404 | PASS |
| pytest 전체 | 67 passed | PASS |

### 문제

없음

### 원인

-

### 수정

-

### 재테스트

PASS

---

## STEP 5 Git 기반 PPT 후보 탐색

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

`tests/test-data/device-a/documents/` (setup_ppt_documents.py)

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| document_path 하위 재귀 탐색 | .pptx 수집 | PASS |
| .pptx / .PPTX 포함 | 대소문자 무시 | PASS |
| .ppt 제외 | legacy/*.ppt 미포함 | PASS |
| ~$*.pptx 제외 | 임시 파일 미포함 | PASS |
| 날짜 형식 4종 Parse | 20240315 등 | PASS |
| 폴더명 날짜 추출 | 2024-03-15 폴더 | PASS |
| 잘못된 날짜 Skip | 20241345 무점수 | PASS |
| 파일명/폴더명 Keyword | match_reasons | PASS |
| 대소문자 Keyword | 무시 매칭 | PASS |
| modified_at 보조 점수 | 약한 가산 | PASS |
| 장비 Context | AG 토큰 | PASS |
| candidate_score DESC 정렬 | 상위 점수 우선 | PASS |
| Candidate Limit | 상위 N건만 | PASS |
| score 0 / primary 없음 제외 | 무관 PPT 미포함 | PASS |
| 후보 없음 | 빈 배열 정상 | PASS |
| equipment 404 | 404 | PASS |
| document_path 없음/접근불가 | 400 | PASS |
| 두 장비 경로 분리 | 독립 탐색 | PASS |
| 개별 stat 실패 | 전체 탐색 계속 | PASS |
| POST /api/trace/ppt-candidates | 200 | PASS |
| pytest test_ppt_candidate | 22 passed | PASS |
| pytest 전체 | 89 passed | PASS |

### 문제

1. `test_ppt_candidate_empty_ok` 실패 — equipment_context만으로 무관 PPT가 후보에 포함
2. `test_individual_stat_failure_continues` 실패 — `is_file()` OSError 시 탐색 중단

### 원인

1. primary match(날짜/Keyword) 없이 equipment_context·modified_at만으로 후보 선정 가능
2. `_iter_pptx_files`에서 `is_file()` 예외 미처리

### 수정

1. primary_reasons 게이트 추가 (filename_date/folder_date/filename_keyword/folder_keyword 중 하나 필수)
2. `is_file()` 호출을 try/except로 감싸 skip + 로그

### 재테스트

PASS

---

## STEP 6 PPT On-demand 분석 및 Cache

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

`tests/test-data/ppt-fixtures/` (setup_ppt_fixtures.py)

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| document_cache / slide_cache 생성 | PASS | PASS |
| equipment 삭제 CASCADE | PASS | PASS |
| document_cache 삭제 CASCADE | PASS | PASS |
| UNIQUE 제약 | PASS | PASS |
| SHA-256 Chunk Hash | PASS | PASS |
| modified_at만 변경 → Cache Hit | PASS | PASS |
| Hash 변경 → 재Parsing | PASS | PASS |
| Parse 실패 시 기존 Cache 유지 | PASS | PASS |
| 신규 Parse 실패 → Cache 미생성 | PASS | PASS |
| Cache 삭제 후 재Parsing | PASS | PASS |
| Title/TextBox/Table/Group 추출 | PASS | PASS |
| 빈 Slide 저장 / Slide 번호 1부터 | PASS | PASS |
| PPT_PARSE_LIMIT 적용 | PASS | PASS |
| Slide Candidate Keyword | PASS | PASS |
| 손상 PPTX → 다른 PPT 계속 | PASS | PASS |
| POST /api/trace/ppt-analysis | PASS | PASS |
| Cache 조회/삭제 API | PASS | PASS |
| 한글/공백 파일명 | PASS | PASS |
| pytest test_ppt_parser/cache/analysis | 33 passed | PASS |
| pytest 전체 | 122 passed | PASS |

### 문제

1. `Presentation` import 오류
2. Blank layout fixture title None

### 원인

1. `from pptx import Presentation` 필요
2. layout 6에 title placeholder 없음

### 수정

1. import 수정
2. Title and Content layout 사용

### 재테스트

PASS

### Group Shape

python-pptx Public API로 Group 생성 제한 — Mock Unit Test로 재귀 추출 검증.
