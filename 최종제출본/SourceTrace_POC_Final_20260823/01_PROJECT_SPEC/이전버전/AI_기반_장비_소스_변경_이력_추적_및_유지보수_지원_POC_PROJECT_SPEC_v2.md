# AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC 개발 작업지시서

## 1. 프로젝트 개요

### 1.1 프로젝트 제목

**AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC**

### 1.2 프로젝트 목적

본 POC는 개발자가 VSCode에서 소스코드를 확인하거나 유지보수 작업을 수행하는 중 특정 코드, 함수, Symbol 또는 변경 내용의 변경 시점과 변경 사유를 질문하면 다음 근거를 자동으로 추적하여 답변하는 시스템을 개발하는 것을 목적으로 한다.

- 장비별 Git 소스 변경 이력 확인
- 특정 코드, 함수, Symbol이 변경된 Commit 탐색
- 변경 전/후 Diff 확인
- Git Commit의 날짜, 메시지, 파일 변경 정보를 이용한 관련 변경내역서 후보 탐색
- 필요한 PPT 변경내역서만 On-demand 방식으로 분석
- 분석한 PPT 결과를 Cache하여 반복 Parsing 최소화
- Git 변경 이력과 PPT Slide 근거 연계
- 내부 Ollama를 이용한 근거 기반 변경 사유 분석
- VSCode Continue에서 자연어 질문을 통해 변경 이력 및 변경 사유 조회
- AI 답변에 Git Commit 및 변경내역서 근거 표시

본 POC의 핵심 사용자 경험은 다음과 같다.

```text
VSCode Continue

개발자:
"CalcFare 함수가 왜 변경됐어?"

        ↓

현재 질문 / 파일 / 코드 정보

        ↓

Change Trace Backend

        ↓

Git 변경 이력 검색

        ↓

Commit / Diff / 날짜 / 파일 / Keyword 추출

        ↓

관련 PPT 후보 탐색

        ↓

필요한 PPT만 On-demand 분석

        ↓

Git ↔ PPT 근거 연계

        ↓

Ollama 근거 기반 분석

        ↓

Continue 답변
```

예상 응답:

```text
CalcFare 함수는 어린이 카드가 일반 카드로 판단되어
일반 요금이 적용되는 문제를 수정하기 위해 변경되었습니다.

변경 Commit
a82bc93

변경 파일
src/fare/FareCalc.c

관련 변경내역서
20240315_AG_변경내역.pptx
Slide 7
```

### 1.3 핵심 방향

본 POC는 Git/PPT 통합 웹 검색 시스템 자체를 최종 목표로 하지 않는다.

웹 UI는 다음 목적으로 사용한다.

```text
장비 설정
Git 동기화
Git 변경 이력 검증
PPT Cache 상태 확인
분석 결과 검증
운영 및 장애 확인
```

실제 주요 사용자 인터페이스는 VSCode Continue를 목표로 한다.

```text
주 사용 인터페이스
VSCode Continue

보조 인터페이스
Web 관리 / 검증 UI
```

---

## 2. 중요 개발 원칙

본 POC는 인터넷이 가능한 개발 PC에서 Cursor를 이용하여 개발하지만 최종 운영 환경은 인터넷이 차단된 내부망이다.

환경은 다음과 같이 구분한다.

```text
개발 PC
- 인터넷 가능
- Cursor 사용
- 기능 개발
- 자동 테스트

        ↓

내부 테스트 환경
- 인터넷 차단
- VSCode 사용 가능
- Continue 사용 가능
- Ollama 사용 가능

        ↓

설치 서버 PC
- FastAPI Backend
- SQLite
- Git Analyzer
- PPT On-demand Parser
- Cache
- Ollama Client

        ↓

운영 PC
- VSCode
- Continue
- Browser 관리 화면
```

### 필수 원칙

1. 인터넷 연결 없이 실행 가능해야 한다.
2. 외부 Cloud AI API를 사용하지 않는다.
3. 외부 CDN을 사용하지 않는다.
4. 실행 시 npm 또는 pip Package를 자동 다운로드하지 않는다.
5. Python 및 Node 의존성 버전을 명확하게 관리한다.
6. 장비별 Git 경로와 변경내역서 경로를 코드에 하드코딩하지 않는다.
7. 장비 경로는 Backend 서버에서 접근 가능한 경로를 기준으로 한다.
8. 서버 로컬 경로를 기본 지원한다.
9. UNC 네트워크 경로는 서버 실행 계정의 접근 권한 및 Git 동작 여부에 따라 사용할 수 있으며 실제 운영 환경에서 별도 검증한다.
10. Windows 환경을 기본 실행 환경으로 한다.
11. 각 STEP 완료 후 독립적인 테스트가 가능해야 한다.
12. 기능 구현과 테스트 절차를 함께 관리한다.
13. Ollama 장애 시 Git 및 근거 검색 기능은 계속 동작해야 한다.
14. AI가 근거에 없는 변경 사유를 사실처럼 생성하지 않도록 한다.
15. Git Repository 전체 또는 모든 PPT 전체 내용을 LLM Prompt에 전달하지 않는다.
16. PPT는 전체 사전 Parsing을 기본 정책으로 하지 않는다.
17. 필요한 PPT만 분석하고 분석 결과를 Cache한다.
18. Cache는 원본 데이터가 아니라 재생성 가능한 검색 보조 데이터로 취급한다.

---

# 3. 권장 기술 구성

## Frontend

```text
React
TypeScript
Vite
```

## Backend

```text
Python
FastAPI
```

## Database / Cache

```text
SQLite
```

## Git 분석

```text
Git CLI
Python subprocess
```

## PPT 분석

```text
python-pptx
```

## AI

```text
Ollama REST API
```

## Continue 연계

우선 Continue에서 사용할 수 있는 Tool 연계 방식을 검토한다.

최종 방식은 실제 내부 Continue 버전과 설정 가능 범위를 확인하여 결정한다.

우선순위:

