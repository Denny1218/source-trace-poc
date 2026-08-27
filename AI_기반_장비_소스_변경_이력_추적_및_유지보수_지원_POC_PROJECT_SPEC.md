# AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC 개발 작업지시서

## 1. 프로젝트 개요

### 1.1 프로젝트 제목

**AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC**

### 1.2 프로젝트 목적

여러 장비의 Git 소스코드 변경 이력과 PPT 형식의 변경내역서를 연계하여 다음 정보를 조회할 수 있는 시스템을 개발한다.

- 특정 코드가 언제 변경되었는지 확인
- 어떤 Commit에서 변경되었는지 확인
- 변경 전/후 코드를 비교
- 관련 변경내역서와 Slide 확인
- 변경 사유를 근거 문서 기반으로 확인
- 자연어 질문을 통해 관련 변경 이력 검색
- AI 분석 결과에 Git 및 변경내역서 근거 표시

본 POC의 핵심은 단순 Git 검색이 아니라 장비 소스 변경 이력과 변경 근거 문서를 연계하여 유지보수 시 변경 배경을 빠르게 확인할 수 있도록 하는 것이다.

```text
소스코드
    ↓
Git 변경 이력
    ↓
Commit / Diff
    ↓
관련 변경내역서
    ↓
변경 사유
```

---

## 2. 중요 개발 원칙

본 POC는 인터넷이 가능한 개발 PC에서 개발하지만 최종 운영 환경은 인터넷이 차단된 내부망이다.

따라서 모든 기능은 다음 환경을 고려하여 개발한다.

```text
개발 PC
인터넷 가능
Cursor 사용

        ↓

내부 테스트 PC
인터넷 차단 환경 테스트
VSCode 사용 가능
Ollama 사용 가능

        ↓

설치 서버 PC
Backend / DB / Index 실행

        ↓

운영 PC
Browser를 통해 시스템 사용
```

### 필수 원칙

1. 인터넷 연결 없이 실행 가능해야 한다.
2. 외부 CDN을 사용하지 않는다.
3. 실행 시 외부 API를 호출하지 않는다.
4. npm 또는 pip 패키지를 런타임 중 자동 다운로드하지 않는다.
5. Python 및 Node 의존성을 명확하게 관리한다.
6. 장비별 Git 경로와 변경내역서 경로를 코드에 하드코딩하지 않는다.
7. Windows 환경을 기본 실행 환경으로 한다.
8. 각 개발 단계 완료 후 독립적인 테스트가 가능해야 한다.
9. 기능 구현과 테스트 절차를 함께 작성한다.
10. 최종 단계 이전에도 서버 PC 또는 테스트 PC로 복사하여 실행 검증할 수 있어야 한다.

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

## Database

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

## 검색

```text
SQLite FTS5
```

## AI

```text
Ollama REST API
```

초기 버전에서는 Vector DB를 사용하지 않는다.

초기 검색은 다음 방식으로 구현한다.

```text
SQLite FTS5
+
Keyword Matching
+
날짜 근접도
+
파일명 및 함수명 Matching
```

AI는 검색된 후보 데이터의 관련성 분석 및 변경 사유 요약에 사용한다.

---

# 4. 시스템 실행 구조

기본 구조는 서버-클라이언트 방식으로 구성한다.

```text
운영 PC
Browser
   │
   │ HTTP
   ▼
설치 서버 PC
FastAPI
   │
   ├── React 정적 파일
   ├── SQLite
   ├── Git Analyzer
   ├── PPT Parser
   └── Ollama Client
```

운영 PC에는 별도 프로그램 설치를 요구하지 않는다.

가능하면 Browser만으로 접속한다.

예:

```text
http://서버IP:8010
```

개발 초기에는 다음 구조도 허용한다.

```text
React Dev Server
http://localhost:5173

FastAPI
http://localhost:8010
```

단, 배포 단계에서는 React build 결과물을 FastAPI 또는 별도 정적 파일 서비스 방식으로 제공하여 실행 프로세스를 단순화한다.

최종 목표:

