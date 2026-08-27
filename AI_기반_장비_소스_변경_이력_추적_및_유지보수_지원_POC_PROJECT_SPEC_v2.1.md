# AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC
## PROJECT_SPEC v2.1 — 현재 기준 명세

- 문서 상태: **현재 기준**
- 기준일: **2026-07-31**
- 이전 기준: `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`
- 적용 우선순위: 본 문서가 이전 v2 및 현행화 보완문서와 충돌하면 본 문서를 따른다.
- 작업 제한: **STEP 10은 사용자 승인 없이 진행하지 않는다.**
- 일반 작업에서는 본 문서만 기준으로 사용한다. 이전 v2와 현행화 보완문서는 변경 이력 참고용이다.

---

## 0. 문서 관리와 상태 기준

### 0.1 기준 문서 정책

앞으로 Cursor 작업 지시문에는 다음 파일만 기준 명세로 지정한다.

```text
AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.1.md
```

기존 v2와 v2.1 현행화 보완명세를 매 작업마다 다시 병합하거나 함께 우선 참조하지 않는다.

### 0.2 상태 정의

| 상태 | 의미 |
|---|---|
| 완료 | 구현 및 기본 회귀 테스트 완료 |
| 완료·정확도 개선 중 | 기능은 동작하지만 운영 데이터 정확도 보정이 계속 필요 |
| 승인됨·미구현 | 구현 방향은 승인되었으나 완료 보고와 실제 테스트가 아직 없음 |
| 검증 필요 | 구현 여부 또는 운영환경 동작을 실제 코드·산출물로 확인해야 함 |
| 미착수 | 아직 공식 작업을 시작하지 않음 |

### 0.3 현재 상태 요약

| 구분 | 상태 |
|---|---|
| 장비·Git Repository 관리 | 완료 |
| Git 동기화·Commit/Diff 조회 | 완료 |
| PPT 후보 탐색·On-demand Parsing·Cache | 완료 |
| 규칙 기반 Git-PPT Evidence Link | 완료 |
| Ollama 근거 기반 보조 설명 | 완료 |
| 함수 Git lifecycle 조회 | 완료·정확도 개선 중 |
| lifecycle 단계별 PPT 연결·문서 집계 | 완료·정확도 개선 중 |
| Source Trace VS Code Extension 분석 기능 | 완료 |
| Extension 최초 서버·장비 설정 | 완료 |
| Extension Output 진행 상태 표시 | 완료 |
| Output 기본 로그와 진단 로그 분리 | 승인됨·미구현 |
| Continue config 삽입 문구 생성·복사 | 완료 |
| Continue Context 원문 보호·Status API·Output polling | 완료 |
| 공식 운영환경 종합 검증 STEP 10 | 미착수 |

버전 번호는 명세에 고정하지 않는다. 실제 Extension 버전은 다음을 기준으로 확인한다.

```text
vscode-extension/package.json
산출물/운영PC의 최신 VSIX
Extension 완료 보고
```

---

## 1. 프로젝트 개요

### 1.1 프로젝트 제목

**AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC**

### 1.2 목적

개발자가 VS Code에서 장비 소스의 특정 함수·Symbol·코드를 확인하면서 다음 질문에 근거 기반으로 답할 수 있도록 한다.

```text
이 함수는 언제 추가됐는가?
어떤 변경 과정을 거쳤는가?
왜 변경됐는가?
어떤 공식 변경내역서와 관련되는가?
초기 적용과 후속 유지보수를 구분할 수 있는가?
```

시스템은 다음 근거를 결합한다.

- 장비별 Git Repository와 Commit 이력
- 파일 단위 Diff
- 함수·Symbol의 전체 lifecycle
- PPTX 프로그램 변경내역서
- 공식 기능 적용·배포 근거
- 개발 과정 참고 근거
- 후속 유지보수 근거
- 선택적 내부 Ollama 설명

### 1.3 핵심 사용자 경험

```text
VS Code에서 함수 또는 코드 선택
→ 장비 변경 이력 조회
→ 질문 입력
→ Source Trace Backend 호출
→ 함수 Git lifecycle 구성
→ PPT 후보 탐색 및 필요한 문서만 분석
→ lifecycle 단계별 Git-PPT 근거 연결
→ 근거 기반 Markdown 결과 표시
```

### 1.4 인터페이스 우선순위

```text
주 사용 인터페이스
- Source Trace VS Code Extension

보조 관리·검증 인터페이스
- Web UI

선택적 호환 인터페이스
- Continue
```

Continue 설치 또는 `config.yaml` 설정은 Extension 사용의 필수 조건이 아니다.

---

## 2. 운영 환경과 개발 원칙

### 2.1 환경

```text
개발 PC
- 인터넷 가능
- Cursor 사용
- 기능 개발·테스트·패키징

서버 PC
- Windows 기본 운영
- FastAPI Backend
- SQLite
- Git CLI
- PPT Parser·Cache
- Ollama Client
- 장비 Git Repository 및 변경내역서 접근

운영 PC
- 인터넷 차단
- VS Code
- Source Trace Extension VSIX
- 필요 시 Continue
- Web 관리 화면
```

### 2.2 필수 원칙