```text
1. MCP 연계 가능 여부 확인
2. Continue Tool / Context Provider 연계 가능 여부 확인
3. Local HTTP API 호출 방식 검토
```

특정 연계 방식을 사전에 확정하여 코드 전체를 종속시키지 않는다.

Backend의 핵심 기능은 Continue 연계 방식과 분리된 HTTP Service API로 구현한다.

---

# 4. 전체 시스템 구조

```text
┌─────────────────────────────────┐
│ VSCode Continue                 │
│                                 │
│ "이 코드가 왜 변경됐어?"        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Change Trace Integration Layer  │
│ MCP / Continue Tool             │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ FastAPI Backend                 │
│                                 │
│ Trace API                       │
│ Git Search Service              │
│ PPT Candidate Service           │
│ PPT On-demand Parser            │
│ Evidence Link Service           │
│ Ollama Analysis Service         │
└───────┬─────────┬───────────────┘
        │         │
        ▼         ▼
┌────────────┐  ┌─────────────────┐
│ Git Repos  │  │ PPT Documents   │
└─────┬──────┘  └────────┬────────┘
      │                  │
      ▼                  ▼
┌─────────────────────────────────┐
│ SQLite                          │
│                                 │
│ equipment                       │
│ git_commit                      │
│ git_change                      │
│ document_cache                  │
│ slide_cache                     │
│ change_link                     │
│ trace_request(optional)         │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Internal Ollama                 │
└─────────────────────────────────┘
```

### 데이터 처리 원칙

```text
Git
→ 사전 동기화 및 DB 인덱싱

PPT
→ 질문 시 후보 탐색
→ 필요한 PPT만 Parsing
→ Parsing 결과 Cache

Ollama
→ 검색 및 근거 연계 완료 후 상위 근거만 전달
```

---

# 5. SQLite 역할

SQLite는 원본 Git 또는 PPT를 대체하지 않는다.

원본:

```text
Git Repository
PPTX 변경내역서
```

SQLite:

```text
장비 설정
Git 검색 인덱스
PPT 분석 Cache
Git-PPT 연계 결과
```

PPT Cache는 삭제하더라도 원본 PPT에서 다시 생성 가능해야 한다.

---

# 6. 프로젝트 디렉터리 구조

다음 구조를 기본으로 한다.

```text
equipment-change-trace/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── equipment.py
│   │   │   ├── git_history.py
│   │   │   ├── trace.py
│   │   │   ├── documents.py
│   │   │   └── analysis.py
│   │   │
│   │   ├── services/
│   │   │   ├── git_service.py
│   │   │   ├── git_history_service.py
│   │   │   ├── trace_service.py
│   │   │   ├── ppt_candidate_service.py
│   │   │   ├── ppt_cache_service.py
│   │   │   ├── ppt_parser_service.py
│   │   │   ├── link_service.py
│   │   │   └── ollama_service.py
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   │
│   │   └── db/
│   │       ├── database.py
│   │       └── migrations.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── requirements-lock.txt
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
│
├── integration/
│   └── continue/
│
├── scripts/
│   ├── start-dev.bat
│   ├── start-server.bat
│   ├── check-environment.bat
│   ├── test-backend.bat
│   └── build-frontend.bat
│
├── data/
├── logs/
├── deploy/
├── tests/
│   └── test-data/
│
├── PROJECT_SPEC.md
├── TEST_PLAN.md
├── DEPLOYMENT.md
└── README.md
```

기능 증가에 따라 구조를 변경할 수 있으나 과도한 추상화와 Microservice 구조는 사용하지 않는다.

---

# 7. 환경 설정 원칙

환경별 설정은 소스코드와 분리한다.

예:

```env
APP_HOST=0.0.0.0
APP_PORT=8010

DATABASE_PATH=./data/equipment_change_trace.db

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:9b

PPT_CANDIDATE_DATE_RANGE_DAYS=90
PPT_CANDIDATE_LIMIT=30
PPT_PARSE_LIMIT=10

LOG_LEVEL=INFO
```

장비별 다음 정보는 DB에서 관리한다.

```text
장비명
Git Repository 경로
변경내역서 폴더
```

---

# 8. 개발 단계별 작업 원칙

모든 STEP은 다음 순서로 진행한다.

```text
명세 확인
↓
STEP 범위 구현
↓
자동 테스트
↓
Frontend Build
↓
문제 수정
↓
테스트 결과 기록
↓
다음 STEP 진행
```

Cursor는 한 번에 전체 시스템을 구현하지 않는다.

---

# STEP 0. 프로젝트 기본 실행 환경 구축

## 상태

**완료**

## 구현 목표

Frontend와 Backend 기본 실행 환경을 구축하고 Health 상태를 확인한다.

## 핵심 완료 항목

```text
FastAPI Application
SQLite 초기화
GET /api/health
React + TypeScript + Vite
환경 확인 Script
개발 실행 Script
Logging
Offline 실행 고려
```

## 완료 기준

- Backend 실행 가능
- Frontend 실행 가능
- Health API 정상
- Git 상태 확인
- Ollama 상태 확인
- Ollama 장애가 Application 실행을 막지 않음

---

# STEP 1. 장비 관리

## 상태

**완료**

## 구현 목표

장비별 Git Repository 및 변경내역서 경로를 관리한다.

## 완료 데이터 모델

```text
equipment

id
name
document_path
created_at
updated_at
(git_path — Deprecated, Migration 호환용 Column 유지)

git_repository

id
equipment_id
name
source_type          # remote | local
repository_url       # 사용자 입력 URL (Password 제외, Username 표시용)
canonical_repository_url
yona_username
local_path
status               # pending | ready | error
created_at
updated_at

UNIQUE (equipment_id, name)
동일 장비 Remote canonical_repository_url 중복 등록 방지 (애플리케이션 정책)
```

## Yona Git URL 정책