```text
Backend 실행
↓
Browser 접속
↓
시스템 사용
```

---

# 5. 프로젝트 디렉터리 구조

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
│   │   │   ├── documents.py
│   │   │   ├── search.py
│   │   │   └── analysis.py
│   │   │
│   │   ├── services/
│   │   │   ├── git_service.py
│   │   │   ├── ppt_service.py
│   │   │   ├── search_service.py
│   │   │   ├── link_service.py
│   │   │   └── ollama_service.py
│   │   │
│   │   ├── models/
│   │   │   └── database.py
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
│   │
│   ├── requirements.txt
│   └── requirements-lock.txt
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
│
├── scripts/
│   ├── start-dev.bat
│   ├── start-server.bat
│   ├── check-environment.bat
│   ├── test-backend.bat
│   └── build-frontend.bat
│
├── data/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
├── deploy/
│   ├── README.md
│   └── OFFLINE_INSTALL.md
│
├── tests/
│   └── test-data/
│
├── PROJECT_SPEC.md
├── TEST_PLAN.md
├── DEPLOYMENT.md
└── README.md
```

기능 증가에 따라 구조를 변경할 수 있으나 과도한 추상화는 하지 않는다.

---

# 6. 환경 설정 원칙

환경별 설정은 소스코드와 분리한다.

예:

```text
.env
```

또는:

```text
config.json
```

예시:

```env
APP_HOST=0.0.0.0
APP_PORT=8010

DATABASE_PATH=./data/equipment_change_trace.db

OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3.5:9b

LOG_LEVEL=INFO
```

장비 Git 경로와 PPT 경로는 환경 설정 파일에 저장하지 않는다.

다음 정보는 DB에서 관리한다.

```text
장비명
Git Repository 경로
변경내역서 폴더
```

---

# 7. 개발 단계별 작업

모든 단계는 다음 형식을 따른다.

```text
개발
↓
로컬 테스트
↓
테스트 데이터 검증
↓
독립 실행 확인
↓
완료 조건 확인
```

각 단계 완료 후 다음 단계로 진행한다.

---

# STEP 0. 프로젝트 기본 실행 환경 구축

## 목표

Frontend와 Backend가 각각 정상 실행되고 기본 상태 확인이 가능해야 한다.

## Backend 구현

다음 API를 구현한다.

```http
GET /api/health
```

응답 예:

```json
{
  "status": "ok",
  "database": "ok",
  "git": "available",
  "ollama": "available"
}
```

Ollama가 없는 경우 시스템 전체가 실패하면 안 된다.

예:

```json
{
  "status": "ok",
  "database": "ok",
  "git": "available",
  "ollama": "unavailable"
}
```

## Frontend 구현

기본 Dashboard 화면을 생성한다.

표시 항목:

```text
Backend 연결 상태
Database 상태
Git 사용 가능 여부
Ollama 연결 상태
```

## 환경 점검 Script

다음 파일을 작성한다.

```text
scripts/check-environment.bat
```

확인 항목:

```text
Python 실행 여부
Python Version
Git 실행 여부
Git Version
Node 실행 여부
Node Version
Ollama 연결 여부
8010 Port 사용 여부
```

## 테스트

### 개발 PC

```text
check-environment.bat 실행
Backend 실행
Frontend 실행
Browser 접속
Health API 확인
```

### 내부 테스트 PC

프로젝트를 복사한다.

인터넷 연결 없이 다음을 확인한다.

```text
환경 점검 Script 실행
Backend 실행
Frontend 실행
Health API 확인
```

## 완료 조건

- 인터넷 없이 Backend 실행 가능
- Health API 정상 응답
- Git 설치 여부 확인 가능
- Ollama 장애가 시스템 전체 실행을 막지 않음
- 실행 오류가 logs 폴더에 기록됨

---

# STEP 1. 장비 관리 기능

## 목표

관리 화면에서 장비별 Git 저장소와 변경내역서 경로를 관리한다.

## 데이터 모델

```text
equipment
```

필드:

```text
id
name
git_path
document_path
created_at
updated_at
```

## API

```http
GET    /api/equipment
GET    /api/equipment/{id}
POST   /api/equipment
PUT    /api/equipment/{id}
DELETE /api/equipment/{id}
```

## Git 경로 검증

다음 명령을 사용한다.

```bash
git -C "{repo_path}" rev-parse --is-inside-work-tree
```

## 문서 경로 검증

다음 조건을 확인한다.

```text
폴더 존재 여부
읽기 가능 여부
PPTX 파일 수
```

## 관리 화면

기능:

```text
장비 목록
장비 추가
장비 수정
장비 삭제
Git 경로 검증
문서 경로 검증
```

장비 등록 화면 예:

```text
장비명