1. 최종 환경은 인터넷 없이 실행 가능해야 한다.
2. 외부 Cloud AI API와 외부 CDN을 사용하지 않는다.
3. 실행 중 npm·pip 패키지를 자동 다운로드하지 않는다.
4. Python·Node 의존성 버전을 고정·관리한다.
5. 장비 경로, Git URL, 서버 IP, 포트, 장비 ID를 소스에 고정하지 않는다.
6. `equipment_id=1` 또는 특정 서버 주소를 환경 독립 기본값으로 사용하지 않는다.
7. Ollama 장애가 Git·PPT 근거 조회를 막지 않아야 한다.
8. 전체 Repository나 전체 PPT 내용을 LLM Prompt에 전달하지 않는다.
9. PPT는 필요한 후보만 On-demand 분석하고 Cache한다.
10. Cache는 삭제·재생성 가능한 검색 보조 데이터로 취급한다.
11. AI가 근거에 없는 변경 이유를 사실처럼 생성하지 않게 한다.
12. 기능 변경 시 테스트와 산출물을 함께 갱신한다.
13. 특정 함수명, Commit hash, PPT 파일명을 운영 코드 조건문에 하드코딩하지 않는다.
14. STEP 10은 별도 승인 없이 진행하지 않는다.

---

## 3. 기술 구성

### 3.1 Frontend

```text
React
TypeScript
Vite
```

### 3.2 Backend

```text
Python
FastAPI
```

### 3.3 Database와 Cache

```text
SQLite
```

### 3.4 Git 분석

```text
Git CLI
Python subprocess
```

### 3.5 PPT 분석

```text
python-pptx
```

### 3.6 내부 AI

```text
Ollama REST API
```

Ollama는 검색 정확도를 만드는 핵심 구성요소가 아니다. Git/PPT 근거가 확정된 후 문장을 보조하는 선택 기능이다.

### 3.7 VS Code Extension

```text
TypeScript
VS Code Extension API
VSIX 오프라인 배포
```

---

## 4. 전체 구조

```text
┌────────────────────────────────────┐
│ Source Trace VS Code Extension     │
│ 선택: Continue                     │
└─────────────────┬──────────────────┘
                  │ HTTP
                  ▼
┌────────────────────────────────────┐
│ Source Trace Backend               │
│                                    │
│ Equipment / Repository API         │
│ Git Sync / History API             │
│ Trace / Continue Trace API         │
│ Function Lifecycle Service         │
│ PPT Candidate Service              │
│ PPT On-demand Parser / Cache        │
│ Evidence Link Service              │
│ Lifecycle PPT Matcher              │
│ Ollama Analysis Service            │
└──────────┬───────────────┬─────────┘
           │               │
           ▼               ▼
   Git Repositories    PPTX Documents
           │               │
           └──────┬────────┘
                  ▼
┌────────────────────────────────────┐
│ SQLite                             │
│ equipment                          │
│ git_repository                     │
│ git_commit                         │
│ git_change                         │
│ document_cache                     │
│ slide_cache                        │
│ change_link                        │
│ 기타 실제 구현 테이블              │
└────────────────────────────────────┘
```

### 4.1 데이터 연결 개념

다음 두 연결을 구분한다.

```text
change_link
- Git change와 PPT Slide 간 규칙 기반 Evidence Link
- 저장 가능한 DB 근거

lifecycle 문서 연결
- 함수 lifecycle의 기능 단계 또는 Commit에 문서를 배치
- 시간·행위·함수·소스 호환성 적용
- 요청 시 구성되는 사용자 결과용 근거
```

둘은 같은 데이터로부터 파생될 수 있지만 동일 개념으로 취급하지 않는다.

---

## 5. 주요 데이터 모델

실제 DB Schema가 본 문서 예시와 다르면 코드와 migration을 확인하여 명세를 갱신한다.

### 5.1 equipment

```text
id
name
document_path
created_at
updated_at
git_path      # Deprecated migration 호환용일 수 있음
```

### 5.2 git_repository

```text
id
equipment_id
name
source_type                 # remote | local
repository_url              # DB/UI 표시용 URL 정책은 실제 Schema와 일치
canonical_repository_url    # userinfo 제거 Repository Identity
yona_username               # 사용자 입력 URL에서 추출한 참고 Context
local_path
status                      # pending | ready | error
created_at
updated_at
```

정책:

- 장비 하나에 여러 Repository를 등록할 수 있다.
- `(equipment_id, name)`은 중복되지 않아야 한다.
- 동일 장비의 동일 canonical Repository URL 중복을 방지한다.
- `repository_url`과 `canonical_repository_url`의 실제 역할이 중복되면 코드 확인 후 하나의 역할로 정리한다.
- 사용자 입력 URL의 username은 실제 서버 Git 접근 계정으로 사용하지 않는다.

### 5.3 git_commit

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

### 5.4 git_change

```text
id
commit_id
file_path
change_type
additions
deletions
diff
```

### 5.5 document_cache

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

### 5.6 slide_cache

```text
id
document_cache_id
slide_number
title
content
```

### 5.7 change_link

```text
id
git_change_id
slide_cache_id
score
link_reason
created_at
```

Cache 재생성 시 `slide_cache` ID 변화와 `change_link` 갱신 정책을 명확히 유지한다.

---

## 6. 장비·경로·Git Repository 정책

### 6.1 장비 관리

Web UI에서 다음을 관리한다.