```text
사용자 UX: Yona 화면의 Git URL을 그대로 입력 (별도 Username 필드 없음)
예: http://ds_yoo@192.168.155.89:9000/13.hhd200/hhd200_card

Backend: urllib.parse 기반 URL 분석 (문자열 split 금지)
  canonical_repository_url — userinfo 제거 Repository Identity
  yona_username — URL userinfo에서 추출한 사용자 Context

동일 canonical URL + 다른 Username → 동일 Repository Identity
Username만 변경 시 git_commit/git_change 유지, origin URL Context만 갱신

서버 Git 접근: YONA_DEFAULT_USERNAME (필수, 예: source_trace)
  사용자 입력 URL Username은 무시 — canonical URL + Default Username으로 Access
Password/Token SQLite·URL 평문 저장 금지 → Git Credential Manager (manager)
GIT_TERMINAL_PROMPT=0 비대화형 실행
```

## document_path 경로 정책 (POC 운영)

```text
document_path는 UNC 네트워크 공유 경로만 허용 (Backend 실행 계정 Read 접근)
비허용: D:\... Local Drive, 운영 PC Browser Local Folder

예: \\192.168.155.90\ChangeDocuments\HHD200

UI: UNC 직접 입력 + [경로 확인] (Web Folder Browser 미사용)

검증: UNC 형식 + 존재 + Directory + Read + 재귀 PPTX Count ([경로 확인] 시)
장비 저장 시: 기본 UNC 검증만 수행 (재귀 PPTX Count 생략)
```

## Yona Git Access 정책

```text
Username 정책: URL userinfo Username 무시 → YONA_DEFAULT_USERNAME만 사용 (필수, Fallback 금지)
Repository Identity: canonical URL (Username 유무 무관)
DB/UI repository_url: canonical URL만 저장·표시 (userinfo 미포함)
Clone: Repository 최초 Prepare 시 1회만. 장비 저장 시 기존 ready Repository 재-Clone/Prepare 금지
기존 Repository Git 갱신: Git Sync(fetch)만 사용
Password: DB/SQLite/.env 평문 저장 금지
초기 설정: scripts/setup-yona-credential.ps1 → Git Credential Manager (manager)
GIT_TERMINAL_PROMPT=0 (모든 Git subprocess)
```

## 완료 기능

```text
장비 CRUD (name, document_path)
Git Repository CRUD (장비당 1:N, 장비 추가 화면에서도 Repository 등록 가능)
장비명 UNIQUE
Remote URL 검증 (git ls-remote)
Local 경로 검증 (git rev-parse)
Document 경로 검증 (하위 폴더 포함 PPTX 재귀 Count — [경로 확인], 장시간 Loading Panel + 경과 시간)
UNC 직접 입력 UI (Folder Browser 미구현)
장비 저장 / Repository Create(Metadata) / Repository Prepare(Clone) 분리 UX (Repository별 준비 상태 표시)
장비 수정: 기존 ready Repository 변경 없음 → Git 명령 0회. 신규 Repository만 Create → Prepare
장시간 작업 Loading Panel + 경과 시간 (Git 동기화, 이력 검색, PPT 분석)
Tab 이동 시 Search/Analysis State 유지, 복귀 시 자동 재조회/완료 알림 재표시 금지 (Browser Refresh 후 복구 미지원)
```

## Git 검증

**Local:**

```text
git -C "{local_path}" rev-parse --is-inside-work-tree
```

**Remote (Yona):**

```text
사용자 입력 URL → canonical URL 파싱 후 검증
git ls-remote <git_access_url>
git_access_url = canonical URL + YONA_DEFAULT_USERNAME (사용자 Username Fallback 금지)
GIT_TERMINAL_PROMPT=0
Repository Create: Git 명령 0회 (Metadata, status=pending)
Repository Prepare: git clone (ls-remote 선행 강제 없음)
```

Python subprocess는 Argument List 방식을 사용한다. Remote URL 전체·Credential은 INFO 로그/API Response에 노출하지 않으며 Password/Token은 Mask한다.

## 경로 정책

장비 경로는 Backend 서버에서 접근 가능한 경로를 기준으로 한다.

서버 로컬 경로를 기본 지원한다.

UNC 네트워크 경로는 서버 실행 계정의 접근 권한 및 Git 동작 여부에 따라 사용할 수 있으며 실제 운영 환경에서 별도 검증한다.

---

# STEP 2. Git 변경 이력 수집

## 상태

**완료**

## 완료 데이터 모델

### git_commit

```text
id
repository_id
commit_hash
commit_date
author
message
parent_hash
```

제약:

```text
repository_id + commit_hash UNIQUE
```

### git_change

```text
id
commit_id
file_path
change_type
additions
deletions
diff
```

### git_repository Sync

```text
Remote: 최초 git clone → data/repositories/{equipment_id}/{repository_id}
        이후 git fetch --all --prune → git log --all
Local:  Local Working Tree 분석 (자동 pull 없음)
```

## 완료 기능

```text
POST /api/equipment/{id}/sync/git        (장비 전체 Repository)
POST /api/repositories/{id}/sync         (단일 Repository)
git log --all 기반 Commit 탐색
신규 Commit만 저장
파일 단위 Diff 저장
Binary 파일 처리
Rename 처리
equipment / repository 삭제 시 Git 데이터 CASCADE
```

## 증분 정책

```text
git log --all
↓
Commit Hash 목록
↓
DB 존재 여부 확인
↓
기존 Commit Skip
↓
신규 Commit 상세 분석
```

단순 마지막 Commit 이후 조회 방식은 사용하지 않는다.

## 현재 제한

Merge Commit은 첫 번째 Parent Hash만 저장한다.

---

# STEP 3. Git 변경 이력 조회

## 상태

**완료**

## 완료 API

```text
GET /api/equipment/{equipment_id}/git/commits
GET /api/git/commits/{commit_id}
```

Commit 상세 API는 DB `commit_id`를 사용한다.

Commit Hash는 시스템 전체 UNIQUE라고 가정하지 않는다.

## 완료 기능

```text
통합 검색
기간 Filter
파일 Filter
작성자 Filter
Pagination
Commit 목록
Commit 상세
변경 파일 선택
파일별 Diff 표시
Git 동기화 UI
```