Git Repository 경로

변경내역서 폴더

[경로 확인]

[저장]
```

Browser 보안 정책상 Web에서 서버 PC의 폴더 선택 기능 구현이 어려운 경우 직접 경로 입력 방식을 기본으로 사용한다.

서버 PC의 실제 경로를 관리하는 기능이므로 운영 PC의 로컬 폴더를 선택하는 기능으로 잘못 구현하지 않는다.

## 테스트 데이터

다음 테스트 장비를 준비한다.

```text
TEST_DEVICE_A
TEST_DEVICE_B
```

각 장비에 독립적인 테스트 Git Repository와 PPT 폴더를 사용한다.

예:

```text
tests/test-data/device-a/repository
tests/test-data/device-a/documents

tests/test-data/device-b/repository
tests/test-data/device-b/documents
```

## 테스트

### Test 1

정상 Git Repository 등록

예상:

```text
등록 성공
```

### Test 2

일반 폴더를 Git 경로로 등록

예상:

```text
Git Repository가 아닙니다.
```

### Test 3

존재하지 않는 PPT 경로 등록

예상:

```text
경로를 찾을 수 없습니다.
```

### Test 4

장비 수정 후 Backend 재시작

예상:

```text
수정 내용 유지
```

## 완료 조건

- 장비 CRUD 동작
- 경로 하드코딩 없음
- DB에 장비 정보 저장
- Backend 재시작 후 데이터 유지
- 서로 다른 두 장비 경로 등록 가능

---

# STEP 2. Git 변경 이력 수집

## 목표

등록된 장비의 Git Repository에서 Commit 및 파일 변경 정보를 수집한다.

## 수집 정보

### git_commit

```text
id
equipment_id
commit_hash
commit_date
author
message
parent_hash
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

## Git 명령 사용 원칙

Git CLI를 사용한다.

Python에서는 다음 방식을 사용한다.

```python
subprocess.run()
```

Shell 문자열 실행을 피하고 Argument List 방식을 사용한다.

예:

```python
subprocess.run(
    [
        "git",
        "-C",
        repo_path,
        "log",
    ],
    capture_output=True,
    text=True,
)
```

경로에 공백 또는 한글이 있어도 동작하도록 한다.

## API

```http
POST /api/equipment/{id}/sync/git
GET  /api/equipment/{id}/git/commits
GET  /api/git/commits/{commit_hash}
```

## 동기화 방식

첫 동기화:

```text
전체 Commit 수집
```

두 번째 이후:

```text
마지막 수집 Commit 확인
↓
신규 Commit만 수집
```

중복 Commit 저장을 금지한다.

Database Unique Constraint를 사용한다.

예:

```text
equipment_id + commit_hash
```

## 테스트용 Repository 생성

테스트 Git Repository에는 최소 다음 이력을 만든다.

```text
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
```

## 테스트

### Test 1

최초 Git 동기화

예상:

```text
5 Commit 수집
```

### Test 2

동일 Repository 재동기화

예상:

```text
신규 Commit 0
중복 저장 0
```

### Test 3

새 Commit 생성 후 동기화

예상:

```text
신규 Commit 1
```

### Test 4

Repository 경로 변경

예상:

```text
새 경로 검증
새 Repository 데이터 정상 수집
```

### Test 5

한글 Commit Message

예상:

```text
문자 깨짐 없음
```