- 장비 CRUD
- 장비별 Git Repository 1:N
- 변경내역서 경로
- Repository 준비 상태
- Git 동기화
- 경로 검증

### 6.2 Git Repository 경로

허용:

```text
서버 로컬 Git Working Tree
Yona 등 Remote Repository
```

Remote Repository는 최초 준비 시 Clone하고 이후 Sync에서 Fetch한다.

```text
Remote
- 최초: clone
- 이후: fetch --all --prune
- 분석: git log --all

Local
- 지정 Working Tree 분석
- 자동 pull 금지
```

### 6.3 변경내역서 document_path

현재 운영 정책:

```text
UNC 네트워크 공유 경로만 허용
Backend 실행 계정이 Read 접근 가능해야 함
하위 폴더를 재귀 탐색
```

비허용:

```text
운영 PC 브라우저의 로컬 경로
D:\... 형태의 임의 로컬 문서 경로
Backend가 접근할 수 없는 Client 경로
```

예:

```text
\\192.168.155.90\ChangeDocuments\HHD200
```

검증:

- UNC 형식
- 경로 존재
- Directory 여부
- Read 가능 여부
- 필요 시 재귀 PPTX 수 확인

### 6.4 Yona 접근

- URL은 `urllib.parse` 등 안전한 방식으로 분석한다.
- userinfo가 제거된 canonical URL을 Repository Identity로 사용한다.
- 서버 접근 계정은 `YONA_DEFAULT_USERNAME` 등 서버 설정을 사용한다.
- Password·Token을 SQLite, URL, `.env`, 일반 로그에 평문 저장하지 않는다.
- Git Credential Manager를 사용한다.
- 모든 Git subprocess에 `GIT_TERMINAL_PROMPT=0`을 적용한다.
- Credential이나 전체 Remote URL을 INFO 로그와 API 응답에 노출하지 않는다.

### 6.5 다중 Repository 분석

- 선택된 장비 하위의 모든 ready Repository를 검색 대상으로 한다.
- 현재 파일 경로나 Workspace Repository와 일치하는 저장소를 우선할 수 있다.
- Repository를 장비처럼 임의 자동 선택하지 않는다.
- 동일 파일 경로가 여러 Repository에 있으면 결과에 Repository 식별 정보를 포함한다.
- 장비를 잘못 선택한 경우 다른 장비로 자동 fallback하지 않는다.

---

## 7. Git 동기화와 변경 이력

### 7.1 동기화

```text
git log --all
→ Commit hash 목록
→ DB 존재 여부 확인
→ 기존 Commit Skip
→ 신규 Commit 상세·Diff 저장
```

단순히 마지막 Commit 이후만 조회하지 않는다.

### 7.2 수집 정보

- Commit hash
- 날짜
- 작성자
- 메시지
- Parent
- 파일 경로
- 변경 유형
- 추가·삭제 수
- Diff

### 7.3 조회

지원:

- 통합 검색
- 전체 기간 기본
- 기간 필터
- 파일 필터
- 작성자 필터
- Pagination
- Commit 상세
- 파일별 Diff

검색 대상:

```text
Commit Message
Commit Hash
Author
File Path
Diff
```

### 7.4 제한

Merge Commit Parent 저장 방식 등 실제 제한은 테스트와 완료 보고에 명시한다.

---

## 8. PPT 후보 탐색·On-demand 분석·Cache

### 8.1 후보 탐색

`equipment.document_path` 아래 `.pptx`를 재귀 탐색한다.

제외:

```text
.ppt
~$*.pptx
```

후보 점수 근거:

- 파일명 날짜
- 폴더명·파일명 Keyword
- Git Commit 날짜
- Commit Message
- 파일명·함수명·Symbol
- 사용자 질문

파일 modified time을 공식 변경일로 단정하지 않는다.

### 8.2 On-demand Parsing

모든 PPT를 사전 분석하지 않는다.

```text
PPT 후보
→ 상위 후보만 Parse
→ Slide 단위 Cache 저장
```

최소 추출:

- TextBox
- Placeholder
- Table
- Group Shape 내부 Text

OCR, 이미지 내부 Text, SmartArt·Chart 직접 XML Parsing은 기본 범위가 아니다.

### 8.3 Cache

```text
Cache 없음
→ Parse 후 저장

Hash 동일
→ Cache 재사용

Hash 변경
→ Parse 성공 후 Cache 교체

Parse 실패
→ 기존 정상 Cache 보존
```

Hash는 SHA-256 Chunk 방식으로 계산한다.

---

## 9. Evidence Link와 함수 lifecycle

### 9.1 Evidence Link

Git 변경 Candidate와 PPT Slide Candidate의 관련성을 규칙 기반 점수로 계산한다.

대표 근거:

- 날짜 근접도
- 파일명·경로 일치
- Commit Message Keyword
- Diff Symbol
- 사용자 Query
- 함수·Identifier

점수와 근거는 한 곳에서 관리하며 사용자 검증이 가능해야 한다.

### 9.2 함수 lifecycle

함수·Symbol 질문에서는 단일 Top Commit만 보여주지 않고 전체 흐름을 구성한다.

```text
1. 최초 개발 및 기능 확정
2. 개발 및 보조 변경
3. 후속 유지보수
4. 연관 이력 — 필요한 경우만
```

원칙:

- 최초 추가는 Parent Commit에서 기존 정의를 확인한다.
- 최초 추가는 lifecycle에서 한 건만 허용한다.
- Merge Commit이나 실질 변경 없는 후보가 결과를 왜곡하지 않게 한다.
- 가능한 경우 Commit별 exact Diff를 사용한다.
- DB Diff가 부족하면 live `git show` fallback을 사용할 수 있다.
- Diff 미확보 항목은 직접 확인된 변경으로 표현하지 않는다.
- PPT 근거가 없어도 Git lifecycle을 유지한다.

---

## 10. 변경내역서 lifecycle 연결 모델

### 10.1 연결 단위

문서를 함수 lifecycle 전체에 일괄 복제하지 않는다.

다음 두 단위를 분리한다.

```text
A. 기능 단계 공식 문서
- 기능 도입·배포 또는 후속 유지보수 전체를 설명
- exact Commit 연결이 없어도 단계에 유지 가능

B. Commit별 문서 연결
- 개별 Commit과 문서의 직접·간접 관계
- Diff·시간·행위·함수·소스 일치 수준 적용
```

Commit 연결 실패가 공식 문서 제거 사유가 되어서는 안 된다.

로그·주석 Commit에만 연결되었다는 이유로 공식 적용 문서가 `개발 및 보조 변경` 단계로 이동해서는 안 된다.

### 10.2 연결 유형

```text
Commit 직접 근거
기능 배포 근거
개발 과정 참고
후속 유지보수 참고
관련 참고자료
```

### 10.3 Commit 직접 근거

다음을 모두 만족할 때만 허용한다.

- exact Commit Diff 확보
- 대상 함수 범위 내 변경 확인
- Diff 행위와 PPT As-Is/To-Be 일치
- 함수 또는 소스 경로 일치
- 문서·Commit의 시간·배포 구간이 합리적으로 일치

다음은 직접 근거가 아니다.

- Commit Message만 일치
- 같은 함수명만 존재
- 같은 파일만 존재
- Diff 미확보
- 수개월·수년 차이의 반대 행위 문서
- 함수 추가 Commit과 로직 삭제 문서
- 로그 삭제 Commit과 기능 변경 문서

### 10.4 시간과 행위 호환성

평가 정보:

```text
Commit 날짜
문서 작성일
배포 예정일
적용 버전
함수·소스 일치
기능 토큰
변경 행위
```

행위 분류:

```text
적용 / 추가 / 도입
수정 / 보완
삭제 / 제거
테스트 / 로그 정리
```

같은 기능 토큰을 포함하더라도 적용 문서와 삭제 문서는 별도 단계로 구분한다.

### 10.5 검색어 정규화

단어 순서에만 의존하지 않는다.

```text
청소년 후불
후불 청소년
청소년후불
후불청소년
```

공백 제거형과 토큰 집합을 함께 사용하되, 변경 행위까지 비교한다.

### 10.6 공식 문서 Identity와 집계

기본 unique key:

```text
equipment_id
+ normalized_document_path
+ slide_number
+ change_item_id(존재하는 경우)
```

Commit hash는 문서 고유 식별 기준이 아니다.

정책:

- 동일 문서·동일 Slide가 여러 Commit에 연결돼도 공식 문서 수는 1건이다.
- 같은 PPT의 다른 Slide 또는 다른 변경항목은 별도 근거가 될 수 있다.
- 한눈에 보기, 본문, 참조 근거, Extension Output 통계는 같은 unique document collection을 사용한다.

### 10.7 PPT 소스·함수 파싱

다음 필드를 분리한다.

```text
related_source_paths
related_symbols
```

소스 경로:

- `.c`, `.h`, `.cpp`, `.hpp` 등
- `/` 또는 `\`를 포함한 경로
- Prefix 정규화
- 제어문자·중복 제거

Symbol:

- C identifier 형태
- 함수, 구조체, 상수 등
- 파일 경로·확장자 제외
- `()`는 표시 단계에서 통일
- 경로 조각에서 생성된 `Lib()`, `Card()`, `src()` 등을 제외

원문 파일명에 오타가 있을 경우 사용자 출력은 원문을 임의 수정하지 않는다. Git 경로 매칭에는 별도 alias나 정규화 정책을 적용할 수 있다.

---

## 11. 결과 Markdown 계약

### 11.1 기본 구조

```markdown
# <함수명> 변경 이력

## 한눈에 보기

## 변경 상세

### 최초 추가 / 초기 개발 및 기능 확정
- 최초 확인 Commit과 공식 문서 시점이 다르면 `최초 추가`와 `후속 공식 기능 변경`으로 분리한다.
- 시점이 가까운 공식 적용 문서만 있을 때는 기존 `초기 개발 및 기능 확정` + `공식 적용` 표시를 유지한다.
- 오래된 후속 문서를 최초 추가의 단계 공식 문서로 자동 승격하지 않는다.

### 개발 및 보조 변경

### 후속 유지보수 참고

## 공식 근거 문서
- 최초 추가 공식 문서 / 후속 공식 기능 변경 문서 / 후속 유지보수 참고 문서
- (시점이 가까운 경우) 공식 적용 문서

## 분석상 주의사항 — 실제 제한이 있을 때만