## 검색 대상

```text
Commit Message
Commit Hash
Author
File Path
Diff
```

## 현재 제한

현재 검색은 LIKE 기반이다.

FTS5는 실제 검색 데이터 규모와 STEP 7 요구사항을 확인한 후 도입 여부를 판단한다.

---

# STEP 4. 변경 추적 요청 API 및 Trace 흐름 구축

## 목표

Continue 연계 이전에 Backend 단독으로 "변경 이유 추적 요청"을 받을 수 있는 핵심 Trace API를 구현한다.

이 STEP에서는 PPT를 Parsing하지 않는다.

Git 데이터를 이용하여 질문과 관련된 Commit 후보를 찾고 이후 PPT 탐색에 필요한 Search Context를 생성한다.

## 핵심 API

```http
POST /api/trace/search
```

요청 예:

```json
{
  "equipment_id": 1,
  "query": "CalcFare 함수가 왜 변경됐어?",
  "file_path": "src/fare/FareCalc.c",
  "selected_code": "if (cardType == TYPE_CHILD) { ... }"
}
```

`file_path`와 `selected_code`는 Optional이다.

Continue에서 현재 파일 또는 선택 코드 정보를 전달할 수 있을 때 사용한다.

응답 예:

```json
{
  "equipment_id": 1,
  "query": "CalcFare 함수가 왜 변경됐어?",
  "git_candidates": [
    {
      "commit_id": 15,
      "commit_hash": "a82bc93...",
      "commit_date": "2024-03-15T14:21:32",
      "message": "어린이 카드 요금 처리 추가",
      "file_path": "src/fare/FareCalc.c",
      "score": 92,
      "match_reasons": [
        "query_keyword",
        "file_path",
        "diff_symbol"
      ]
    }
  ],
  "search_context": {
    "keywords": [
      "CalcFare",
      "FareCalc.c",
      "TYPE_CHILD",
      "CHILD_FARE"
    ],
    "date_from": "2023-12-16",
    "date_to": "2024-06-13"
  }
}
```

## Git Candidate 검색

검색 근거:

```text
사용자 query
현재 file_path
selected_code
Commit Message
git_change.file_path
git_change.diff
```

초기 Candidate Score 예:

```text
현재 파일 일치          30
검색 Symbol 일치         25
Commit Message Keyword  20
Diff Keyword            20
날짜/기타 Context         5
```

점수 기준은 설정 객체 또는 한 곳의 상수로 관리한다.

## Keyword 추출

LLM을 사용하지 않는다.

초기에는 규칙 기반으로 추출한다.

보존 대상:

```text
함수명
대문자 Symbol
파일명
영문 Identifier
한글 핵심 검색어
```

예:

```text
CalcFare
CHILD_FARE
TYPE_CHILD
FareCalc.c
어린이
요금
```

C/C++ Identifier 형태를 우선 고려한다.

과도한 자연어 NLP 처리를 하지 않는다.

## Search Context 생성

상위 Git Candidate에서 다음 정보를 수집하여 PPT 후보 검색 Context를 만든다.

```text
Commit Date 범위
변경 파일명
Commit Message Keyword
Diff Symbol
함수명
사용자 Query Keyword
```

## 테스트

다음 질문을 테스트한다.

```text
CHILD_FARE가 왜 추가됐어?
CalcFare 함수 변경 이유
어린이 카드 요금 변경
```

검증:

```text
관련 Commit이 Top 5 안에 포함
검색 Context에 핵심 Symbol 포함
현재 file_path가 제공되면 해당 파일 Candidate 우선
selected_code가 제공되면 Symbol 추출
```

## 완료 조건

- PPT 없이 Git Candidate 생성 가능
- Ollama 없이 동작
- Trace Search Context 생성 가능
- Candidate Score 근거 확인 가능

---

# STEP 5. Git 기반 PPT 후보 탐색

## 목표

모든 PPT를 Parsing하지 않고 파일 경로와 Git Search Context를 이용하여 관련 가능성이 높은 PPT 파일 후보를 탐색한다.

이 STEP에서는 PPT 내부 Text를 아직 전체 분석하지 않는다.

## 후보 탐색 대상

```text
equipment.document_path
```

하위 폴더까지 재귀 탐색한다.

지원:

```text
.pptx
```

제외:

```text
.ppt
~$*.pptx
```

## Candidate 정보

```text
file_path
file_name
modified_at
file_size
candidate_score
match_reasons
```

## 초기 후보 점수

```text
파일명 날짜 근접도       35
파일 modified_at 근접도  10
파일명 Keyword          30
폴더명 Keyword          15
장비 Context             10
```

중요:

파일 modified_at은 문서 변경일과 동일하다고 가정하지 않는다.

날짜 문자열이 파일명 또는 폴더명에 존재하는 경우 우선 활용한다.

지원할 날짜 형식 예:

```text
20240315
2024-03-15
2024_03_15
2024.03.15
```

날짜 Parse 실패는 오류가 아니다.

## Candidate 범위

기본 예:

```text
Git Commit Date ± 90일
```

설정 가능하게 한다.

날짜 기반 후보가 너무 적거나 없는 경우 Keyword 기반 후보를 추가한다.

전체 PPT를 무조건 반환하지 않는다.

기본 Candidate 최대 개수:

```text
30
```

설정 가능하게 한다.

## API

Trace API 내부 Service로 사용하거나 다음 Debug API를 허용한다.

```http
POST /api/trace/ppt-candidates
```

웹 UI에서는 개발 및 운영 검증 목적으로 후보 목록을 확인할 수 있어도 된다.

## 테스트

다음 구조를 준비한다.

```text
documents/
├── 2024/
│   ├── 20240315_AG_변경내역.pptx
│   ├── 20240501_AG_변경내역.pptx
│   └── 20241220_AG_변경내역.pptx
├── 요금/
│   └── 어린이카드_변경.pptx
└── 기타/
    └── 화면문구변경.pptx
```

검증:

```text
2024-03-15 Commit → 20240315 문서 상위 후보
"어린이 카드" → 어린이카드 문서 후보
무관 문서는 낮은 점수
후보 개수 제한 적용
```

## 완료 조건

- PPT 내부 Parsing 없이 후보 파일 선정
- 날짜 및 Keyword 근거 표시
- 하위 폴더 재귀 탐색
- 후보 Limit 적용

---

# STEP 6. PPT On-demand 분석 및 Cache

## 목표

STEP 5에서 선정된 상위 PPT 후보만 Parsing한다.

Parsing한 Slide Text는 Cache에 저장하여 동일 파일을 반복 분석하지 않는다.

## 데이터 모델

### document_cache

```text
id
equipment_id
file_path
file_name
file_hash
modified_at
parsed_at
slide_count
```

제약:

```text
equipment_id + file_path UNIQUE
```

### slide_cache

```text
id
document_cache_id
slide_number
title
content
```

제약:

```text
document_cache_id + slide_number UNIQUE
```

## Cache 원칙

```text
Cache 없음
→ PPT Parse
→ Cache 저장

Cache 있음 + Hash 동일
→ Cache 사용
→ PPT 재Parsing 없음

Cache 있음 + Hash 변경
→ PPT 재Parsing
→ Parsing 성공 후 Cache 교체

Parsing 실패
→ 기존 정상 Cache 유지
```

Cache는 원본 문서가 아니다.

Cache 삭제 후 다시 분석할 수 있어야 한다.

## PPT Parsing 범위

최소 지원:

```text
TextBox
Placeholder
Table Cell
Group Shape 내부 Text
```

Group Shape는 재귀 처리한다.

추출 순서:

```text
1. Group Shape
2. Table
3. Text Frame
```

중복 Text 추출에 주의한다.

## Table 저장 형식

권장:

```text
장비명 | AG
변경일 | 2024-03-15
변경내용 | 어린이 카드 요금 오류 수정
```

각 Row는 줄바꿈, Cell은 ` | `로 구분한다.

## Slide title

순서:

```text
1. Title Placeholder
2. 첫 번째 의미 있는 Text의 첫 줄
3. 없음
```

Fallback title은 최대 200자.

## 빈 Slide

모든 Slide를 저장한다.

```text
slide_number = 실제 PowerPoint 번호
```

1부터 시작한다.

Text 없는 Slide도 저장한다.

## Hash

SHA-256을 Chunk 방식으로 계산한다.

modified_at만으로 Cache 유효성을 판단하지 않는다.

## On-demand Parse Limit

한 Trace 요청에서 모든 Candidate PPT를 Parsing하지 않는다.

예:

```text
PPT 후보 30개
↓
상위 10개 Parse
```

`PPT_PARSE_LIMIT` 설정을 사용한다.

## API / Trace 연계

Trace 흐름:

```text
Git Candidate
↓
PPT File Candidate
↓
상위 PPT Parse / Cache 조회
↓
Slide Search Candidate 생성
```

## Slide Candidate 검색

Parsing된 Slide에서 다음 정보를 검색한다.

```text
title
content
file_name
```

검색 기준:

```text
Git Keyword
Commit Message Keyword
Diff Symbol
파일명
사용자 Query
```

## 관리 / 검증 UI

기존 Web UI에 최소한 다음 기능을 추가할 수 있다.

```text
PPT Cache 목록
Cache된 문서
Slide 수
Hash
Parsing 시간
Cache 상세 Slide Text 확인
Cache 삭제
```

이 화면은 운영 검증용이다.

전체 변경내역서를 미리 동기화하는 버튼을 만들지 않는다.

## OCR

이번 STEP에서는 구현하지 않는다.

이미지 내부 Text는 추출하지 않는다.

## SmartArt / Chart

python-pptx Public API 범위에서 추출 가능한 Text만 처리한다.

XML 직접 Parsing은 하지 않는다.

## 테스트

- Cache 없는 PPT 최초 Parsing
- 동일 Hash Cache 재사용
- PPT 변경 후 재Parsing
- Parsing 실패 시 기존 Cache 유지
- 한글 Text
- CHILD_FARE 유지
- CalcFare 유지
- Table Text
- Group Shape Text
- Title Placeholder
- Fallback Title
- 빈 Slide 번호 유지
- 한글/공백 파일명
- Parse Limit
- 두 장비 Cache 분리
- equipment 삭제 시 Cache CASCADE

## 완료 조건

- 상위 후보 PPT만 Parsing
- Hash 기반 Cache
- 기존 Cache 안전성
- Slide 단위 Text 저장
- 실제 Slide 번호 유지

---

# STEP 7. Git-PPT 근거 연계

## 목표

Git 변경 Candidate와 On-demand 분석된 PPT Slide Candidate의 관련성을 계산한다.

AI를 사용하기 전에 규칙 기반 연계 결과를 생성한다.

## 데이터 모델

### change_link

```text
id
git_change_id
slide_cache_id
score
link_reason
created_at
```

Cache 재생성으로 slide_cache ID가 변경될 수 있으므로 FK 및 Cache 갱신 정책을 명확히 처리한다.

POC 단계에서는 Cache 문서 갱신 시 관련 change_link를 삭제하고 필요 시 재생성하는 단순 정책을 우선 검토한다.

## 초기 연계 점수

```text
날짜 근접도            25
파일명 일치            20
Commit Message Keyword 20
Diff Symbol 일치       20
사용자 Query Keyword   10
함수명 / Identifier     5
```

점수는 한 곳에서 관리한다.

## link_reason

예:

```json
{
  "date_score": 25,
  "file_score": 20,
  "message_score": 18,
  "diff_symbol_score": 20,
  "query_score": 10,
  "identifier_score": 5
}
```

## Trace 결과

```json
{
  "git_evidence": [...],
  "document_evidence": [
    {
      "file_name": "20240315_AG_변경내역.pptx",
      "slide_number": 7,
      "score": 94,
      "match_reasons": [...]
    }
  ]
}
```