## 완료 조건

- Commit 이력 DB 저장
- Diff 저장
- 신규 Commit 증분 수집
- 중복 데이터 없음
- 한글 Commit Message 정상 처리
- 경로에 공백이 있어도 동작

---

# STEP 3. Git 이력 조회 화면

## 목표

AI 없이 Git 데이터만으로 변경 이력을 조회할 수 있어야 한다.

## 화면 기능

```text
장비 선택
검색어 입력
기간 선택
파일 경로 Filter
Commit 목록
Commit 상세
Diff 표시
```

## 검색 가능 대상

```text
Commit Message
파일 경로
Diff Text
Commit Hash
Author
```

## Commit 상세 화면

표시 항목:

```text
Commit Hash
Date
Author
Message

변경 파일 목록

Diff
```

Diff는 다음 형식을 시각적으로 구분한다.

```text
추가 라인
삭제 라인
Context
```

## 테스트

검색어:

```text
CHILD_FARE
```

예상:

```text
CHILD_FARE가 포함된 Diff Commit 조회
```

검색어:

```text
CalcFare
```

예상:

```text
함수 관련 변경 조회
```

## 완료 조건

- AI가 없어도 Git 변경 검색 가능
- Commit 상세 조회 가능
- Diff 확인 가능
- 장비별 검색 가능

---

# STEP 4. PPT 변경내역서 분석

## 목표

등록된 변경내역서 폴더에서 PPTX 문서를 읽고 Slide Text를 수집한다.

## 지원 파일

초기 버전:

```text
.pptx
```

`.ppt` 파일은 지원 대상에서 제외한다.

지원하지 않는 파일 발견 시 오류가 아니라 Skip 처리하고 로그를 남긴다.

## 데이터 모델

### document

```text
id
equipment_id
file_name
file_path
file_hash
modified_at
indexed_at
```

### document_slide

```text
id
document_id
slide_number
title
content
```

## PPT Text 추출

다음 요소의 Text를 추출한다.

```text
TextBox
Placeholder
Table Cell
Group Shape 내부 Text
```

가능한 범위에서 재귀적으로 Shape를 탐색한다.

이미지 OCR은 초기 버전에서 구현하지 않는다.

## 문서 변경 감지

다음 정보를 사용한다.

```text
file_path
file_hash
modified_at
```

동기화 규칙:

```text
신규 파일
→ 분석

Hash 변경
→ 기존 Slide 삭제 후 재분석

Hash 동일
→ Skip

파일 삭제
→ deleted 상태 처리 또는 DB 정리
```

구현 방식은 단순하고 데이터 무결성이 높은 방식을 선택한다.

## API

```http
POST /api/equipment/{id}/sync/documents
GET  /api/equipment/{id}/documents
GET  /api/documents/{id}
```

## 테스트 PPT

최소 5개 PPTX 파일을 준비한다.

내용 예:

```text
어린이 카드 요금 오류 수정
FareCalc.c
CHILD_FARE

환승 요금 계산 조건 수정
CalcTransferFare

정산 파일 생성 오류 수정

통신 Timeout 변경

화면 문구 변경
```

## 테스트

### Test 1

최초 동기화

예상:

```text
5 문서 분석
Slide Text 저장
```

### Test 2

동일 문서 재동기화

예상:

```text
재분석 없음
```

### Test 3

PPT 내용 수정

예상:

```text
변경 파일 1개 재분석
```

### Test 4

Table 내부 Text

예상:

```text
검색 가능
```

### Test 5

한글 Text

예상:

```text
문자 깨짐 없음
```

## 완료 조건

- PPTX Text 추출 가능
- Slide 단위 저장
- Table Text 추출
- Hash 기반 변경 감지
- 재동기화 가능

---

# STEP 5. 변경내역서 검색 화면

## 목표

AI 없이 변경내역서 내용을 검색할 수 있어야 한다.

## 검색 대상

```text
파일명
Slide 제목
Slide Content
```

## 검색 결과

예:

```text
어린이 카드 요금 오류 수정

문서
20240315_AG_변경내역.pptx

Slide
7

일치 내용
특정 어린이 카드 사용 시 일반 요금이 적용되는 문제...
```

## 완료 조건

- 키워드 검색 가능
- 장비별 Filter 가능
- 문서 및 Slide 번호 확인 가능
- 검색 결과에서 Slide 전체 Text 확인 가능

---

# STEP 6. Git 변경과 PPT Slide 연계

## 목표

Git 변경 이력과 변경내역서 Slide의 관련 후보를 계산한다.

AI는 아직 필수로 사용하지 않는다.

## Candidate 점수

초기 기준:

```text
날짜 근접도           30
파일명 일치           20
Commit Message 유사도 20
Diff Keyword 유사도   20
함수명 또는 Symbol    10
```

총점:

```text
100
```

점수 기준은 코드 상수로 분산하지 않는다.

다음과 같이 한 곳에서 관리한다.

```python
LINK_SCORE_CONFIG = {
    "date": 30,
    "file_name": 20,
    "commit_message": 20,
    "diff_keyword": 20,
    "symbol": 10,
}
```

## 데이터 모델

### change_link

```text
id
git_change_id
document_slide_id
score
link_reason
created_at
```

## link_reason 예

```json
{
  "date_score": 30,
  "file_score": 20,
  "message_score": 18,
  "diff_score": 15,
  "symbol_score": 10
}
```

사용자가 점수 근거를 확인할 수 있어야 한다.

## Candidate 생성

Git 변경 1건에 대해 모든 Slide와 비교하지 않는다.

먼저 Candidate 범위를 줄인다.

예:

```text
Commit Date ± 90일
동일 장비
```

그 이후 점수를 계산한다.

## 화면

Commit 상세 화면에 다음 영역을 추가한다.

```text
관련 변경내역 후보

1.
20240315_AG_변경내역.pptx
Slide 7
연관도 93

2.
20240320_AG_변경내역.pptx
Slide 3
연관도 61
```

점수를 클릭하면 근거를 표시한다.

## 테스트

미리 정답을 알고 있는 Git Commit과 PPT Slide Pair를 최소 10개 준비한다.

예:

```text
Commit A ↔ Slide A
Commit B ↔ Slide B
...
```

테스트 결과를 다음 형식으로 기록한다.

```text
Top 1 성공률
Top 3 성공률
Top 5 성공률
```

## 완료 조건

최소 목표:

```text
Top 5 후보 내 정답 포함
80% 이상
```

테스트 데이터가 적은 경우 성공률을 과도하게 일반화하지 않는다.

실제 테스트 Pair 수를 함께 표시한다.

예:

```text
8 / 10
80%
```

---

# STEP 7. 통합 검색

## 목표

Git 이력과 변경내역서를 하나의 검색 화면에서 조회한다.

## 검색 입력

예:

```text
CHILD_FARE
```

또는:

```text
어린이 카드 요금
```

## 검색 흐름

```text
검색어
↓
Git Search
+
Document Search
↓
Candidate Link
↓
통합 결과
```

## 검색 결과

```text
변경 제목

장비
변경 날짜

Git
Commit Hash
파일
Diff

변경내역
문서명
Slide

관련 점수
```

## 완료 조건

- Git 및 PPT 결과 동시 검색
- 관련 결과 그룹 표시
- 근거 데이터 개별 확인 가능

---

# STEP 8. Ollama 연계

## 목표

검색된 Git 변경 및 변경내역서 근거를 이용하여 변경 사유를 요약한다.

## 중요 원칙

Ollama에게 전체 Git Repository 또는 전체 PPT 문서를 전달하지 않는다.

다음 흐름을 사용한다.

```text
사용자 질문
↓
Local Search
↓
Candidate Ranking
↓
상위 Git / PPT 결과
↓
Ollama Context
↓
분석 결과
```

## Ollama 상태 확인

```http
GET /api/health
```

또는 별도 API:

```http
GET /api/ollama/status
```

Ollama 연결 실패 시:

```text
AI 분석 기능만 비활성화
기존 검색 기능은 정상 동작
```

## AI Prompt 원칙

System Prompt에는 다음 규칙을 포함한다.

```text
제공된 Git 및 변경내역서 근거만 사용한다.

근거에 없는 변경 사유를 사실처럼 생성하지 않는다.

확인할 수 없는 경우 확인 불가라고 답한다.

답변에서 Git Commit과 변경내역서 위치를 표시한다.
```

## AI 응답 구조

가능하면 JSON 구조로 받는다.

예:

```json
{
  "summary": "어린이 카드가 일반 카드로 판단되는 문제를 수정하기 위한 변경입니다.",
  "reason": "카드 타입 판단 조건 오류",
  "confidence": "high",
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

LLM JSON Parsing 실패에 대비한다.

```text
JSON Parse 실패
↓
Raw Response 저장
↓
사용자에게 분석 실패 표시
```

전체 API Error로 처리하지 않는다.

## 완료 조건

- Ollama 연결 가능
- Ollama 중단 시 검색 기능 정상
- 근거 기반 분석
- 근거 없는 사유 생성 억제
- Git / PPT Evidence 표시

---

# STEP 9. 코드 Line 변경 이력 추적

## 목표

특정 파일과 코드 Line의 최종 변경 Commit을 확인하고 관련 변경내역을 조회한다.

## 기본 흐름

```text
파일 선택
↓
현재 소스 표시
↓
Line 선택
↓
git blame
↓
Commit Hash
↓
git show
↓
관련 PPT Candidate
↓
변경 사유 분석
```

## Git 명령

```text
git blame
git show
git log
```

`git blame` 결과만으로 변경 사유를 결정하지 않는다.

반드시 Commit Diff를 함께 조회한다.

## 화면

```text
파일 Tree

Code Viewer

Line Number

선택 Line 정보

Commit
Date
Author
Message

변경 Diff

관련 변경내역

AI 분석
```

## 완료 조건

- 파일 조회 가능
- Line 선택 가능
- Commit 확인 가능
- Diff 확인 가능
- 관련 PPT 확인 가능

---

# STEP 10. 배포 형태 정리

## 목표

개발 도구 없이 내부 서버 PC에서 실행할 수 있는 배포 절차를 만든다.

## 배포 기본안

초기에는 Python 설치형 배포를 허용한다.

필요 환경:

```text
Python
Git
Ollama
```

Frontend는 Build하여 Backend와 함께 배포한다.

운영 PC에는 설치 항목이 없다.

## Frontend Build

```bash
npm run build
```

결과:

```text
frontend/dist
```

FastAPI가 정적 파일을 제공하도록 구성할 수 있다.

## Backend Dependency

다음 파일을 유지한다.

```text
requirements.txt
requirements-lock.txt
```

의존성 버전을 고정한다.

예:

```text
fastapi==...
uvicorn==...
python-pptx==...
```

## Offline 설치 패키지 준비

인터넷 가능 PC에서 다음과 같은 별도 Offline Package 생성 절차를 문서화한다.

예:

```bash
pip download -r requirements-lock.txt -d offline_packages/python
```

내부망 설치:

```bash
pip install --no-index --find-links=offline_packages/python -r requirements-lock.txt
```

Node는 서버 실행 시 필요하지 않는 구조를 목표로 한다.

Frontend build는 개발 PC에서 완료한다.

## 배포 폴더 예

```text
equipment-change-trace-deploy/
│
├── app/
├── frontend/
│   └── dist/
├── data/
├── logs/
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

# 8. 단계별 환경 테스트 전략

개발 완료 후 한 번에 내부망 테스트하지 않는다.

다음 단계마다 내부망 또는 내부망과 유사한 테스트 환경에서 실행 확인한다.