## 전체 참조 근거
```

### 11.2 한눈에 보기

최소 정보:

- 최초 확인
- 변경 흐름
- 최초 추가 공식 문서 (없으면 `찾지 못함`) 또는 시점 일치 시 `공식 적용`
- 후속 공식 기능 변경 (해당 시)
- 후속 유지보수 참고
- 공식 문서 건수 요약
- 분석 신뢰도

대표 기능명 우선순위:

```text
시점 일치 공식 적용 문서
→ 후속 공식 기능 변경 문서 (대표용, 최초 추가로로 오해되지 않게 표시)
→ 최초 추가 Commit Message
→ 초기 개발 구간 반복 기능명
```

후속 유지보수 문서 제목 하나가 전체 대표 기능명을 덮어쓰면 안 된다.
후속 유지보수 참고는 Commit 직접 근거로 승격하지 않는다.

### 11.3 Commit 항목과 단계 공식 문서

해당 단계에 공식 문서는 있지만 특정 Commit 직접 연결이 없는 경우 다음을 구분한다.

```text
Commit 직접 연결: 없음
해당 기능 단계 공식 문서: 있음
```

단순히 `연결된 변경내역서 없음`이라고 표시하여 공식 문서 자체가 없는 것처럼 오해시키지 않는다.

### 11.4 집계 일관성

다음 위치는 같은 문서 컬렉션과 동일한 집계 로직을 사용한다.

- 한눈에 보기
- 각 lifecycle 항목
- 공식 적용 문서
- 후속 유지보수 문서
- 참조 근거
- Extension Output

### 11.5 불확실성 문구

금지:

```text
Diff 확보가 제한됨
+
Commit 직접 근거
```

권장:

```text
Commit 메시지상 카드 유형 판정 변경으로 확인되지만,
대상 함수의 세부 Diff는 확보하지 못했습니다.
```

내용이 없는 `분석 범위 및 참고사항`, `특이 제한 사항 없음`은 출력하지 않는다.

---

## 12. Source Trace VS Code Extension

### 12.1 현재 구현 완료

- 함수 또는 코드 선택
- 우클릭·Command Palette 변경 이력 조회
- 질문 입력
- 서버·장비 설정이 없을 때 최초 설정 흐름
- 서버 연결 확인
- 서버 장비 목록 조회
- 장비명을 보고 선택
- 분석 API 호출
- Markdown 결과 표시
- Output Channel 진행 상태 표시
- Notification 유지

### 12.2 서버와 장비 설정

흐름:

```text
서버 URL 입력
→ 연결 확인
→ 서버 장비 목록 조회
→ 장비명 선택
→ 설정 저장
→ 원래 분석 계속
```

사용자는 `equipment_id` 숫자를 미리 알 필요가 없다.

저장 정책:

```text
serverUrl
- User/Global 기본
- 필요 시 Workspace override 허용

equipmentId
- Workspace 우선
- Workspace가 없으면 User/Global
```

분석 전 검증:

- URL 형식
- 서버 연결
- 장비 선택
- 현재 서버에서 장비 존재 여부

다른 장비로 자동 fallback하지 않는다.

### 12.3 주 분석 API

현재 Extension의 주 분석 Endpoint:

```http
POST /api/continue/trace
```

`/api/trace/search`, PPT 후보·분석 API 등은 Backend 내부 흐름 또는 Web 검증용으로 사용할 수 있다.

Endpoint를 변경할 때는 Extension 계약과 하위 호환 정책을 명확히 한다.

### 12.4 Output — 현재 구현

사용자에게 다음을 표시한다.

- 분석 시작
- 서버
- 장비
- 질문 또는 요청 종류
- 함수
- 파일
- 요청 준비
- 서버 전송
- 결과 수신
- 분석 완료
- 주요 결과 수

### 12.5 Output 개선 — 승인됨·미구현

기본 Output에서는 내부 Debug Payload를 제거한다.

제외 대상:

```text
source_mode
selection_mode
immediate_selection_chars
selected_text_chars
selected_code_sent_chars
query_sent
selection line range
recent_fallback
preview
raw request body
internal enum
ISO 내부 timestamp
```

권장 기본 Output:

```text
[14:51:14] Source Trace 분석 시작
서버: http://<서버>:<포트>
장비: <장비명>
요청: 함수 변경 이력 조회
사용자 질문: ...
함수: ...
파일: Workspace 상대 경로