## 테스트 정답 Set

실제 운영환경 테스트 전에는 테스트 데이터 Pair를 사용한다.

운영환경에서는 실제 변경 건 10~20개를 직접 선정하여 정답 Set을 만든다.

평가:

```text
Top 1 성공률
Top 3 성공률
Top 5 성공률
```

목표:

```text
Top 5 내 정답 포함 80% 이상
```

단, 테스트 건수를 함께 표시한다.

예:

```text
8 / 10
80%
```

## 완료 조건

- Git ↔ PPT Slide 규칙 기반 연계
- Score 근거 확인
- Top N 결과 생성
- 실제 운영 데이터 조정 가능 구조

---

# STEP 8. Ollama 근거 기반 변경 사유 분석

## 목표

Git 및 PPT 근거 연계가 완료된 후 내부 Ollama를 이용하여 변경 사유를 요약한다.

## 중요 원칙

다음 순서를 반드시 지킨다.

```text
사용자 질문
↓
Git Search
↓
PPT 후보 탐색
↓
On-demand Parse / Cache
↓
Git-PPT Link
↓
상위 Evidence 선정
↓
Ollama
```

다음 구조를 사용하지 않는다.

```text
전체 Git
+
전체 PPT
↓
LLM
```

## Ollama Context

예:

```text
[사용자 질문]

CalcFare 함수가 왜 변경됐어?


[Git 근거 1]

Commit:
a82bc93

Date:
2024-03-15

File:
src/fare/FareCalc.c

Message:
어린이 카드 요금 처리 추가

Diff:
- fare = DEFAULT_FARE;
+ fare = CHILD_FARE;


[변경내역서 근거 1]

File:
20240315_AG_변경내역.pptx

Slide:
7

Content:
특정 어린이 카드 사용 시 일반 요금이 적용되는 문제 확인
카드 종류 판단 조건 수정
```

## System Prompt 원칙

```text
제공된 근거만 사용한다.

근거에 없는 변경 이유를 사실처럼 생성하지 않는다.

Git 변경 사실과 문서에 명시된 사유를 구분한다.

추론이 필요한 경우 "추정"이라고 표시한다.

변경 사유를 확인할 수 없으면 확인 불가라고 답한다.

Commit Hash와 변경내역서 File / Slide를 Evidence로 반환한다.
```

## 응답 구조

JSON 응답을 우선 사용한다.

```json
{
  "summary": "어린이 카드 요금 처리 오류를 수정하기 위한 변경입니다.",
  "reason": "어린이 카드가 일반 요금으로 처리되는 문제",
  "confidence": "high",
  "inference": false,
  "evidence": [
    {
      "type": "git",
      "commit": "a82bc93"
    },
    {
      "type": "document",
      "file": "20240315_AG_변경내역.pptx",
      "slide": 7
    }
  ]
}
```

## JSON Parsing 실패

```text
JSON Parse 실패
↓
Raw Response 별도 처리
↓
분석 형식 오류 표시
```

전체 Trace API를 500 Error로 만들지 않는다.

## Ollama 장애

```text
AI 분석 사용 불가

Git Evidence 정상
PPT Evidence 정상
```

근거 조회 결과는 반환한다.

## 테스트

- 정상 근거 기반 요약
- PPT 근거 없는 경우
- Git 근거만 있는 경우
- 근거 없는 변경 사유 생성 억제
- JSON 외 Text 포함 응답
- Ollama Timeout
- Ollama 중단
- 한글 답변
- Evidence 누락 감지

## 완료 조건

- 근거 기반 분석
- AI 장애와 검색 기능 분리
- Evidence 표시
- 추정 여부 표시

---

# STEP 9. VSCode Continue 연계

## 목표

개발자가 VSCode Continue에서 자연어로 변경 이력과 변경 사유를 질문할 수 있도록 한다.

## 사전 확인

내부 운영 환경의 다음 정보를 실제로 확인한다.

```text
VSCode Version
Continue Version
Continue 설정 방식
MCP 지원 여부
Custom Tool 지원 여부
Context Provider 지원 여부
Local HTTP 접근 가능 여부
```

이 결과를 문서에 기록한다.

현재 Continue 기능을 추정하여 연계 방식을 임의 확정하지 않는다.

## 연계 우선순위

### Option 1

```text
MCP
```

실제 설치된 Continue 버전에서 안정적으로 지원되는 경우 우선 검토한다.

### Option 2

```text
Continue Custom Tool / Context Provider
```

내부 Continue 설정으로 Local Backend를 호출할 수 있는 경우 사용한다.

### Option 3

```text
Local Wrapper / HTTP Integration
```

필요 시 최소 Wrapper를 사용한다.

## Backend 핵심 API

Continue Integration Layer는 다음 API를 호출한다.

```http
POST /api/trace/analyze
```

요청:

```json
{
  "equipment_id": 1,
  "query": "이 코드가 왜 변경됐어?",
  "file_path": "src/fare/FareCalc.c",
  "selected_code": "fare = CHILD_FARE;"
}
```

응답:

```json
{
  "answer": "...",
  "confidence": "high",
  "inference": false,
  "git_evidence": [...],
  "document_evidence": [...]
}
```

## 현재 코드 Context

가능한 경우 Continue에서 다음 정보를 전달한다.

```text
현재 Workspace
현재 파일 경로
선택 코드
사용자 질문
```

장비 자동 선택은 별도 정책으로 구현한다.

초기 POC에서는 명시적 equipment_id 선택을 허용한다.

이후 Repository Path와 현재 Workspace Path를 비교하여 장비를 자동 추론할 수 있다.

## 장비 자동 매칭

선택적 확장:

```text
현재 Workspace Path
↓
equipment.git_path 비교
↓
가장 근접한 Repository
↓
equipment 자동 선택
```

자동 매칭 실패 시 장비를 임의 선택하지 않는다.

## Continue 답변 형식

예:

```text
CalcFare 변경 사유

어린이 카드가 일반 카드로 판단되어 일반 요금이 적용되는
문제를 수정하기 위해 변경된 것으로 확인됩니다.

Git 근거
- a82bc93
- src/fare/FareCalc.c
- 2024-03-15

변경내역서 근거
- 20240315_AG_변경내역.pptx
- Slide 7
```

근거가 부족한 경우:

```text
해당 코드의 변경 Commit은 확인했지만
관련 변경내역서를 찾지 못해 변경 사유는 확인할 수 없습니다.

Git 근거
- ...
```

## 테스트 질문

```text
이 코드가 왜 변경됐어?
CHILD_FARE가 언제 추가됐어?
CalcFare 함수 변경 이유 찾아줘
어린이 카드 요금 관련 변경 이력 알려줘
```

## 완료 조건

- Continue에서 자연어 질문 가능
- 현재 코드 Context 전달 가능 여부 검증
- Trace Backend 호출
- 근거 기반 답변 표시
- 내부망에서 외부 연결 없음

---

# STEP 10. 운영환경 배포 및 단계별 검증

## 목표

인터넷이 차단된 내부 서버와 운영 PC에서 실제 사용 가능하도록 배포한다.

## 배포 구조

```text
운영 PC
VSCode + Continue
Browser
       │
       ▼
서버 PC
FastAPI
SQLite
Git CLI
PPT Parser
Ollama Client
       │
       ├── Git Repository
       ├── PPT 변경내역 폴더
       └── Internal Ollama
```

## Frontend

개발 PC에서 Build한다.

```bash
npm run build
```

Node는 서버 Runtime 필수 항목으로 만들지 않는다.

## Python Offline Package

인터넷 가능 PC:

```bash
pip download -r requirements-lock.txt -d offline_packages/python
```

내부망:

```bash
pip install --no-index --find-links=offline_packages/python -r requirements-lock.txt
```

## 배포 폴더

```text
equipment-change-trace-deploy/
│
├── app/
├── frontend/
│   └── dist/
├── data/
├── logs/
├── integration/
│   └── continue/
├── scripts/
│   ├── start-server.bat
│   └── check-environment.bat
├── offline_packages/
│   └── python/
├── requirements-lock.txt
├── config.example.env
├── OFFLINE_INSTALL.md
└── DEPLOYMENT_TEST.md
```

---

# 9. 운영환경 테스트 시점

## 1차 운영환경 테스트

**STEP 6 완료 후 수행**

이전 명세의 전체 PPT 사전 동기화 방식은 사용하지 않는다.

1차 테스트 목적:

```text
실제 Git Repository 동기화
Git 검색 결과 확인
실제 PPT 폴더 후보 탐색
실제 PPT On-demand Parsing
Cache 결과 확인
```

검증 항목:

```text
인터넷 없는 서버 실행
운영 PC Browser 접속
실제 장비 등록
Git 경로 접근
PPT 경로 접근
Git 동기화
한글 Commit Message
Diff 표시
PPT 후보 선정
PPT 일부만 Parsing되는지
Slide Text 추출
Table Text
Group Shape Text
한글 Text
빈 Slide 번호
이미지 중심 Slide 비율
SmartArt / Chart 미추출 영향
Cache 재사용
```

중요:

실제 PPT가 이미지 중심인지 반드시 확인한다.

이미지로 작성된 변경내역 비율이 높으면 OCR 필요성을 STEP 7 이전에 재검토한다.

## 2차 운영환경 테스트

**STEP 7 완료 후 수행**

실제 Git-PPT Pair 10~20개를 선정한다.

```text
Commit
실제 관련 PPT
실제 Slide
```

정답 Set을 만든다.

평가:

```text
Top 1
Top 3
Top 5
```

점수 가중치는 실제 데이터 결과를 기준으로 조정한다.

## 3차 운영환경 테스트

**STEP 8 완료 후 수행**

내부 Ollama 확인:

```text
API 주소
Model 이름
응답 시간
한글 품질
JSON 안정성
근거 없는 추론 여부
Context 길이
Timeout
```

## 4차 운영환경 테스트

**STEP 9 완료 후 수행**

Continue 실제 사용 시나리오 테스트:

```text
현재 코드 선택
질문
Backend 호출
Git 추적
PPT 탐색
Cache
Ollama
Continue 답변
Evidence 확인
```

---

# 10. 테스트 결과 기록

각 STEP 완료 시 `TEST_PLAN.md`에 결과를 기록한다.

형식:

```markdown
## STEP 6 PPT On-demand Cache

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

TEST_DEVICE_A

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 최초 Parsing | Cache 생성 | PASS |
| 동일 파일 | Cache 사용 | PASS |
| Hash 변경 | 재Parsing | PASS |

### 문제

Group Shape Text 일부 누락

### 원인

Group Shape 내부 Shape 재귀 탐색 미구현

### 수정

재귀 Text Extractor 적용

### 재테스트

PASS
```

실패 내용을 숨기지 않는다.

---

# 11. Logging

로그:

```text
logs/app.log
```

주요 항목:

```text
Application Start
Database Init
Equipment Add / Update
Git Sync Start / End
Git History Search
Trace Search
Git Candidate Created
PPT Candidate Search
PPT Cache Hit
PPT Cache Miss
PPT Parse Start / End
PPT Parse Error
Evidence Link
Ollama Request
Ollama Error
Continue Integration Request
```

로그에 다음 내용을 전체 저장하지 않는다.

```text
Full Diff
PPT 전체 Text
Slide 전체 Content
전체 AI Prompt
선택 코드 전체
```

민감한 코드 또는 문서 내용이 로그에 누적되지 않도록 한다.

---

# 12. Error 처리 원칙

사용자 화면 또는 Continue 응답에 Python Exception을 그대로 표시하지 않는다.

예:

```text
Bad

FileNotFoundError: [WinError 3] ...
```

표시:

```text
변경내역서 경로를 찾을 수 없습니다.

장비 관리에서 서버 경로를 확인하십시오.
```

상세 오류는 로그에 기록한다.