| 단계 | 핵심 테스트 |
|---|---|
| STEP 0 | Backend / Frontend Offline 실행 |
| STEP 1 | 서버 PC 경로 등록 |
| STEP 2 | 실제 Git Repository 읽기 |
| STEP 3 | 운영 PC Browser 조회 |
| STEP 4 | 실제 PPT 폴더 분석 |
| STEP 5 | 한글 변경내역 검색 |
| STEP 6 | Git-PPT 연계 정확도 |
| STEP 7 | 통합 검색 |
| STEP 8 | 내부 Ollama 호출 |
| STEP 9 | 실제 소스 Line 추적 |
| STEP 10 | 신규 PC Offline 설치 |

---

# 9. 테스트 환경 구분

테스트 결과를 환경별로 구분한다.

```text
DEV
TEST-OFFLINE
SERVER
CLIENT
```

## DEV

인터넷 가능 개발 PC

목적:

```text
기능 개발
자동 테스트
UI 개발
```

## TEST-OFFLINE

인터넷 연결을 차단한 테스트 PC 또는 개발 PC의 네트워크 차단 상태

목적:

```text
외부 연결 의존성 확인
Offline 실행 검증
```

## SERVER

실제 설치 서버 또는 동일 조건 PC

목적:

```text
실제 Git 경로 접근
실제 PPT 경로 접근
Ollama 연결
장시간 실행
```

## CLIENT

운영 PC

목적:

```text
Browser 접속
화면 표시
검색
AI 분석 요청
```

---

# 10. 테스트 결과 기록

각 STEP 완료 시 TEST_PLAN.md에 결과를 작성한다.

형식:

```markdown
## STEP 2 Git 동기화

### 테스트 환경

DEV

### 테스트 날짜

2026-07-06

### 테스트 데이터

TEST_DEVICE_A

### 테스트 결과

| 테스트 | 예상 | 결과 |
|---|---|---|
| 최초 동기화 | Commit 5 | PASS |
| 재동기화 | 신규 0 | PASS |
| 신규 Commit | 신규 1 | PASS |

### 문제

한글 Commit Message 일부 깨짐

### 원인

subprocess 기본 Encoding 사용

### 수정

encoding="utf-8" 적용

### 재테스트

PASS
```

모든 단계에서 PASS만 기록하지 않는다.

발생한 문제와 수정 내용을 기록한다.

---

# 11. Logging

모든 주요 기능은 로그를 남긴다.

예:

```text
logs/app.log
```

로그 항목:

```text
Application Start
Database Init
Equipment Add / Update
Git Sync Start
Git Sync End
Git Command Error
Document Sync Start
Document Parse Error
Link Analysis
Ollama Request
Ollama Error
```

민감한 전체 소스 코드 또는 전체 PPT 내용을 로그에 기록하지 않는다.

예:

```text
금지

Full Diff 전체 출력
PPT 전체 Text
AI Prompt 전체 내용
```

기본 로그 예:

```text
2026-07-06 10:30:21
INFO
Git sync started
equipment=AG

2026-07-06 10:30:24
INFO
Git sync completed
equipment=AG
new_commits=12
```

---

# 12. Error 처리 원칙

사용자 화면에 Python Exception 또는 Stack Trace를 그대로 표시하지 않는다.

예:

```text
Bad

FileNotFoundError: [WinError 3]...
```

다음과 같이 표시한다.

```text
변경내역서 경로를 찾을 수 없습니다.

경로:
D:\ChangeDoc\AG

장비 관리에서 경로를 확인하십시오.
```

상세 Exception은 로그에 기록한다.

---

# 13. 테스트 자동화

Backend 주요 Service는 pytest 테스트가 가능하도록 작성한다.

우선 테스트 대상:

```text
Git Repository Validation
Git Log Parsing
Git Diff Parsing
PPT Text Extraction
File Hash
Document Change Detection
Link Score
```

외부 Ollama 호출은 Unit Test에서 직접 호출하지 않는다.

Mock 또는 Fake Response를 사용한다.

실제 Ollama 연결 테스트는 Integration Test로 구분한다.

테스트 구분:

```text
Unit Test

Integration Test

Manual Test

Offline Deployment Test
```

---

# 14. Cursor 작업 원칙

Cursor는 한 번에 전체 시스템을 구현하지 않는다.