[14:51:14] 요청 준비 완료
[14:51:14] 서버 요청 전송
[14:51:14] 분석 중
[14:52:11] 분석 결과 수신
[14:52:11] Git 변경 이력: N건
[14:52:11] 공식 변경내역서: N건
[14:52:11] 분석 완료 (소요 시간)
```

진단 설정 제안:

```text
sourceTrace.diagnosticLogging = false
```

- 기본 false
- true일 때만 제한된 진단 정보 출력
- 선택 코드 원문, 전체 Diff, Token, Password, 인증 Header는 항상 제외

### 12.6 Continue config 문구 생성 / 원문 보호 / Output polling — 완료 (2026-08-03, 2026-08-04 보완)

Extension은 Continue `config.yaml`을 자동 수정하지 않는다. `Source Trace: Continue
설정 스니펫 생성` 명령으로 구현했다.

서버·장비 설정 후 Extension이 알고 있는 다음 값으로 삽입용 문구를 생성한다.

- 서버 URL(`/api/continue/trace`까지 조립한 전체 URL)
- 장비명과 `equipment_id`
- Workspace별 비식별 `client_id`
- `use_ollama`(기존 Continue 기본 정책인 `true` 유지)
- context `name` 기본값: `<정규화 장비명>변경이력` (비면 `장비변경이력`)

사용자 기능:

```text
Continue 설정 스니펫 생성 (미리보기 문서 자동으로 열림)
클립보드 자동 복사 (생성 직후 YAML만 복사)
```

실제 삽입·저장은 사용자가 수행한다. Extension은 Continue 설정 파일을 직접 열거나
읽지 않는다. 미리보기는 Continue **사이드바 → Local Config → 설정(톱니바퀴)** 으로
`config.yaml`을 여는 방식을 안내한다 (명령 팔레트 `Continue: Open Config`나
Windows 고정 경로를 필수 안내로 쓰지 않는다. Remote-SSH 등에서 경로가 달라질 수 있음).

`name`은 Continue `@호출명`이며 사용자가 YAML에서 변경할 수 있다. 변경 시 채팅
`@호출명`도 같아야 한다. `provider`·`url`·`equipment_id`·`client_id`·`options`는 변경하지 않는
것을 권장한다.

서버 URL 또는 선택 장비가 없으면 스니펫을 생성하지 않고 먼저 설정하도록 안내한다
(서버·장비를 변경한 뒤에는 명령을 다시 실행해 새 스니펫을 생성해야 한다).

Continue config Schema는 새로 추정하지 않고, 저장소에 이미 있던 STEP 9 산출물
`continue-config.example.yaml`(`http` Context Provider, `CONTINUE_INTEGRATION.md`에
문서화된 실제 확인된 구조)을 그대로 사용해 서버 URL·장비명·`equipment_id`·`client_id`·호출명만
채워 넣는다.

Continue native 요청의 `content`는 Source Trace 원문 Markdown을 보호 지시와 함께 감싼다.
단순 변경 이력 질문은 원문 그대로 출력 우선, 함수명 변경 금지, Commit/문서/Slide/코드값 보존,
근거 밖 사실 생성 금지 규칙을 적용한다. 단순 조회에서는 Backend Ollama를 자동 우회해
Continue와의 이중 LLM 왜곡을 줄인다.

VS Code Extension은 Workspace별 `client_id`로 `GET /api/continue/status?client_id=...`
polling을 수행해 `보기 → Output → Source Trace`에 Continue 요청 감지, 단계별 진행,
완료/실패를 표시한다. 이 로그는 Source Trace 백엔드 분석 범위까지만 다루며, Continue 모델의
최종 답변 생성 과정은 추적하지 않는다.

### 12.7 README

README는 현재 Source Trace 사용자 안내만 포함한다.

포함:

- 기능
- VSIX 설치
- 최초 서버·장비 설정
- 사용 방법
- 서버·장비 변경
- 현재 설정 확인
- Output 확인
- 오류 해결
- 관리자 사전 준비
- 구현 완료 후 Continue 설정 문구 생성

제거:

- STEP 번호
- MVP
- POC 데모 과정
- 과거 Continue 비교
- 구현 단계 역사

존재하지 않는 명령·설정을 문서에 쓰지 않는다.

---

## 13. Web UI

Web UI는 관리·검증을 목적으로 한다.

- 장비 관리
- Repository 관리
- 경로 확인
- Git 동기화
- Commit 목록·상세·Diff
- 변경 이력 분석
- PPT 후보·분석 확인
- Cache 확인·삭제
- Evidence Link 검증
- 상태·장애 확인

UX 원칙:

- 장비 추가 화면을 과도하게 크게 만들지 않는다.
- 입력 예시는 입력창 내부 Placeholder에만 의존하지 않는다.
- 긴 작업은 진행 상태와 경과 시간을 표시한다.
- Tab 이동 후 작업 상태를 유지한다.
- 기본 기간은 전체 이력이다.
- 불필요한 정보는 접기·펼치기를 사용한다.

---

## 14. Ollama

### 14.1 역할

Ollama는 검색·연결 결과를 자연스럽게 설명하는 보조 기능이다.

```text
Git Search
→ PPT 후보
→ On-demand Parse
→ Evidence Link
→ 상위 근거
→ Ollama
```

### 14.2 금지

```text
전체 Git + 전체 PPT → LLM
```

### 14.3 응답 원칙

- 제공된 근거만 사용
- Git 변경 사실과 문서 사유를 구분
- 추론은 추정이라고 표시
- 확인 불가하면 확인 불가라고 답변
- Commit과 PPT File·Slide를 근거로 표시

Ollama 실패 시 Git·PPT 결과는 정상 반환한다.

---

## 15. Logging과 오류 처리

### 15.1 서버 로그

주요 이벤트:

- Application 시작
- DB 초기화
- 장비·Repository 변경
- Git Sync
- Trace Search
- PPT Candidate
- Cache Hit·Miss
- PPT Parse
- Evidence Link
- Ollama 요청·오류
- Extension/Continue 요청

### 15.2 로그 금지

- Full Diff
- PPT 전체 Text
- Slide 전체 Content
- 전체 AI Prompt
- 선택 코드 전체
- Password·Token·Credential
- 인증 Header

### 15.3 사용자 오류

Python Exception을 그대로 노출하지 않는다.

예:

```text
변경내역서 경로를 찾을 수 없습니다.
장비 관리에서 서버 경로와 접근 권한을 확인하십시오.
```

개별 PPT Parsing 실패는 전체 요청을 즉시 실패시키지 않는다.

---

## 16. API 계약

실제 Router와 Schema를 기준으로 유지한다. 아래는 현재 주요 역할이다.

```text
Health API
장비 목록·상세 API
Repository CRUD·Prepare·Sync API
Git Commit 목록·상세 API
Trace Search API
PPT Candidate·Analysis API
Extension 분석 API: POST /api/continue/trace
```

정책:

- Extension의 분석 계약을 변경할 때 하위 호환 또는 명확한 Migration을 제공한다.
- `equipment_id`, `file_path`, `selected_code`, `detected_symbol`, `use_ollama` 등 실제 Request Schema를 코드와 문서에서 일치시킨다.
- 내부 Debug 필드는 사용자 Output에 기본 표시하지 않는다.
- API 200 응답 속 Markdown 오류와 HTTP 오류 정책을 일관되게 관리한다.

---

## 17. 테스트 전략

### 17.1 Unit Test

- Git 경로·URL 정규화
- Git log·Diff Parsing
- Symbol 정규화
- 최초 추가 Parent 검증
- PPT 날짜·Keyword 후보 점수
- SHA-256 Cache
- PPT Text·Table·Group 추출
- PPT 소스·함수 분리
- Evidence Link Score
- lifecycle 단계 분류
- 공식 문서 Identity·집계
- Ollama 응답 Parsing
- Extension 설정·Output

### 17.2 Integration Test

- 장비·Repository CRUD
- Remote Clone·Fetch
- Git Sync
- Trace Search
- 함수 lifecycle
- PPT 후보·On-demand Parse
- Cache 재사용
- Git-PPT 연결
- Extension 분석 요청
- Ollama Mock 또는 내부 API

### 17.3 운영 데이터 회귀 테스트

실제 변경 건 10~20개 정답 Set을 관리한다.

```text
함수 또는 Symbol
관련 Commit
관련 PPT
관련 Slide
기능 단계
예상 연결 유형
```

평가:

```text
Top 1
Top 3
Top 5
Lifecycle 단계 정확성
공식 문서 수·참조 일관성
오탐 연결 여부
```

### 17.4 필수 최신 회귀 조건

1. 초기 적용 문서와 후속 삭제 문서를 별도 단계로 배치한다.
2. 후속 문서를 초기 Commit 전체에 복제하지 않는다.
3. 적용 Commit과 삭제 문서를 직접 연결하지 않는다.
4. Diff 미확보는 Commit 직접 근거가 아니다.
5. 단계 공식 문서는 Commit 연결 실패 시에도 유지된다.
6. 본문 모든 문서는 참조 근거와 집계에 포함된다.
7. 공식 문서 unique 집계가 Commit 수에 따라 중복되지 않는다.
8. 관련 소스와 Symbol을 분리한다.
9. 경로 조각을 함수명으로 만들지 않는다.
10. Output 개선 완료 후 기본 모드에 Debug Payload가 없어야 한다.
11. Continue 문구 기능 완료 후 config 자동 수정이 없어야 한다.
12. 일반 검색과 non-symbol 질문이 회귀하지 않는다.

---

## 18. 산출물

기능 수정 시 다음을 함께 갱신한다.

```text
프로젝트 소스
산출물 폴더
산출물/서버PC 또는 package-deploy
산출물/운영PC VSIX
Extension 사용자 가이드
README
TEST_PLAN 또는 테스트 결과
PROJECT_SPEC v2.1 — 설계 정책 변경 시
```

완료 보고:

- 정확한 원인
- 변경 파일
- 핵심 구현
- 사용자 동작 변화
- 테스트
- 실패·수정·재테스트
- Backend·Frontend·Extension 결과
- VSIX 버전·패키징
- 서버PC·운영PC 산출물 반영
- 명세 반영 여부
- 현재 제한

---

## 19. STEP 상태

### STEP 0 — 기본 실행 환경

**완료**

- FastAPI
- SQLite
- React·Vite
- Health
- Logging
- Offline 고려

### STEP 1 — 장비·Repository 관리

**완료**

- 장비 CRUD
- Repository 1:N
- Yona Remote·Local
- UNC 변경내역서 경로
- Repository Prepare
- 경로·접근 검증

### STEP 2 — Git 변경 이력 수집

**완료**

- Commit·Diff 수집
- 증분 Sync
- Rename·Binary 기본 처리
- Repository별 Commit Identity

### STEP 3 — Git 변경 이력 조회

**완료**

- 검색·필터·Pagination
- Commit 상세·파일 Diff
- Web UI

### STEP 4 — Trace Search

**완료**

- 규칙 기반 Git Candidate
- Keyword·Symbol
- Search Context
- Ollama 비의존

### STEP 5 — PPT 후보 탐색

**완료**

- 재귀 `.pptx`
- 날짜·Keyword 후보
- Candidate Limit

### STEP 6 — PPT On-demand·Cache

**완료**

- 상위 후보 Parse
- SHA-256 Cache
- Slide·Table·Group
- Cache 재사용

### STEP 7 — Git-PPT Evidence Link

**완료**

- 규칙 기반 Score
- 근거 이유
- Top N
- lifecycle 연결은 정확도 개선 중

### STEP 8 — Ollama 보조 분석

**완료**

- 근거 기반 요약
- 장애 분리
- JSON·Fallback

### STEP 9 — Source Trace VS Code Extension

**완료·개선 중**

완료:

- 선택 코드·함수 질의
- 서버·장비 최초 설정
- 분석 API 호출
- Markdown 결과
- Output 진행 상태
- Continue config 삽입 문구 생성·복사(명령: `Source Trace: Continue 설정 스니펫 생성`,
  자동 설정 파일 수정 없음)

개선 중·후속:

- lifecycle PPT 정확도와 집계
- Output Debug 분리
- README 최신화

### STEP 10 — 공식 운영환경 종합 검증

**미착수**

현재 배포 산출물 구성과 내부 테스트는 계속 수행할 수 있으나, STEP 10 공식 종합 검증은 별도 승인 후 시작한다.

---

## 20. 금지 사항

- Git·PPT 경로 하드코딩
- 특정 서버 IP·Port 전역 기본값
- `equipment_id=1` 기본값
- 외부 Cloud AI API
- CDN
- Runtime Package 자동 다운로드
- 전체 Repository·PPT를 LLM에 전달
- 모든 PPT 사전 Parsing
- 전체 변경내역서 동기화 버튼
- 초기 Vector DB
- Docker 필수화
- 불필요한 Microservice
- Ollama 장애로 전체 기능 중단
- AI 결과만 표시하고 Evidence 숨김
- 특정 함수·Commit·PPT 파일명 예외 분기
- 후속 문서를 초기 lifecycle 전체에 복제
- Diff 미확보 직접 근거
- 마지막 문서 제목으로 대표 기능명 덮어쓰기
- 경로 토큰을 함수로 출력
- Continue config 자동 수정
- README에 STEP·MVP·POC 데모 이력 노출
- 사용자 Output에 Raw Debug Payload 기본 노출

---

## 21. 최종 대표 시나리오

### 21.1 관리자

```text
장비: 휴대용정산기
Git Repository: 장비별 복수 등록 가능
변경내역서: \\문서서버\공유폴더\휴대용정산기
```

- Repository 준비
- Git Sync
- PPT 경로 확인

### 21.2 개발자

VS Code에서 함수를 선택하고 변경 이력을 조회한다.

### 21.3 Backend

```text
대상 장비·Repository 확인
→ 전체 함수 Git lifecycle
→ 최초 추가·핵심 변경·보조 변경·후속 유지보수 분류
→ PPT 후보 탐색
→ 필요한 PPT만 Parse·Cache
→ 초기 공식 적용 문서와 후속 유지보수 문서 분리
→ Commit별 근거 수준 결정
→ Markdown 생성
```

### 21.4 결과

```text
한눈에 보기
- 주요 기능
- 최초 개발
- 공식 적용 문서
- 후속 유지보수
- 공식 문서 수
- 신뢰도