개별 PPT Parsing 오류는 전체 Trace 요청을 즉시 실패시키지 않는다.

가능한 다른 근거를 계속 탐색한다.

---

# 13. 테스트 자동화

Backend 주요 Service는 pytest 테스트가 가능하도록 구현한다.

## Unit Test

```text
Git Path Validation
Git Log Parsing
Git Diff Parsing
Trace Keyword Extraction
Git Candidate Score
PPT Candidate Date Parsing
PPT Candidate Score
SHA-256
PPT Text Extraction
Cache Validation
Link Score
Ollama Response Parser
```

## Integration Test

```text
Git Repository Sync
Trace Search
PPT Candidate Search
PPT On-demand Parse
Cache Reuse
Git-PPT Link
Ollama Local API
Continue Integration
```

Ollama는 일반 Unit Test에서 직접 호출하지 않는다.

Mock/Fake Response를 사용한다.

---

# 14. Cursor 작업 원칙

Cursor는 각 STEP 시작 시 다음을 확인한다.

```text
PROJECT_SPEC.md
현재 구현 상태
기존 테스트
DB Schema
TEST_PLAN.md
```

이미 완료된 STEP 0~3 기능을 새 방향에 맞춘다는 이유로 임의 재작성하지 않는다.

STEP 0~3은 현재 구현을 기반으로 유지한다.

변경이 필요한 경우:

```text
변경 이유
영향 범위
수정 파일
기존 테스트 영향
```

을 먼저 확인하고 최소 범위로 수정한다.

---

# 15. Cursor 단계별 완료 보고 형식

각 STEP 완료 시 다음을 보고한다.

```text
1. 구현한 기능

2. 생성 또는 수정한 파일

3. 핵심 구현 방식

4. 실행 방법

5. 테스트 방법

6. 테스트 결과

7. 현재 제한 사항

8. 다음 STEP 진행 전 확인 사항
```

추가로 반드시 보고한다.

```text
테스트 실패 이력
실패 원인
수정 내용
재테스트 결과
```

STEP별 핵심 설계 정책도 보고한다.

---

# 16. 금지 사항

다음 구현을 하지 않는다.

```text
Git 경로 하드코딩

PPT 경로 하드코딩

외부 Cloud AI API

CDN

Runtime Package 자동 다운로드

Ollama 장애 시 전체 시스템 장애

AI 답변만 표시하고 Evidence 숨김

전체 Repository를 LLM Prompt에 전달

전체 PPT를 LLM Prompt에 전달

모든 PPT 사전 Parsing을 기본 정책으로 구현

전체 변경내역서 동기화 버튼 구현

초기 단계 Vector DB 도입

불필요한 Microservice

Docker 필수 구조

PPT 변경 사유를 규칙 없이 AI가 임의 구조화

Continue 연계 방식 미확인 상태에서 특정 Plugin 구조 강제
```

---

# 17. 최종 완료 시나리오

## Scenario 1

관리자가 장비를 등록한다.

```text
장비
AG

Git
D:\Source\AG

변경내역
D:\ChangeDoc\AG
```

## Scenario 2

Git 이력을 동기화한다.

```text
Commit / Diff DB 인덱싱
```

PPT는 전체 분석하지 않는다.

## Scenario 3

개발자가 VSCode에서 `FareCalc.c`를 확인한다.

코드:

```c
if (cardType == TYPE_CHILD) {
    fare = CHILD_FARE;
}
```

## Scenario 4

Continue에 질문한다.

```text
CHILD_FARE가 왜 추가됐어?
```

## Scenario 5

Backend가 Git 이력을 탐색한다.

```text
Commit
a82bc93

Date
2024-03-15

File
FareCalc.c

Message
어린이 카드 요금 처리 추가
```

## Scenario 6

Git Context를 이용하여 PPT 후보를 탐색한다.

```text
20240315_AG_변경내역.pptx
어린이카드_변경.pptx
```

## Scenario 7

상위 PPT 후보만 Parsing한다.

```text
20240315_AG_변경내역.pptx
Slide 7
```

Cache가 없으면 생성한다.

이미 동일 Hash Cache가 존재하면 재Parsing하지 않는다.

## Scenario 8

Git과 PPT 근거를 연계한다.

```text
Git a82bc93
↕
20240315_AG_변경내역.pptx / Slide 7
```

## Scenario 9

Ollama가 근거 기반 분석을 수행한다.

```text
어린이 카드가 일반 카드로 판단되어 일반 요금이 적용되는
문제를 수정하기 위해 CHILD_FARE 처리가 추가되었습니다.
```

## Scenario 10

Continue에 결과를 표시한다.

```text
변경 사유

어린이 카드가 일반 카드로 판단되어 일반 요금이 적용되는
문제를 수정하기 위한 변경입니다.

Git 근거
a82bc93

변경내역서 근거
20240315_AG_변경내역.pptx
Slide 7
```

## Scenario 11

동일 PPT와 관련된 다른 질문을 한다.

예상:

```text
기존 PPT Cache 사용
PPT 재Parsing 없음
```

## Scenario 12

Ollama를 중단한다.

예상:

```text
AI 분석 사용 불가

Git 근거 정상
PPT 근거 정상
```

## Scenario 13

신규 내부망 PC에 배포한다.

예상:

```text
인터넷 연결 없이 설치
Backend 실행
Continue 연계
변경 추적 질문 수행
```

---

# 18. 현재 개발 상태 및 다음 작업

현재 완료:

```text
STEP 0 완료
STEP 1 완료
STEP 2 완료
STEP 3 완료
```

다음 작업:

```text
STEP 4 변경 추적 요청 API 및 Trace 흐름 구축
```

Cursor는 현재 프로젝트를 확인한 후 STEP 4만 구현한다.

아직 다음 기능은 구현하지 않는다.

```text
PPT Parsing
PPT Cache
Git-PPT Link
Ollama Analysis
Continue Integration
Vector DB
OCR
```

STEP 4 완료 후 본 문서의 Cursor 단계별 완료 보고 형식에 따라 결과를 보고한다.