반드시 STEP 단위로 작업한다.

예:

```text
STEP 0 구현
↓
Test
↓
문제 수정
↓
완료 확인
↓
STEP 1
```

각 STEP 작업 시작 시 다음을 먼저 확인한다.

```text
PROJECT_SPEC.md
현재 구현 상태
기존 테스트
기존 DB Schema
```

기존 기능을 임의로 대규모 변경하지 않는다.

리팩터링이 필요한 경우 이유를 설명하고 최소 범위로 수정한다.

---

# 15. Cursor 단계별 수행 지시

Cursor는 각 STEP 완료 시 다음 내용을 보고한다.

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

예:

```text
STEP 2 완료

구현 기능
- Git Commit 수집
- Diff 수집
- 증분 동기화

수정 파일
backend/app/services/git_service.py
backend/app/api/git_history.py

실행
scripts/start-dev.bat

테스트
pytest backend/tests/test_git_service.py

결과
8 passed

제한 사항
Merge Commit의 Combined Diff는 현재 별도 처리하지 않음
```

---

# 16. 금지 사항

다음 구현을 하지 않는다.

```text
Git 경로 하드코딩

PPT 경로 하드코딩

외부 Cloud AI API 사용

CDN 사용

런타임 Package 자동 다운로드

Ollama 장애 시 전체 시스템 장애

AI 답변만 표시하고 근거 숨김

전체 Repository를 LLM Prompt에 전달

전체 PPT 내용을 한 번에 LLM Prompt에 전달

초기 단계에서 불필요한 Vector DB 도입

지나친 Microservice 구조

Docker 필수 구조
```

Docker는 내부 운영 환경에서 사용 가능 여부가 확인되기 전까지 필수 기술로 사용하지 않는다.

---

# 17. 프로젝트 최종 완료 기준

다음 시나리오가 동작해야 한다.

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

Git 및 변경내역 동기화를 실행한다.

```text
Git Commit 수집

PPT Slide 분석
```

## Scenario 3

운영 PC에서 검색한다.

```text
CHILD_FARE
```

## Scenario 4

관련 변경 정보를 조회한다.

```text
2024-03-15

FareCalc.c

Commit
a82bc93

- fare = DEFAULT_FARE
+ fare = CHILD_FARE
```

## Scenario 5

관련 변경내역을 확인한다.

```text
20240315_AG_변경내역.pptx

Slide 7

어린이 카드 요금 오류 수정
```

## Scenario 6

AI 분석을 실행한다.

결과:

```text
어린이 카드가 일반 카드로 판단되어
일반 요금이 적용되는 문제를 수정하기 위한 변경입니다.
```

근거:

```text
Git
a82bc93

변경내역서
20240315_AG_변경내역.pptx
Slide 7
```

## Scenario 7

Ollama를 중단한다.

예상:

```text
AI 분석 사용 불가

Git 검색 정상
변경내역 검색 정상
Commit 상세 정상
```

## Scenario 8

프로젝트를 신규 내부망 PC에 복사한다.

OFFLINE_INSTALL.md 절차만 사용한다.

예상:

```text
인터넷 연결 없이 설치
서버 실행
운영 PC Browser 접속
```

---

# 18. 최초 개발 시작 지시

현재 프로젝트가 비어 있다면 STEP 0부터 시작한다.

Cursor는 우선 다음 작업만 수행한다.

```text
1. 프로젝트 기본 디렉터리 생성

2. FastAPI 기본 Application 생성

3. SQLite 초기화 구조 생성

4. GET /api/health 구현

5. React + TypeScript + Vite 기본 화면 생성

6. Backend Health 상태 표시

7. check-environment.bat 생성

8. start-dev.bat 생성

9. 기본 Logging 구성

10. STEP 0 테스트 작성
```

아직 다음 기능은 구현하지 않는다.

```text
Git Commit 수집

PPT 분석

Ollama 분석

Vector Search

AI Chat UI
```

STEP 0 완료 후 구현 결과와 테스트 결과를 보고하고 다음 작업을 진행한다.