최초 개발 및 기능 확정
- 최초 추가
- 핵심 변경
- 공식 적용 문서

개발 및 보조 변경
- 로그·테스트·주석

후속 유지보수
- 후속 로직 변경
- 후속 공식 문서

참조 근거
- Git Commit
- PPT File·Slide
```

### 21.5 장애

- Ollama 중단: Git·PPT 결과 정상
- 일부 PPT Parse 실패: 다른 근거 계속
- 장비 미선택: 설정 흐름 안내
- 잘못된 장비: 자동 fallback 금지

---

## 22. Cursor 작업 원칙

Cursor는 작업 시작 시 다음을 확인한다.

```text
PROJECT_SPEC v2.1
현재 코드
실제 DB Schema
실제 package.json
기존 테스트
TEST_PLAN
배포 산출물 가이드
```

원칙:

1. 완료된 STEP 0~9를 임의 재작성하지 않는다.
2. 원인 해결에 필요한 최소 범위를 수정한다.
3. 구현 완료와 승인된 후속 요구를 구분한다.
4. 실제로 존재하지 않는 설정·명령·버전을 문서에 완료 기능으로 기록하지 않는다.
5. 수정 내용을 산출물 폴더에 반영한다.
6. STEP 10은 승인 없이 시작하지 않는다.

완료 보고 형식:

```text
1. 원인
2. 구현한 기능
3. 생성·수정 파일
4. 핵심 방식
5. 테스트
6. 실패 및 재테스트
7. 사용자 동작 변화
8. 제한 사항
9. 산출물 반영
10. 다음 작업 전 확인 사항
```

---

## 23. 다음 우선 작업

1. lifecycle 단계 공식 문서와 Commit별 문서 연결을 분리하여 최신 운영 사례 재검증
2. 공식 문서 unique 집계와 본문·참조·Output 통계 일치
3. PPT 관련 소스·함수 파싱 오류 제거
4. Extension 기본 Output에서 Debug Payload 제거
5. 필요 시 `sourceTrace.diagnosticLogging` 구현
6. README와 운영PC 가이드 갱신
7. 변경 후 전체 회귀 테스트와 VSIX 재패키징
8. STEP 10(공식 운영환경 종합 검증)은 별도 승인 대기

완료(2026-08-03): 서버·장비 설정값 기반 Continue config 삽입 문구 생성 —
`Source Trace: Continue 설정 스니펫 생성` 명령. Continue 설정 파일 자동 수정 없음.
