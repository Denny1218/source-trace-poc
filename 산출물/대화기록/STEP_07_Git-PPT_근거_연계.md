# STEP 7. Git-PPT 근거 연계

> **범위**: Cursor 메인 개발 대화 turn **#48 ~ #65** （14턴）
> **이 STEP 요지**: Git Candidate ↔ Change Item Evidence Link

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #48 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트 기준 명세 파일로…
2. 메인 #49 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트 기준 명세 파일로…
3. 메인 #51 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
4. 메인 #52 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
5. 메인 #53 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
6. 메인 #54 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
7. 메인 #55 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
8. 메인 #57 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
9. 메인 #60 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
10. 메인 #61 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
11. 메인 #62 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
12. 메인 #63 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
13. 메인 #64 — STEP 8은 아직 진행하지 마. Evidence Link 검증 화면 테스트 결과 Query Intent 분류가 전보다 좋아졌지…
14. 메인 #65 — STEP 8은 아직 진행하지 마. Evidence Query Intent 테스트 결과가 전반적으로 좋아졌지만, `file_clo…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #48  |  Friday, Jul 10, 2026, 5:50 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트 기준 명세 파일로 사용해.

기존 `PROJECT_SPEC.md` 또는 이전 명세와 충돌하면 v2 명세를 우선 적용해.

이제 STEP 7을 진행해.

# STEP 7
Git 변경 이력과 프로그램 변경내역 Change Item 간 Evidence Link 생성

중요:

STEP 6 운영환경 테스트와 보완 작업은 완료되었다.

운영환경에서 다음을 확인했다.

- Change Item Parser 정상 동작
- Header Label 기반 구조 분석 정상 동작
- Progressive Fallback 정상 동작
- 최초 내부 Keyword 검색 누락 문제 해결 확인
- `영수증` 최초 검색 정상
- `15분` 검색 정상
- Change Item 중심 분석 화면 정상
- 관련도 높음/보통/낮음 표시 정상
- 추가 탐색 Count는 메인 Summary에서 제거하고 분석 상태 상세에만 유지
- 출처 영역의 `폴더 경로 복사` 정상 동작
- HTTP 환경 Clipboard Compatibility Fallback 정상 동작

STEP 6 기능을 불필요하게 다시 수정하지 마.

이번 STEP 7의 목적은:

`Git Commit 후보와 Change Item 후보를 규칙 기반으로 연결하고, 향후 Ollama가 사용할 Evidence Set을 생성하는 것`

이다.

아직 STEP 8 Ollama 분석은 진행하지 마.

아직 VSCode Continue 연동도 진행하지 마.

---

# 1. STEP 7 목표 흐름

현재 흐름:

사용자 Query
→ `/api/trace/search`
→ Git Candidate Top 5

현재 PPT 흐름:

Query / Search Context
→ PPT Candidate
→ Slide Cache
→ Change Item Parser
→ Change Item Cache
→ Change Item Search

STEP 7에서는 다음 흐름을 추가해.

User Query
→ Git Candidate Top 5
→ Change Item Candidate Search
→ Git Candidate × Change Item Candidate Link Score 계산
→ Evidence Link 후보 생성
→ 상위 Evidence Set 반환

개념:

Git Commit A
+
Change Item 1
→ Link Score 92

Git Commit A
+
Change Item 2
→ Link Score 35

Git Commit B
+
Change Item 1
→ Link Score 74

최종:

Evidence Link Top N

아직 LLM Summary를 생성하지 않는다.

---

# 2. 핵심 원칙

STEP 7 Link Score는 Rule-based / Explainable 방식으로 구현해.

금지:

- Embedding
- Vector DB
- ML Model
- LLM Link 판단
- Ollama Link 판단
- Fuzzy AI Matching
- 전체 Repository LLM 전달
- 전체 PPT Text LLM 전달

각 Link Score는 왜 연결되었는지 설명 가능해야 한다.

각 Evidence Link는 반드시 `match_reasons` 또는 동일 의미의 구조를 가져야 한다.

예:

[
  "same_file: fare_calc.c",
  "same_function: fare_check_reent_valid_troa",
  "keyword_match: 재승차",
  "date_distance_days: 3"
]

점수만 반환하지 마.

---

# 3. Git Candidate 입력 재사용

STEP 4의 기존 Git Candidate 검색을 재사용해.

현재 `/api/trace/search` 또는 내부 Service에서 생성하는 Git Top 5 Candidate 결과 구조를 확인해.

가능한 기존 정보:

- commit id
- commit hash
- commit date
- author
- message
- file path
- diff
- score
- match reasons
- search context

기존 Git Candidate Score Algorithm을 변경하지 마.

STEP 7 Link Score는 Git Candidate 자체 Score와 별도의 점수다.

혼합하지 마.

예:

git_candidate_score = 80

link_score = 95

각 의미를 분리해.

---

# 4. Change Item Candidate 입력

STEP 6의 `change_item_cache`와 Change Item Search Service를 재사용해.

Change Item Candidate에서 최소 다음 정보를 사용할 수 있어야 한다.

- document_cache_id
- document path 또는 document identity
- slide_no
- item_no
- change_title
- csr_no
- business_background
- current_status
- as_is
- to_be
- source_functions
- test_cases
- applicable_scopes
- raw_text
- parser_version

기존 Change Item Search Score는 유지해.

STEP 7 Link Score와 분리해.

예:

change_item_search_score = 140

link_score = 90

---

# 5. Evidence Link의 기본 단위

Evidence Link의 기본 단위는:

`1 Git Commit Candidate ↔ 1 Change Item`

이다.

한 Link는 다음을 식별할 수 있어야 한다.

Git:

- git_commit.id
- repository_id
- commit_hash

Change Item:

- change_item_cache.id
- document_cache_id
- slide_no

동일 Change Title이라고 자동 Dedup하지 마.

서로 다른 Document / Slide / Source Evidence면 별도 Link로 유지해.

---

# 6. Link Score 설계

초기 Link Score는 단순하고 설명 가능한 Rule 기반으로 구현해.

다음 Evidence를 우선 검토해.

## A. Source File Match

Git Change의 file_path와 Change Item의 source_functions.file_path 비교.

가장 중요한 Evidence 중 하나다.

매칭 단계 예시:

1. normalized full path exact
2. normalized path suffix match
3. basename exact match

예:

Git:

`src/fare/fare_calc.c`

Change Item:

`subwaylib/fare/src/fare_calc.c`

Full Path는 다르지만 basename:

`fare_calc.c`

동일.

또는 Path suffix:

`fare/src/fare_calc.c`

동일.

주의:

단순 substring:

`fare`

같은 방식으로 File Match 처리하지 마.

File extension 포함한 File Identity 중심.

Windows/Unix Separator 차이 고려:

`\`
`/`

Case normalization 정책을 명시해.

Git Repository 운영 환경 특성상 path는 일반적으로 case-sensitive 가능성이 있으나 현재 검색/내부 운영 정책에 맞는 비교 전략을 결정해.

비교용 normalized value와 원본 값은 분리해.

---

## B. Function / Symbol Match

Git Diff 또는 Search Context의 Symbol과 Change Item source_functions.functions 비교.

예:

Git Diff:

`fare_check_reent_valid_troa`

Change Item:

`fare_check_reent_valid_troa()`

동일 Symbol로 인식 가능해야 한다.

Normalization 검토:

- trailing `()`
- whitespace
- pointer/reference 표현
- C/C++ common identifier form

과도한 C++ Parser를 만들지 마.

Initial Rule 기반 Identifier Normalization만 적용해.

예:

`fare_check_reent_valid_troa()`
→ `fare_check_reent_valid_troa`

Symbol exact normalized match를 강한 Evidence로 사용.

단순 substring만으로 Function Match를 강한 점수로 처리하지 마.

---

## C. Commit Message ↔ Change Item Keyword Match

Git Commit Message와 다음 Change Item Field 비교.

우선:

- change_title
- business_background
- current_status
- as_is
- to_be

기존 Keyword Extraction / Normalization Utility를 재사용할 수 있는지 확인해.

STEP 4의 Keyword Extraction과 STEP 6의 Change Item Keyword Search가 있다.

동일 기능을 새로 중복 구현하기 전에 기존 Utility를 확인해.

한글 Keyword.
영문 Case-insensitive.
C/C++ Identifier.
UPPER_SNAKE_CASE.

Stopword/짧은 Token 정책은 기존 Search 정책과 최대한 일관되게 유지해.

---

## D. Diff ↔ Change Item Keyword Match

Git Diff와 Change Item Field의 Keyword Match.

다만 Diff는 매우 길 수 있다.

전체 Diff Text를 무제한 반복 비교하지 마.

기존 Git Candidate가 이미 Top 5로 축소되어 있으므로 해당 Candidate 범위에서만 수행.

필요하면 Diff Text 길이 Limit 또는 normalized token set을 사용해.

사용 Field:

- change_title
- current_status
- as_is
- to_be
- business_background
- source/function

Raw Text Match는 약한 Evidence로만 사용.

---

## E. Date Proximity

Git Commit Date와 Change Document / Change Item 관련 날짜의 근접성을 Evidence로 사용해.

중요:

PPT modified_at을 실제 변경일로 강하게 사용하지 마.

STEP 5에서 이미 확정한 정책:

`modified_at은 weak helper only`

를 유지해.

우선 날짜 Evidence:

1. Document Filename에서 파싱된 Date
2. 기존 PPT Metadata Candidate에서 사용하는 Filename/Folder Date Context
3. 필요한 경우 Git Search Context Date Range

Change Item 자체에 별도 Date Field가 없다면 임의 Date를 생성하지 마.

Commit Date ↔ Document Filename Date 차이 계산.

예:

0~7 days
8~30 days
31~90 days
90 days 초과

와 같은 Explainable Bucket 방식 검토.

정확한 Bucket/점수는 현재 실제 데이터 특성을 확인 후 결정해.

Date만 일치한다고 높은 Link Score가 나오면 안 된다.

Date Evidence는 보조 Evidence다.

---

## F. CSR Match

Git Commit Message 또는 Diff에 CSR 번호가 존재하고 Change Item `csr_no`와 동일하면 강한 Evidence로 사용해.

예:

Commit Message:

`SR260529_42025 반영`

Change Item:

`csr_no = SR260529_42025`

Exact normalized CSR Match.

현재 실제 문서 Sample 분석에서는 CSR Pattern이 다음과 유사했다.

`C20YYMMDD_NNN`

또는 운영 문서에서 SR 계열 등 다른 Prefix가 존재할 수 있다.

특정 `C` Prefix만 하드코딩하지 마.

현재 Change Item Parser가 추출한 csr_no 값을 기준으로 exact match를 우선 사용해.

CSR Pattern 탐색이 필요하면 Generic Identifier 형태로 처리하되 과도한 Regex 범용화를 하지 마.

---

# 7. Link Score 초기 방향

다음은 개념 예시다.

실제 현재 Score 체계와 운영 데이터 분포를 먼저 확인한 뒤 설명 가능한 값으로 결정해.

예시:

same_function_exact
+40

same_file_path_or_suffix
+35

same_file_basename
+25

csr_exact
+35

commit_message_keyword
+20

diff_keyword
+15

date_0_7_days
+15

date_8_30_days
+10

date_31_90_days
+5

raw_text_keyword
+5

중요:

이 점수값을 그대로 복사해서 하드코딩하지 마.

먼저 현재 실제 데이터 구조와 Candidate Score Distribution을 확인해.

그 후 Link Score Weight를 결정해.

Weight는 Config 또는 명확한 Constants로 분리해.

예:

LINK_SCORE_*

완료 보고에 Weight와 근거를 기록해.

---

# 8. Score Cap 여부

Link Score를 100점으로 Cap할지 검토해.

현재 사용자 UI에 Link Score 숫자를 바로 노출할 계획은 없다.

따라서 무조건 100점으로 맞출 필요는 없다.

다만 향후 STEP 8에서 Evidence Ranking에 사용하기 쉽도록 Score 의미가 일관되어야 한다.

두 방식 중 하나를 선택해.

A.
가중치 합산 Raw Score 유지

B.
100점 Cap

선택 이유를 완료 보고해.

현재 Change Item Search Score처럼 140 이상 점수가 가능하더라도 내부 Ranking Score라면 문제는 없다.

UI Percent처럼 오해될 표현은 하지 마.

---

# 9. match_reasons 구조

각 Link는 최소 다음 형태의 이유 정보를 제공해.

예시 개념:

{
  "type": "same_function",
  "score": 40,
  "git_value": "fare_check_reent_valid_troa",
  "change_item_value": "fare_check_reent_valid_troa"
}

{
  "type": "same_file_basename",
  "score": 25,
  "git_value": "src/fare/fare_calc.c",
  "change_item_value": "subwaylib/fare/src/fare_calc.c"
}

{
  "type": "date_proximity",
  "score": 10,
  "distance_days": 18
}

또는 현재 API Convention에 맞는 유사 구조.

단순 String Array도 가능하지만 향후 STEP 8 Evidence Prompt 구성과 Debug를 고려하면 Structured Reason을 우선 검토해.

중요:

Original internal document raw text를 match_reasons에 대량 복사하지 마.

Match에 필요한 최소 Evidence Value만 포함.

Diff 전체 Text 포함 금지.

---

# 10. change_link 저장 여부 검토

PROJECT SPEC v2와 기존 설계를 확인해.

STEP 7 원래 계획에 `change_link` 저장 구조가 있다면 구현해.

다만 먼저 현재 요구에 맞게 저장 필요성을 검토해.

Link 결과는 동일 Git/PPT Cache 상태에서는 반복 계산될 수 있다.

다음 질문을 기준으로 결정해.

- Link 계산 비용
- Git Commit 데이터의 안정성
- change_item_cache hash/parser_version invalidation
- Change Item 재생성 시 stale Link 가능성
- Repository Sync 이후 신규 Commit
- Score Rule Version 변경

저장한다면 `change_link` 테이블을 명확히 설계해.

권장 검토 Field:

- id
- git_commit_id
- change_item_cache_id
- link_score
- match_reasons_json
- linker_version
- created_at
- updated_at

Unique:

(git_commit_id, change_item_cache_id, linker_version)

또는 현재 정책에 맞는 구조.

중요:

`linker_version`을 검토해.

향후 Link Rule/Weight 변경 시 기존 Link 결과와 구분 가능해야 한다.

예:

`rule-v1`

저장 구조를 선택하면 stale invalidation 정책을 반드시 정의해.

Change Item 삭제:
→ link cascade delete

Git Commit 삭제:
→ link cascade delete

Parser Version 변경/Hash Change로 Change Item 재생성:
→ 기존 Change Item 삭제 Cascade로 Link 제거

Linker Version 변경:
→ 기존 Row를 즉시 전체 Migration/재계산하지 않아도 됨
→ 현재 Version 기준 lazy rebuild 가능

이번 STEP에서 전체 Git × 전체 Change Item 사전 Link 계산 금지.

On-demand 방식 유지.

---

# 11. On-demand Link 생성

전체 DB의 모든 Commit과 모든 Change Item을 Cartesian Product로 연결하지 마.

금지:

모든 Git Commit
×
모든 Change Item

사전 Link 계산.

현재 Query 기준:

Git Top 5 Candidate

×

관련 Change Item Candidate Top N

범위에서만 Link Score 계산.

Change Item Candidate N은 현재 Search Result Limit 또는 별도 Config로 관리해.

예시 Config:

`TRACE_CHANGE_ITEM_LINK_LIMIT`

정확한 Default는 현재 결과 규모를 확인하고 결정.

너무 큰 N 금지.

예:

Top 20 또는 Top 30 수준 검토.

완료 보고에 실제 Default와 이유 기록.

---

# 12. Evidence Link Result Limit

최종 Evidence Link는 Top N으로 제한해.

예:

Top 10

Config 예시:

`TRACE_EVIDENCE_LINK_LIMIT`

실제 기본값은 현재 데이터 구조를 확인 후 결정.

Sort:

1. link_score DESC
2. Git Candidate Rank
3. Change Item Search Score
4. deterministic tie breaker

동점 결과 순서가 요청마다 흔들리지 않게 해.

---

# 13. 최소 Link Threshold

모든 Cartesian Pair를 Evidence로 반환하지 마.

Link Score 0 또는 매우 약한 Pair는 제외해.

최소 Threshold를 정의해.

예:

`TRACE_LINK_MIN_SCORE`

Threshold 결정 시 다음을 확인해.

- file only match
- function exact match
- date only
- raw keyword only
- commit message keyword only
- multiple weak evidence combined

Date only Pair는 Evidence Link로 반환되지 않는 방향을 우선 검토해.

modified_at only Pair는 절대 Evidence Link가 되면 안 된다.

최소 하나 이상의 Primary Evidence가 필요한 Gate를 검토해.

Primary Evidence 예:

- file match
- function match
- CSR match
- strong keyword match

정확한 Gate 정책을 완료 보고에 기록해.

---

# 14. Primary Evidence Gate 권장

STEP 5의 PPT Candidate Primary Gate와 비슷한 철학을 적용해.

Link Score가 Date 또는 약한 Raw Text Match만으로 생성되지 않게 해.

권장 개념:

Primary Evidence:

- exact/suffix/basename file match
- normalized exact function match
- exact CSR match
- commit message ↔ change title strong keyword match
- diff ↔ source/function strong keyword match

Weak Evidence:

- date proximity
- raw_text keyword
- modified_at
- general context keyword

Primary Evidence가 하나도 없는 Pair는 Link 제외를 우선 검토해.

단 현재 실제 운영 데이터에서 Git Commit Message가 매우 빈약하고 Source/Function 문서화도 일부 누락될 수 있다.

그래서 구현 전 현재 데이터 특성을 확인하고 지나치게 엄격한 Gate가 실제 Link를 전부 제거하지 않는지 Test해.

필요하면:

Strong Evidence 1개

또는

Independent Weak Evidence 2~3개 조합

정책을 설계 가능.

단 Explainable해야 한다.

---

# 15. Evidence API

기존 `/api/trace/search`의 역할을 깨지 마.

현재 API를 그대로 확장할지 별도 API를 만들지 검토해.

권장:

`POST /api/trace/evidence`

Input 예시:

{
  "equipment_id": 1,
  "query": "fare_check_reent_valid_troa 함수가 왜 변경됐어?",
  "file_path": "subwaylib/fare/src/fare_calc.c",
  "selected_code": "optional"
}

Response 개념:

{
  "query": "...",
  "git_candidates": [...],
  "change_item_candidates": [...],
  "evidence_links": [
    {
      "git_candidate": {...},
      "change_item": {...},
      "link_score": 95,
      "match_reasons": [...]
    }
  ],
  "analysis_context": {
    ...
  }
}

단 Git Candidate / Change Item 전체 Object를 Link마다 중복하여 Payload가 과도하게 커지지 않게 설계해.

예:

git_candidates
change_items
evidence_links:
  git_candidate_id/reference
  change_item_id/reference

형태도 검토해.

API Payload를 읽기 쉽고 STEP 8에서 재사용하기 좋은 구조로 결정해.

기존 API Convention을 우선해.

---

# 16. Evidence Context

STEP 8 Ollama에 넘길 Evidence Context의 기반을 STEP 7에서 준비해.

아직 Ollama Prompt를 만들지 마.

Evidence Context에는 최소 다음 의미가 있어야 한다.

Query

Git Evidence:
- commit hash
- date
- message
- changed file
- relevant diff excerpt 또는 Match Context

Change Item Evidence:
- change title
- CSR
- business background
- current status
- As-Is
- To-Be
- source/function
- document filename
- slide number

Link:
- link score
- match reasons

중요:

전체 Diff를 그대로 Evidence Context에 넣지 마.

전체 raw_text를 그대로 넣지 마.

Evidence에 관련된 최소 Context Extract 정책을 검토해.

향후 STEP 8 Token 사용량 제어를 고려해.

다만 이번 STEP 7에서는 LLM Token 계산이나 Prompt 최적화까지 구현하지 마.

---

# 17. Relevant Diff Excerpt

Git Diff가 큰 경우 향후 Evidence 사용을 위해 관련 Diff Excerpt를 만들 수 있는지 검토해.

Query Keyword / Matched Function / Matched File 기준으로:

- Match Line
- 주변 ±N Lines

형태.

예:

matched line ±5 lines

단 이번 STEP에서 복잡한 Diff Parser를 새로 만들 필요는 없다.

현재 Git Candidate Service에 Diff Context 또는 selected code context가 이미 있다면 재사용해.

없다면 최소 Helper만 구현 가능.

전체 Diff 저장 구조는 변경하지 마.

Diff Excerpt는 계산 결과 또는 API Context 용.

기본 N은 Config 또는 Constant.

완료 보고에 정책 기록.

---

# 18. 날짜 정보 추출 재사용

STEP 5의 PPT Filename/Folder Date Parsing Logic을 재사용해.

Link Service에서 날짜 Regex를 새로 별도 구현하여 정책이 달라지지 않게 해.

현재 Candidate Service의 Date Extraction Utility가 Private Function이라 재사용이 어렵다면:

- 공통 Utility로 최소 Refactor

가능.

단 STEP 5 Score Algorithm 동작을 바꾸지 마.

Refactor 전/후 기존 Test 통과 확인.

---

# 19. Path Normalization Utility

Git ↔ Change Item Source Path Link를 위해 공통 Path Normalization Helper를 추가해.

예시 처리:

- `\` → `/`
- duplicate slash 정리
- leading `./` 제거
- trim
- basename 추출
- normalized suffix comparison

UNC Document Path용 Utility와 혼동하지 마.

Source Code Path Normalize Utility는 별도 책임.

예시:

normalize_source_path
source_path_match_level

Match Level 개념:

EXACT
SUFFIX
BASENAME
NONE

가능.

Case 정책을 명시하고 Test해.

---

# 20. Symbol Normalization Utility

Function/Symbol 비교 Helper.

예:

normalize_symbol

Input:

`fare_check_reent_valid_troa()`

Output:

`fare_check_reent_valid_troa`

Input:

` fare_check_reent_valid_troa `

Output:

`fare_check_reent_valid_troa`

C/C++ Identifier 형태 중심.

다음 수준의 전체 Parser는 금지.

- template parsing
- namespace AST parsing
- function signature parser

단순 Initial Rule.

Invalid / Free Text는 Function Exact Match 대상으로 사용하지 않게 해.

---

# 21. 테스트 Fixture

실제 내부 PPT 원문을 Test Fixture에 복사하지 마.

기존 원본 Sample PPTX를 Repository/Test Resource에 포함하지 마.

Synthetic Fixture만 사용.

Git Synthetic Data:

- commit message
- commit date
- changed file
- diff
- function name

Change Item Synthetic Data:

- change title
- CSR
- business background
- As-Is
- To-Be
- source/function
- document date

실제 회사명/내부 IP/실제 Repository URL/실제 CSR/실제 변경 문구 하드코딩 금지.

Generic Data 사용.

예:

`fare_calc.c`

`calculate_fare`

`C20250101_001`

정도의 가상 데이터.

---

# 22. 필수 Test Case

최소 다음 Test를 추가해.

## File Match

1. Full Path Exact
2. Separator 차이
3. Path Suffix Match
4. Basename Exact
5. Same basename with unrelated extension
6. Partial substring not match

## Symbol Match

7. Exact Symbol
8. trailing ()
9. whitespace
10. different symbol
11. substring only not strong match
12. invalid free text

## CSR

13. Exact CSR
14. Case normalization 정책
15. Different CSR
16. CSR 없음

## Date

17. Same day
18. 7 days
19. 30 days
20. 90 days
21. >90 days
22. Filename Date 없음
23. modified_at only

## Keyword

24. Commit message ↔ change title
25. Korean keyword
26. English case-insensitive
27. C identifier
28. Diff ↔ To-Be
29. Raw Text only weak match

## Gate

30. Date only → Link 제외
31. modified_at only → Link 제외
32. Strong File Evidence → Link 포함
33. Function Evidence → Link 포함
34. CSR Evidence → Link 포함
35. Multiple weak Evidence 조합 정책 Test

## Ranking

36. Function + File > File only
37. CSR + Keyword > Keyword only
38. Equal score deterministic ordering
39. Top N Limit
40. Min Threshold

## DB / Cache if change_link implemented

41. Unique Policy
42. Cascade Git Commit Delete
43. Cascade Change Item Delete
44. linker_version
45. Same Version Upsert/Reuse
46. New Version Lazy Rebuild

## API

47. Evidence API Normal Result
48. Git Candidate 없음
49. Change Item 없음
50. Link 없음
51. Invalid equipment
52. Empty Query
53. Ollama unavailable 영향 없음

---

# 23. 운영 테스트 관점

구현 완료 후 실제 내부 운영환경에서 다음을 확인할 예정이다.

Case A:

Function Name Query

예:
특정 함수가 왜 변경됐는지 질문

기대:
Git Candidate
+
해당 Source/Function이 기록된 Change Item
→ 높은 Link Ranking

Case B:

File Name Query

기대:
동일/유사 Source File Change Item 연결

Case C:

Business Keyword Query

기대:
Commit Message/Diff Keyword
+
Change Title/Background/To-Be
→ 관련 Link

Case D:

Date만 가까운 unrelated 문서

기대:
상위 Evidence로 나오지 않음

Case E:

동일 Change Title이 여러 Document에 존재

기대:
Source/Function/Scope/Date Evidence 차이에 따라 별도 Link 유지

---

# 24. Web UI 범위

이번 STEP 7에서 대규모 UI를 추가하지 마.

우선 Backend Evidence Link와 API 검증이 중심이다.

필요하면 Web UI에 별도 `Evidence Link 검증` 영역을 최소 추가할 수 있다.

다만 기존 메뉴:

- 시스템 상태
- 장비 관리
- 소스 변경 이력
- 변경내역서 분석

전체 구조를 다시 설계하지 마.

우선 API/Test로 검증 가능하면 UI 추가를 최소화해.

STEP 8과 STEP 9에서 최종 사용자 UX는 Continue 중심으로 갈 예정이다.

Web UI는 관리/검증 보조다.

---

# 25. 기존 기능 회귀 금지

다음은 반드시 유지해.

Equipment:
- 1:N Git Repository
- Metadata Save 분리
- Prepare 분리
- Existing Ready Repo Save 시 Git Network Command 0
- Yona Default Username 정책
- User URL Username 무시
- Password 미저장
- GIT_TERMINAL_PROMPT=0

Git:
- Incremental Sync
- Commit/Change 저장
- Commit List/Detail
- Diff

Trace:
- Git Top 5 Candidate
- 기존 Git Score
- Search Context

PPT:
- Metadata Candidate Search
- Progressive Fallback
- On-demand Parse
- SHA-256 Cache
- slide_cache
- change_item_cache
- parser_version
- Header Label 기반 Change Item Parser
- Change Item Search
- 관련도 UI
- 최초 내부 Keyword 검색

Frontend:
- Tab State 유지
- Tab 복귀 시 자동 Search 금지
- 완료 Toast 반복 금지
- Equipment Version Refresh
- Date Filter 정책
- Long-running Loading Panel
- 분석 상태 상세
- Cache Collapse
- 폴더 경로 복사
- Clipboard Compatibility Fallback

---

# 26. 이번 STEP에서 하지 않을 기능

- STEP 8 Ollama Answer
- LLM Prompt
- LLM Link 판단
- Embedding
- Vector DB
- Semantic Search Model
- Continue 연동
- MCP
- VSCode Extension 직접 개발
- OCR
- 전체 PPT Pre-parse
- 전체 Git × Change Item Link 사전 계산
- UI Dashboard 재설계
- AI Confidence Percentage

---

# 27. 구현 전 확인

코드 수정 전에 다음을 먼저 확인해.

1. 현재 Git Candidate Model/API 구조
2. Git Candidate 내부 Service
3. Current Git Score / match reason 구조
4. Change Item Model
5. change_item_cache Schema
6. Change Item Search Service
7. Change Item Search Score 구조
8. PPT Date Extraction Utility
9. Git Diff Context 구조
10. Search Context Keyword 구조
11. Existing DB Migration Pattern
12. Current API Router Convention
13. Current Config/Settings Pattern

기존 기능을 재사용할 수 있는 부분을 먼저 식별해.

중복 구현을 최소화해.

---

# 28. 완료 보고

완료 후 반드시 다음을 보고해.

1. STEP 7 최종 Architecture
2. Git Candidate 재사용 구조
3. Change Item Candidate 재사용 구조
4. Evidence Link 기본 단위
5. Link Score Weight 전체 목록
6. 각 Weight 선택 근거
7. Score Cap 여부
8. Primary Evidence 정의
9. Weak Evidence 정의
10. Primary Evidence Gate 정책
11. Min Link Threshold
12. File Match Level
13. Source Path Normalize 정책
14. Source Path Case 정책
15. Symbol Normalize 정책
16. Function Exact Match 정책
17. CSR Match 정책
18. Keyword Match 정책
19. Diff Match 정책
20. Date Evidence Source
21. Date Bucket/Weight
22. modified_at 처리 정책
23. match_reasons 최종 구조
24. change_link 저장 여부
25. change_link Schema
26. linker_version
27. Link Cache/Reuse 정책
28. Stale Link Invalidation 정책
29. On-demand Link 범위
30. Change Item Link Candidate Limit
31. Evidence Link Result Limit
32. Sort/Tie-break 정책
33. Evidence API Endpoint
34. Request Schema
35. Response Schema
36. Evidence Context 구조
37. Diff Excerpt 정책
38. 전체 Diff 미전달 확인
39. 전체 raw_text 미전달 확인
40. Synthetic Fixture 정책
41. 신규 Test 목록
42. 전체 Backend pytest 결과
43. Frontend 수정 여부
44. Frontend build 여부
45. 기존 STEP 1~6 회귀 확인
46. 구현 중 실패 이력
47. 실패 원인
48. 수정 내용
49. 재테스트 결과
50. STEP 8 미진행 확인

완료 후 STEP 8은 진행하지 말고 결과만 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_

### ◇ 진행 과정 요약（도구·짧은 안내만）

- _(도구 호출 없음)_

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [002]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #49  |  Friday, Jul 10, 2026, 5:50 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트 기준 명세 파일로 사용해.

기존 `PROJECT_SPEC.md` 또는 이전 명세와 충돌하면 v2 명세를 우선 적용해.

이제 STEP 7을 진행해.

# STEP 7
Git 변경 이력과 프로그램 변경내역 Change Item 간 Evidence Link 생성

중요:

STEP 6 운영환경 테스트와 보완 작업은 완료되었다.

운영환경에서 다음을 확인했다.

- Change Item Parser 정상 동작
- Header Label 기반 구조 분석 정상 동작
- Progressive Fallback 정상 동작
- 최초 내부 Keyword 검색 누락 문제 해결 확인
- `영수증` 최초 검색 정상
- `15분` 검색 정상
- Change Item 중심 분석 화면 정상
- 관련도 높음/보통/낮음 표시 정상
- 추가 탐색 Count는 메인 Summary에서 제거하고 분석 상태 상세에만 유지
- 출처 영역의 `폴더 경로 복사` 정상 동작
- HTTP 환경 Clipboard Compatibility Fallback 정상 동작

STEP 6 기능을 불필요하게 다시 수정하지 마.

이번 STEP 7의 목적은:

`Git Commit 후보와 Change Item 후보를 규칙 기반으로 연결하고, 향후 Ollama가 사용할 Evidence Set을 생성하는 것`

이다.

아직 STEP 8 Ollama 분석은 진행하지 마.

아직 VSCode Continue 연동도 진행하지 마.

---

# 1. STEP 7 목표 흐름

현재 흐름:

사용자 Query
→ `/api/trace/search`
→ Git Candidate Top 5

현재 PPT 흐름:

Query / Search Context
→ PPT Candidate
→ Slide Cache
→ Change Item Parser
→ Change Item Cache
→ Change Item Search

STEP 7에서는 다음 흐름을 추가해.

User Query
→ Git Candidate Top 5
→ Change Item Candidate Search
→ Git Candidate × Change Item Candidate Link Score 계산
→ Evidence Link 후보 생성
→ 상위 Evidence Set 반환

개념:

Git Commit A
+
Change Item 1
→ Link Score 92

Git Commit A
+
Change Item 2
→ Link Score 35

Git Commit B
+
Change Item 1
→ Link Score 74

최종:

Evidence Link Top N

아직 LLM Summary를 생성하지 않는다.

---

# 2. 핵심 원칙

STEP 7 Link Score는 Rule-based / Explainable 방식으로 구현해.

금지:

- Embedding
- Vector DB
- ML Model
- LLM Link 판단
- Ollama Link 판단
- Fuzzy AI Matching
- 전체 Repository LLM 전달
- 전체 PPT Text LLM 전달

각 Link Score는 왜 연결되었는지 설명 가능해야 한다.

각 Evidence Link는 반드시 `match_reasons` 또는 동일 의미의 구조를 가져야 한다.

예:

[
  "same_file: fare_calc.c",
  "same_function: fare_check_reent_valid_troa",
  "keyword_match: 재승차",
  "date_distance_days: 3"
]

점수만 반환하지 마.

---

# 3. Git Candidate 입력 재사용

STEP 4의 기존 Git Candidate 검색을 재사용해.

현재 `/api/trace/search` 또는 내부 Service에서 생성하는 Git Top 5 Candidate 결과 구조를 확인해.

가능한 기존 정보:

- commit id
- commit hash
- commit date
- author
- message
- file path
- diff
- score
- match reasons
- search context

기존 Git Candidate Score Algorithm을 변경하지 마.

STEP 7 Link Score는 Git Candidate 자체 Score와 별도의 점수다.

혼합하지 마.

예:

git_candidate_score = 80

link_score = 95

각 의미를 분리해.

---

# 4. Change Item Candidate 입력

STEP 6의 `change_item_cache`와 Change Item Search Service를 재사용해.

Change Item Candidate에서 최소 다음 정보를 사용할 수 있어야 한다.

- document_cache_id
- document path 또는 document identity
- slide_no
- item_no
- change_title
- csr_no
- business_background
- current_status
- as_is
- to_be
- source_functions
- test_cases
- applicable_scopes
- raw_text
- parser_version

기존 Change Item Search Score는 유지해.

STEP 7 Link Score와 분리해.

예:

change_item_search_score = 140

link_score = 90

---

# 5. Evidence Link의 기본 단위

Evidence Link의 기본 단위는:

`1 Git Commit Candidate ↔ 1 Change Item`

이다.

한 Link는 다음을 식별할 수 있어야 한다.

Git:

- git_commit.id
- repository_id
- commit_hash

Change Item:

- change_item_cache.id
- document_cache_id
- slide_no

동일 Change Title이라고 자동 Dedup하지 마.

서로 다른 Document / Slide / Source Evidence면 별도 Link로 유지해.

---

# 6. Link Score 설계

초기 Link Score는 단순하고 설명 가능한 Rule 기반으로 구현해.

다음 Evidence를 우선 검토해.

## A. Source File Match

Git Change의 file_path와 Change Item의 source_functions.file_path 비교.

가장 중요한 Evidence 중 하나다.

매칭 단계 예시:

1. normalized full path exact
2. normalized path suffix match
3. basename exact match

예:

Git:

`src/fare/fare_calc.c`

Change Item:

`subwaylib/fare/src/fare_calc.c`

Full Path는 다르지만 basename:

`fare_calc.c`

동일.

또는 Path suffix:

`fare/src/fare_calc.c`

동일.

주의:

단순 substring:

`fare`

같은 방식으로 File Match 처리하지 마.

File extension 포함한 File Identity 중심.

Windows/Unix Separator 차이 고려:

`\`
`/`

Case normalization 정책을 명시해.

Git Repository 운영 환경 특성상 path는 일반적으로 case-sensitive 가능성이 있으나 현재 검색/내부 운영 정책에 맞는 비교 전략을 결정해.

비교용 normalized value와 원본 값은 분리해.

---

## B. Function / Symbol Match

Git Diff 또는 Search Context의 Symbol과 Change Item source_functions.functions 비교.

예:

Git Diff:

`fare_check_reent_valid_troa`

Change Item:

`fare_check_reent_valid_troa()`

동일 Symbol로 인식 가능해야 한다.

Normalization 검토:

- trailing `()`
- whitespace
- pointer/reference 표현
- C/C++ common identifier form

과도한 C++ Parser를 만들지 마.

Initial Rule 기반 Identifier Normalization만 적용해.

예:

`fare_check_reent_valid_troa()`
→ `fare_check_reent_valid_troa`

Symbol exact normalized match를 강한 Evidence로 사용.

단순 substring만으로 Function Match를 강한 점수로 처리하지 마.

---

## C. Commit Message ↔ Change Item Keyword Match

Git Commit Message와 다음 Change Item Field 비교.

우선:

- change_title
- business_background
- current_status
- as_is
- to_be

기존 Keyword Extraction / Normalization Utility를 재사용할 수 있는지 확인해.

STEP 4의 Keyword Extraction과 STEP 6의 Change Item Keyword Search가 있다.

동일 기능을 새로 중복 구현하기 전에 기존 Utility를 확인해.

한글 Keyword.
영문 Case-insensitive.
C/C++ Identifier.
UPPER_SNAKE_CASE.

Stopword/짧은 Token 정책은 기존 Search 정책과 최대한 일관되게 유지해.

---

## D. Diff ↔ Change Item Keyword Match

Git Diff와 Change Item Field의 Keyword Match.

다만 Diff는 매우 길 수 있다.

전체 Diff Text를 무제한 반복 비교하지 마.

기존 Git Candidate가 이미 Top 5로 축소되어 있으므로 해당 Candidate 범위에서만 수행.

필요하면 Diff Text 길이 Limit 또는 normalized token set을 사용해.

사용 Field:

- change_title
- current_status
- as_is
- to_be
- business_background
- source/function

Raw Text Match는 약한 Evidence로만 사용.

---

## E. Date Proximity

Git Commit Date와 Change Document / Change Item 관련 날짜의 근접성을 Evidence로 사용해.

중요:

PPT modified_at을 실제 변경일로 강하게 사용하지 마.

STEP 5에서 이미 확정한 정책:

`modified_at은 weak helper only`

를 유지해.

우선 날짜 Evidence:

1. Document Filename에서 파싱된 Date
2. 기존 PPT Metadata Candidate에서 사용하는 Filename/Folder Date Context
3. 필요한 경우 Git Search Context Date Range

Change Item 자체에 별도 Date Field가 없다면 임의 Date를 생성하지 마.

Commit Date ↔ Document Filename Date 차이 계산.

예:

0~7 days
8~30 days
31~90 days
90 days 초과

와 같은 Explainable Bucket 방식 검토.

정확한 Bucket/점수는 현재 실제 데이터 특성을 확인 후 결정해.

Date만 일치한다고 높은 Link Score가 나오면 안 된다.

Date Evidence는 보조 Evidence다.

---

## F. CSR Match

Git Commit Message 또는 Diff에 CSR 번호가 존재하고 Change Item `csr_no`와 동일하면 강한 Evidence로 사용해.

예:

Commit Message:

`SR260529_42025 반영`

Change Item:

`csr_no = SR260529_42025`

Exact normalized CSR Match.

현재 실제 문서 Sample 분석에서는 CSR Pattern이 다음과 유사했다.

`C20YYMMDD_NNN`

또는 운영 문서에서 SR 계열 등 다른 Prefix가 존재할 수 있다.

특정 `C` Prefix만 하드코딩하지 마.

현재 Change Item Parser가 추출한 csr_no 값을 기준으로 exact match를 우선 사용해.

CSR Pattern 탐색이 필요하면 Generic Identifier 형태로 처리하되 과도한 Regex 범용화를 하지 마.

---

# 7. Link Score 초기 방향

다음은 개념 예시다.

실제 현재 Score 체계와 운영 데이터 분포를 먼저 확인한 뒤 설명 가능한 값으로 결정해.

예시:

same_function_exact
+40

same_file_path_or_suffix
+35

same_file_basename
+25

csr_exact
+35

commit_message_keyword
+20

diff_keyword
+15

date_0_7_days
+15

date_8_30_days
+10

date_31_90_days
+5

raw_text_keyword
+5

중요:

이 점수값을 그대로 복사해서 하드코딩하지 마.

먼저 현재 실제 데이터 구조와 Candidate Score Distribution을 확인해.

그 후 Link Score Weight를 결정해.

Weight는 Config 또는 명확한 Constants로 분리해.

예:

LINK_SCORE_*

완료 보고에 Weight와 근거를 기록해.

---

# 8. Score Cap 여부

Link Score를 100점으로 Cap할지 검토해.

현재 사용자 UI에 Link Score 숫자를 바로 노출할 계획은 없다.

따라서 무조건 100점으로 맞출 필요는 없다.

다만 향후 STEP 8에서 Evidence Ranking에 사용하기 쉽도록 Score 의미가 일관되어야 한다.

두 방식 중 하나를 선택해.

A.
가중치 합산 Raw Score 유지

B.
100점 Cap

선택 이유를 완료 보고해.

현재 Change Item Search Score처럼 140 이상 점수가 가능하더라도 내부 Ranking Score라면 문제는 없다.

UI Percent처럼 오해될 표현은 하지 마.

---

# 9. match_reasons 구조

각 Link는 최소 다음 형태의 이유 정보를 제공해.

예시 개념:

{
  "type": "same_function",
  "score": 40,
  "git_value": "fare_check_reent_valid_troa",
  "change_item_value": "fare_check_reent_valid_troa"
}

{
  "type": "same_file_basename",
  "score": 25,
  "git_value": "src/fare/fare_calc.c",
  "change_item_value": "subwaylib/fare/src/fare_calc.c"
}

{
  "type": "date_proximity",
  "score": 10,
  "distance_days": 18
}

또는 현재 API Convention에 맞는 유사 구조.

단순 String Array도 가능하지만 향후 STEP 8 Evidence Prompt 구성과 Debug를 고려하면 Structured Reason을 우선 검토해.

중요:

Original internal document raw text를 match_reasons에 대량 복사하지 마.

Match에 필요한 최소 Evidence Value만 포함.

Diff 전체 Text 포함 금지.

---

# 10. change_link 저장 여부 검토

PROJECT SPEC v2와 기존 설계를 확인해.

STEP 7 원래 계획에 `change_link` 저장 구조가 있다면 구현해.

다만 먼저 현재 요구에 맞게 저장 필요성을 검토해.

Link 결과는 동일 Git/PPT Cache 상태에서는 반복 계산될 수 있다.

다음 질문을 기준으로 결정해.

- Link 계산 비용
- Git Commit 데이터의 안정성
- change_item_cache hash/parser_version invalidation
- Change Item 재생성 시 stale Link 가능성
- Repository Sync 이후 신규 Commit
- Score Rule Version 변경

저장한다면 `change_link` 테이블을 명확히 설계해.

권장 검토 Field:

- id
- git_commit_id
- change_item_cache_id
- link_score
- match_reasons_json
- linker_version
- created_at
- updated_at

Unique:

(git_commit_id, change_item_cache_id, linker_version)

또는 현재 정책에 맞는 구조.

중요:

`linker_version`을 검토해.

향후 Link Rule/Weight 변경 시 기존 Link 결과와 구분 가능해야 한다.

예:

`rule-v1`

저장 구조를 선택하면 stale invalidation 정책을 반드시 정의해.

Change Item 삭제:
→ link cascade delete

Git Commit 삭제:
→ link cascade delete

Parser Version 변경/Hash Change로 Change Item 재생성:
→ 기존 Change Item 삭제 Cascade로 Link 제거

Linker Version 변경:
→ 기존 Row를 즉시 전체 Migration/재계산하지 않아도 됨
→ 현재 Version 기준 lazy rebuild 가능

이번 STEP에서 전체 Git × 전체 Change Item 사전 Link 계산 금지.

On-demand 방식 유지.

---

# 11. On-demand Link 생성

전체 DB의 모든 Commit과 모든 Change Item을 Cartesian Product로 연결하지 마.

금지:

모든 Git Commit
×
모든 Change Item

사전 Link 계산.

현재 Query 기준:

Git Top 5 Candidate

×

관련 Change Item Candidate Top N

범위에서만 Link Score 계산.

Change Item Candidate N은 현재 Search Result Limit 또는 별도 Config로 관리해.

예시 Config:

`TRACE_CHANGE_ITEM_LINK_LIMIT`

정확한 Default는 현재 결과 규모를 확인하고 결정.

너무 큰 N 금지.

예:

Top 20 또는 Top 30 수준 검토.

완료 보고에 실제 Default와 이유 기록.

---

# 12. Evidence Link Result Limit

최종 Evidence Link는 Top N으로 제한해.

예:

Top 10

Config 예시:

`TRACE_EVIDENCE_LINK_LIMIT`

실제 기본값은 현재 데이터 구조를 확인 후 결정.

Sort:

1. link_score DESC
2. Git Candidate Rank
3. Change Item Search Score
4. deterministic tie breaker

동점 결과 순서가 요청마다 흔들리지 않게 해.

---

# 13. 최소 Link Threshold

모든 Cartesian Pair를 Evidence로 반환하지 마.

Link Score 0 또는 매우 약한 Pair는 제외해.

최소 Threshold를 정의해.

예:

`TRACE_LINK_MIN_SCORE`

Threshold 결정 시 다음을 확인해.

- file only match
- function exact match
- date only
- raw keyword only
- commit message keyword only
- multiple weak evidence combined

Date only Pair는 Evidence Link로 반환되지 않는 방향을 우선 검토해.

modified_at only Pair는 절대 Evidence Link가 되면 안 된다.

최소 하나 이상의 Primary Evidence가 필요한 Gate를 검토해.

Primary Evidence 예:

- file match
- function match
- CSR match
- strong keyword match

정확한 Gate 정책을 완료 보고에 기록해.

---

# 14. Primary Evidence Gate 권장

STEP 5의 PPT Candidate Primary Gate와 비슷한 철학을 적용해.

Link Score가 Date 또는 약한 Raw Text Match만으로 생성되지 않게 해.

권장 개념:

Primary Evidence:

- exact/suffix/basename file match
- normalized exact function match
- exact CSR match
- commit message ↔ change title strong keyword match
- diff ↔ source/function strong keyword match

Weak Evidence:

- date proximity
- raw_text keyword
- modified_at
- general context keyword

Primary Evidence가 하나도 없는 Pair는 Link 제외를 우선 검토해.

단 현재 실제 운영 데이터에서 Git Commit Message가 매우 빈약하고 Source/Function 문서화도 일부 누락될 수 있다.

그래서 구현 전 현재 데이터 특성을 확인하고 지나치게 엄격한 Gate가 실제 Link를 전부 제거하지 않는지 Test해.

필요하면:

Strong Evidence 1개

또는

Independent Weak Evidence 2~3개 조합

정책을 설계 가능.

단 Explainable해야 한다.

---

# 15. Evidence API

기존 `/api/trace/search`의 역할을 깨지 마.

현재 API를 그대로 확장할지 별도 API를 만들지 검토해.

권장:

`POST /api/trace/evidence`

Input 예시:

{
  "equipment_id": 1,
  "query": "fare_check_reent_valid_troa 함수가 왜 변경됐어?",
  "file_path": "subwaylib/fare/src/fare_calc.c",
  "selected_code": "optional"
}

Response 개념:

{
  "query": "...",
  "git_candidates": [...],
  "change_item_candidates": [...],
  "evidence_links": [
    {
      "git_candidate": {...},
      "change_item": {...},
      "link_score": 95,
      "match_reasons": [...]
    }
  ],
  "analysis_context": {
    ...
  }
}

단 Git Candidate / Change Item 전체 Object를 Link마다 중복하여 Payload가 과도하게 커지지 않게 설계해.

예:

git_candidates
change_items
evidence_links:
  git_candidate_id/reference
  change_item_id/reference

형태도 검토해.

API Payload를 읽기 쉽고 STEP 8에서 재사용하기 좋은 구조로 결정해.

기존 API Convention을 우선해.

---

# 16. Evidence Context

STEP 8 Ollama에 넘길 Evidence Context의 기반을 STEP 7에서 준비해.

아직 Ollama Prompt를 만들지 마.

Evidence Context에는 최소 다음 의미가 있어야 한다.

Query

Git Evidence:
- commit hash
- date
- message
- changed file
- relevant diff excerpt 또는 Match Context

Change Item Evidence:
- change title
- CSR
- business background
- current status
- As-Is
- To-Be
- source/function
- document filename
- slide number

Link:
- link score
- match reasons

중요:

전체 Diff를 그대로 Evidence Context에 넣지 마.

전체 raw_text를 그대로 넣지 마.

Evidence에 관련된 최소 Context Extract 정책을 검토해.

향후 STEP 8 Token 사용량 제어를 고려해.

다만 이번 STEP 7에서는 LLM Token 계산이나 Prompt 최적화까지 구현하지 마.

---

# 17. Relevant Diff Excerpt

Git Diff가 큰 경우 향후 Evidence 사용을 위해 관련 Diff Excerpt를 만들 수 있는지 검토해.

Query Keyword / Matched Function / Matched File 기준으로:

- Match Line
- 주변 ±N Lines

형태.

예:

matched line ±5 lines

단 이번 STEP에서 복잡한 Diff Parser를 새로 만들 필요는 없다.

현재 Git Candidate Service에 Diff Context 또는 selected code context가 이미 있다면 재사용해.

없다면 최소 Helper만 구현 가능.

전체 Diff 저장 구조는 변경하지 마.

Diff Excerpt는 계산 결과 또는 API Context 용.

기본 N은 Config 또는 Constant.

완료 보고에 정책 기록.

---

# 18. 날짜 정보 추출 재사용

STEP 5의 PPT Filename/Folder Date Parsing Logic을 재사용해.

Link Service에서 날짜 Regex를 새로 별도 구현하여 정책이 달라지지 않게 해.

현재 Candidate Service의 Date Extraction Utility가 Private Function이라 재사용이 어렵다면:

- 공통 Utility로 최소 Refactor

가능.

단 STEP 5 Score Algorithm 동작을 바꾸지 마.

Refactor 전/후 기존 Test 통과 확인.

---

# 19. Path Normalization Utility

Git ↔ Change Item Source Path Link를 위해 공통 Path Normalization Helper를 추가해.

예시 처리:

- `\` → `/`
- duplicate slash 정리
- leading `./` 제거
- trim
- basename 추출
- normalized suffix comparison

UNC Document Path용 Utility와 혼동하지 마.

Source Code Path Normalize Utility는 별도 책임.

예시:

normalize_source_path
source_path_match_level

Match Level 개념:

EXACT
SUFFIX
BASENAME
NONE

가능.

Case 정책을 명시하고 Test해.

---

# 20. Symbol Normalization Utility

Function/Symbol 비교 Helper.

예:

normalize_symbol

Input:

`fare_check_reent_valid_troa()`

Output:

`fare_check_reent_valid_troa`

Input:

` fare_check_reent_valid_troa `

Output:

`fare_check_reent_valid_troa`

C/C++ Identifier 형태 중심.

다음 수준의 전체 Parser는 금지.

- template parsing
- namespace AST parsing
- function signature parser

단순 Initial Rule.

Invalid / Free Text는 Function Exact Match 대상으로 사용하지 않게 해.

---

# 21. 테스트 Fixture

실제 내부 PPT 원문을 Test Fixture에 복사하지 마.

기존 원본 Sample PPTX를 Repository/Test Resource에 포함하지 마.

Synthetic Fixture만 사용.

Git Synthetic Data:

- commit message
- commit date
- changed file
- diff
- function name

Change Item Synthetic Data:

- change title
- CSR
- business background
- As-Is
- To-Be
- source/function
- document date

실제 회사명/내부 IP/실제 Repository URL/실제 CSR/실제 변경 문구 하드코딩 금지.

Generic Data 사용.

예:

`fare_calc.c`

`calculate_fare`

`C20250101_001`

정도의 가상 데이터.

---

# 22. 필수 Test Case

최소 다음 Test를 추가해.

## File Match

1. Full Path Exact
2. Separator 차이
3. Path Suffix Match
4. Basename Exact
5. Same basename with unrelated extension
6. Partial substring not match

## Symbol Match

7. Exact Symbol
8. trailing ()
9. whitespace
10. different symbol
11. substring only not strong match
12. invalid free text

## CSR

13. Exact CSR
14. Case normalization 정책
15. Different CSR
16. CSR 없음

## Date

17. Same day
18. 7 days
19. 30 days
20. 90 days
21. >90 days
22. Filename Date 없음
23. modified_at only

## Keyword

24. Commit message ↔ change title
25. Korean keyword
26. English case-insensitive
27. C identifier
28. Diff ↔ To-Be
29. Raw Text only weak match

## Gate

30. Date only → Link 제외
31. modified_at only → Link 제외
32. Strong File Evidence → Link 포함
33. Function Evidence → Link 포함
34. CSR Evidence → Link 포함
35. Multiple weak Evidence 조합 정책 Test

## Ranking

36. Function + File > File only
37. CSR + Keyword > Keyword only
38. Equal score deterministic ordering
39. Top N Limit
40. Min Threshold

## DB / Cache if change_link implemented

41. Unique Policy
42. Cascade Git Commit Delete
43. Cascade Change Item Delete
44. linker_version
45. Same Version Upsert/Reuse
46. New Version Lazy Rebuild

## API

47. Evidence API Normal Result
48. Git Candidate 없음
49. Change Item 없음
50. Link 없음
51. Invalid equipment
52. Empty Query
53. Ollama unavailable 영향 없음

---

# 23. 운영 테스트 관점

구현 완료 후 실제 내부 운영환경에서 다음을 확인할 예정이다.

Case A:

Function Name Query

예:
특정 함수가 왜 변경됐는지 질문

기대:
Git Candidate
+
해당 Source/Function이 기록된 Change Item
→ 높은 Link Ranking

Case B:

File Name Query

기대:
동일/유사 Source File Change Item 연결

Case C:

Business Keyword Query

기대:
Commit Message/Diff Keyword
+
Change Title/Background/To-Be
→ 관련 Link

Case D:

Date만 가까운 unrelated 문서

기대:
상위 Evidence로 나오지 않음

Case E:

동일 Change Title이 여러 Document에 존재

기대:
Source/Function/Scope/Date Evidence 차이에 따라 별도 Link 유지

---

# 24. Web UI 범위

이번 STEP 7에서 대규모 UI를 추가하지 마.

우선 Backend Evidence Link와 API 검증이 중심이다.

필요하면 Web UI에 별도 `Evidence Link 검증` 영역을 최소 추가할 수 있다.

다만 기존 메뉴:

- 시스템 상태
- 장비 관리
- 소스 변경 이력
- 변경내역서 분석

전체 구조를 다시 설계하지 마.

우선 API/Test로 검증 가능하면 UI 추가를 최소화해.

STEP 8과 STEP 9에서 최종 사용자 UX는 Continue 중심으로 갈 예정이다.

Web UI는 관리/검증 보조다.

---

# 25. 기존 기능 회귀 금지

다음은 반드시 유지해.

Equipment:
- 1:N Git Repository
- Metadata Save 분리
- Prepare 분리
- Existing Ready Repo Save 시 Git Network Command 0
- Yona Default Username 정책
- User URL Username 무시
- Password 미저장
- GIT_TERMINAL_PROMPT=0

Git:
- Incremental Sync
- Commit/Change 저장
- Commit List/Detail
- Diff

Trace:
- Git Top 5 Candidate
- 기존 Git Score
- Search Context

PPT:
- Metadata Candidate Search
- Progressive Fallback
- On-demand Parse
- SHA-256 Cache
- slide_cache
- change_item_cache
- parser_version
- Header Label 기반 Change Item Parser
- Change Item Search
- 관련도 UI
- 최초 내부 Keyword 검색

Frontend:
- Tab State 유지
- Tab 복귀 시 자동 Search 금지
- 완료 Toast 반복 금지
- Equipment Version Refresh
- Date Filter 정책
- Long-running Loading Panel
- 분석 상태 상세
- Cache Collapse
- 폴더 경로 복사
- Clipboard Compatibility Fallback

---

# 26. 이번 STEP에서 하지 않을 기능

- STEP 8 Ollama Answer
- LLM Prompt
- LLM Link 판단
- Embedding
- Vector DB
- Semantic Search Model
- Continue 연동
- MCP
- VSCode Extension 직접 개발
- OCR
- 전체 PPT Pre-parse
- 전체 Git × Change Item Link 사전 계산
- UI Dashboard 재설계
- AI Confidence Percentage

---

# 27. 구현 전 확인

코드 수정 전에 다음을 먼저 확인해.

1. 현재 Git Candidate Model/API 구조
2. Git Candidate 내부 Service
3. Current Git Score / match reason 구조
4. Change Item Model
5. change_item_cache Schema
6. Change Item Search Service
7. Change Item Search Score 구조
8. PPT Date Extraction Utility
9. Git Diff Context 구조
10. Search Context Keyword 구조
11. Existing DB Migration Pattern
12. Current API Router Convention
13. Current Config/Settings Pattern

기존 기능을 재사용할 수 있는 부분을 먼저 식별해.

중복 구현을 최소화해.

---

# 28. 완료 보고

완료 후 반드시 다음을 보고해.

1. STEP 7 최종 Architecture
2. Git Candidate 재사용 구조
3. Change Item Candidate 재사용 구조
4. Evidence Link 기본 단위
5. Link Score Weight 전체 목록
6. 각 Weight 선택 근거
7. Score Cap 여부
8. Primary Evidence 정의
9. Weak Evidence 정의
10. Primary Evidence Gate 정책
11. Min Link Threshold
12. File Match Level
13. Source Path Normalize 정책
14. Source Path Case 정책
15. Symbol Normalize 정책
16. Function Exact Match 정책
17. CSR Match 정책
18. Keyword Match 정책
19. Diff Match 정책
20. Date Evidence Source
21. Date Bucket/Weight
22. modified_at 처리 정책
23. match_reasons 최종 구조
24. change_link 저장 여부
25. change_link Schema
26. linker_version
27. Link Cache/Reuse 정책
28. Stale Link Invalidation 정책
29. On-demand Link 범위
30. Change Item Link Candidate Limit
31. Evidence Link Result Limit
32. Sort/Tie-break 정책
33. Evidence API Endpoint
34. Request Schema
35. Response Schema
36. Evidence Context 구조
37. Diff Excerpt 정책
38. 전체 Diff 미전달 확인
39. 전체 raw_text 미전달 확인
40. Synthetic Fixture 정책
41. 신규 Test 목록
42. 전체 Backend pytest 결과
43. Frontend 수정 여부
44. Frontend build 여부
45. 기존 STEP 1~6 회귀 확인
46. 구현 중 실패 이력
47. 실패 원인
48. 수정 내용
49. 재테스트 결과
50. STEP 8 미진행 확인

완료 후 STEP 8은 진행하지 말고 결과만 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

STEP 7 구현이 완료되었습니다. 전체 백엔드 pytest 회귀 테스트는 2회 연속 263개 전체 통과했고, 산출물 deploy 패키지도 재생성했습니다. 요청하신 50개 항목에 대해 순서대로 보고합니다.

## 1. STEP 7 최종 Architecture

```
query → search_trace() [기존 STEP4 재사용]
      → Git Candidate Top 5 + SearchContext
      → analyze_ppt_from_context() [기존 STEP6 재사용, 재구현 없음]
      → Change Item Candidate Top N (TRACE_CHANGE_ITEM_LINK_LIMIT)
      → get_or_compute_change_link()  [신규, change_link 캐시 lazy reuse]
      → Primary Evidence Gate + Min Score 필터
      → sort → Evidence Link Top N
      → POST /api/trace/evidence 응답
```

신규 모듈: `source_path_utils.py`, `symbol_utils.py`, `link_score_config.py`, `link_score_service.py`, `change_link_service.py`, `evidence_service.py`. 기존 STEP4/6 코드는 로직 변경 없이 재사용(단 1건의 사전 존재 버그 그레이스풀 처리 — 항목 46 참고).

## 2. Git Candidate 재사용 구조
`trace_service.search_trace()`를 그대로 호출해 Top5 `GitCandidate`(및 `SearchContext`)를 얻음. STEP4 Score/match_reasons 로직 미변경. 다만 `GitCandidate` 응답 모델에는 `diff`가 없어, `trace_service.get_commit_change_diff(commit_id, file_path)`를 신규 추가해 Link Score 계산 시점에만 diff를 조회.

## 3. Change Item Candidate 재사용 구조
`ppt_analysis_service.analyze_ppt_from_context(equipment_id, search_context)`을 그대로 호출 — Progressive Fallback/Cache/Parser 전부 기존 로직. 결과의 `change_item_candidates`를 `TRACE_CHANGE_ITEM_LINK_LIMIT`(기본 30)으로 절단.

## 4. Evidence Link 기본 단위
`1 Git Candidate(commit_id + file_path) ↔ 1 Change Item(change_item_cache_id)`. 동일 `change_title`이어도 Dedup하지 않음(항목 24 정책 유지).

## 5. Link Score Weight 전체 목록

| type | score | 분류 |
|---|---|---|
| same_function_exact | 40 | Primary |
| csr_exact | 35 | Primary |
| same_file_path (EXACT/SUFFIX) | 35 | Primary |
| same_file_basename | 25 | Primary |
| commit_message_change_title | 25 | Primary |
| diff_change_title | 15 | Weak |
| diff_source_function | 15 | Weak |
| date_0_7_days | 15 | Weak |
| message_other_field | 12 | Weak |
| date_8_30_days | 10 | Weak |
| diff_other_field | 10 | Weak |
| date_31_90_days | 5 | Weak |
| raw_text_keyword | 5 | Weak |

## 6. 각 Weight 선택 근거
실 운영 스코어를 직접 노출하지 않고, 기존 확정된 스케일에 맞춰 결정: STEP4 `TRACE_SCORE_CONFIG`(file_path=30, diff_symbol=25)와 STEP6 `CHANGE_ITEM_SCORE_CONFIG`(title=40, source_function=35, csr=25)의 상단 구간(25~40)을 그대로 Primary 대역으로 채택했습니다. 정확한 identifier/CSR 일치가 가장 explainable하므로 최고점(40/35), 단순 basename·commit message 매칭은 그보다 약간 낮게(25). Weak 대역(5~15)은 STEP4 `context`(5)·STEP6 `raw_text`(10) 수준을 참고해, 단독으로는 절대 Primary와 동급이 될 수 없도록 설계했습니다.

## 7. Score Cap 여부
**Option A(무제한 가중합)**. STEP6 Change Item Score가 이미 100을 초과하는 내부 랭킹 점수로 쓰이고 있어 관례를 유지했고, UI에 %로 노출할 계획이 없어 Cap의 실익이 없습니다.

## 8. Primary Evidence 정의
`same_function_exact`, `csr_exact`, `same_file_path`, `same_file_basename`, `commit_message_change_title` — 정확한 식별자/구조적 일치만 Primary로 분류.

## 9. Weak Evidence 정의
나머지 8종(diff 기반 키워드, message 보조 필드, date 3버킷, raw_text) — 모두 단서일 뿐 확정 근거는 아님.

## 10. Primary Evidence Gate 정책
`Primary 1개 이상` **OR** `서로 다른 Weak 타입 2개 이상`. 단일 Weak(예: date만, raw_text만)로는 절대 통과 불가 → date-only/약한 텍스트만의 Pair는 항상 제외됩니다.

## 11. Min Link Threshold
`TRACE_LINM_MIN_SCORE=10` (가장 작은 2-Weak 조합 `raw_text(5)+date_31_90(5)=10`과 동일값). Gate가 실질적 필터이며 이 값은 향후 Weight 변경 시를 위한 방어적 하한선입니다.

## 12. File Match Level
`EXACT`(정규화 경로 완전일치) > `SUFFIX`(한쪽이 다른 쪽의 디렉터리 경계 정렬된 접미사) > `BASENAME`(파일명만 일치) > `NONE`. 단순 substring은 절대 매치로 인정하지 않음(`fare_calc.c` vs `fare_calc_extended.c` 테스트로 검증).

## 13. Source Path Normalize 정책
`\`→`/`, 중복 슬래시 정리, 선행 `./` 제거, trim — `source_path_utils.normalize_source_path()`.

## 14. Source Path Case 정책
**대소문자 무시(소문자 정규화)**. 기존 STEP4 `trace_service._normalize_path`(Git file_path ↔ 사용자 질의 file_path 비교)가 이미 이 정책을 쓰고 있어 일관성을 위해 그대로 채택.

## 15. Symbol Normalize 정책
trailing `()` 제거 + whitespace trim만 수행(`symbol_utils.normalize_symbol`). 템플릿/네임스페이스/시그니처 파서는 만들지 않음.

## 16. Function Exact Match 정책
**대소문자 구분**(C/C++ 식별자 관례). `\b`(단어 경계) 정규식으로 diff/message 내 정확한 식별자 occurrence만 인정 — substring 매치(`calculate_fare` ⊄ `calculate_fare_extended`) 배제, 자유 텍스트는 `is_valid_symbol()`로 원천 차단.

## 17. CSR Match 정책
`csr_no` 값을 그대로 message+diff에 대해 **대소문자 무시 substring** 검사. CSR 포맷을 하드코딩한 정규식으로 추출하지 않고, Change Item Parser가 이미 뽑아낸 값을 기준으로 exact match만 사용.

## 18. Keyword Match 정책
기존 STEP4 `keyword_extractor.extract_keywords()`를 message/diff 양쪽에 그대로 재사용(한글 2+ 자, 영문 대소문자 무시, C 식별어/UPPER_SNAKE 모두 커버). message↔`change_title`은 Primary, message/diff↔나머지 구조화 필드는 Weak로 분리.

## 19. Diff Match 정책
diff는 `TRACE_DIFF_KEYWORD_SCAN_LIMIT_CHARS`(기본 4000자)로 길이 제한 후 스캔. 전체 diff 무제한 반복 비교 없음. Top5 Git Candidate 범위 내에서만 수행.

## 20. Date Evidence Source
Change Item의 **문서 파일명 날짜만** 사용(`ppt_date_parser.parse_date_from_text`, 기존 STEP5 로직 재사용, 신규 정규식 없음). `document_cache.modified_at`은 아예 입력에서 제외.

## 21. Date Bucket/Weight
0~7일: 15, 8~30일: 10, 31~90일: 5, 90일 초과: 근거 없음(생성 안 함).

## 22. modified_at 처리 정책
`ChangeItemEvidenceInput`에 `modified_at` 필드 자체가 존재하지 않음 — 구조적으로 절대 Link Score 입력이 될 수 없습니다(`test_date_evidence_never_derived_from_modified_at`로 검증).

## 23. match_reasons 최종 구조
```json
{"type": "same_function_exact", "score": 40, "git_value": "calculate_fare", "change_item_value": "calculate_fare()"}
{"type": "date_0_7_days", "score": 15, "distance_days": 3}
```
`type`/`score` 필수, `git_value`/`change_item_value`/`distance_days`/`match_level`은 있을 때만 포함(None 생략). 원문 대량 복사 없음.

## 24. change_link 저장 여부
**저장함(캐시)**. Link Score는 질의(keyword)와 무관하게 Git commit/file 고유값과 Change Item 고유값에만 의존하므로 캐싱이 항상 유효하다고 판단했습니다.

## 25. change_link Schema
```sql
CREATE TABLE change_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    git_commit_id INTEGER NOT NULL,
    git_file_path TEXT NOT NULL,
    change_item_cache_id INTEGER NOT NULL,
    link_score INTEGER NOT NULL,
    match_reasons_json TEXT NOT NULL DEFAULT '[]',
    linker_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (git_commit_id) REFERENCES git_commit(id) ON DELETE CASCADE,
    FOREIGN KEY (change_item_cache_id) REFERENCES change_item_cache(id) ON DELETE CASCADE,
    UNIQUE (git_commit_id, git_file_path, change_item_cache_id, linker_version)
);
```
사용자 지시의 `git_commit_id` 기반 식별을 따르되, **`git_file_path`를 키에 추가**했습니다 — 한 commit이 여러 파일을 건드리면 파일별로 diff/평가가 다른데, `git_commit_id`만으로 키를 잡으면 한 파일의 점수가 다른 파일 점수를 덮어쓰는 충돌이 생기기 때문입니다(완료 보고 중 유일한 스키마 설계 보정).

## 26. linker_version
`"rule-v1"` 상수(`link_score_config.LINKER_VERSION`). 향후 Weight/Rule 변경 시 값만 올리면 됩니다.

## 27. Link Cache/Reuse 정책
`(git_commit_id, git_file_path, change_item_cache_id, linker_version)` 완전 일치 시 캐시 재사용, 없으면 계산 후 `INSERT ... ON CONFLICT DO UPDATE`로 저장.

## 28. Stale Link Invalidation 정책
전부 **SQLite FK Cascade로 자동 처리**, 별도 무효화 코드 불필요:
- git_commit 삭제(장비/repo 삭제 등) → cascade
- change_item_cache 삭제(문서 재파싱/hash 변경 시 `store_change_items`가 delete+insert) → cascade
- linker_version 변경 → 기존 row는 그대로 두고, 다음 조회 시 새 버전 row가 lazy하게 추가 생성(강제 재계산 없음)
- `tests/test_change_link.py` 5개 케이스로 캐스케이드/버전 동작 검증

## 29. On-demand Link 범위
Git Top5 × Change Item Top N만 계산(최대 5×30=150쌍). 전체 Cartesian Product 사전 계산 없음.

## 30. Change Item Link Candidate Limit
`TRACE_CHANGE_ITEM_LINK_LIMIT=30`(env override 가능) — 기존 STEP6 `CHANGE_ITEM_CANDIDATE_LIMIT`(30)과 동일하게 맞춰 이중 축소 없이 일관성 유지.

## 31. Evidence Link Result Limit
`TRACE_EVIDENCE_LINK_LIMIT=10`.

## 32. Sort/Tie-break 정책
`link_score DESC` → `git rank(Top5 내 순서)` → `change_item_search_score DESC` → `commit_id` → `change_item_cache_id` (완전 deterministic, `test_ranking_equal_score_deterministic`로 검증).

## 33. Evidence API Endpoint
`POST /api/trace/evidence` (신규, 기존 `/search`/`/ppt-analysis` 미변경).

## 34. Request Schema
```json
{"equipment_id": 1, "query": "...", "file_path": "optional", "selected_code": "optional"}
```

## 35. Response Schema
```json
{
  "equipment_id": 1, "query": "...",
  "git_candidates": [...], "change_item_candidates": [...],
  "evidence_links": [
    {"git_commit_id":.., "git_repository_id":.., "git_commit_hash":.., "git_file_path":..,
     "change_item_cache_id":.., "document_cache_id":.., "link_score":.., "match_reasons":[...], "diff_excerpt": "..."}
  ],
  "debug": {"change_item_link_candidate_count":.., "fallback_documents_parsed":.., "change_item_total":..}
}
```
`evidence_links`는 전체 객체 대신 **id 참조**만 포함 — `git_candidates`/`change_item_candidates`에서 join.

## 36. Evidence Context 구조
Git 쪽(commit hash/date/message/file_path)과 Change Item 쪽(title/csr/background/status/as_is/to_be/source_functions/filename/slide_no) 필드는 이미 `git_candidates`/`change_item_candidates`에 다 있어 별도 중복 객체를 만들지 않았습니다. Link 쪽엔 `link_score`/`match_reasons`/`diff_excerpt`.

## 37. Diff Excerpt 정책
Primary 매치 근거(`same_function_exact`/`diff_*`/`csr_exact`)의 `git_value`를 anchor로 diff에서 매치 라인 찾아 `±DIFF_EXCERPT_CONTEXT_LINES`(기본 5줄)만 추출. 새 diff 파서는 만들지 않음(`evidence_service._extract_diff_excerpt`, 단순 라인 스캔).

## 38. 전체 Diff 미전달 확인
`match_reasons`/`diff_excerpt` 모두 4000자 제한 스캔 + ±5라인 발췌만 포함, 전체 diff 텍스트는 응답/캐시 어디에도 저장하지 않습니다.

## 39. 전체 raw_text 미전달 확인
`raw_text_keyword` 근거는 매치된 키워드 문자열(`git_value`)만 포함, Change Item `raw_text` 전문은 넣지 않습니다.

## 40. Synthetic Fixture 정책
전부 가상 데이터: `fare_calc.c`/`calculate_fare`/`C20250101_001` 류의 예시, 그리고 기존에 이미 있던 device-a 테스트 저장소(`FareCalc.c`/`CalcFare`/`CHILD_FARE`, 실제 회사 코드 아님)를 재사용. 실제 샘플 PPTX/원문은 전혀 사용하지 않았습니다.

## 41. 신규 Test 목록
84개 신규 (`test_source_path_utils.py` 13, `test_symbol_utils.py` 13, `test_link_score_service.py` 34, `test_change_link.py` 6, `test_evidence_api.py` 11 — parametrize 포함). File/Symbol/CSR/Date/Keyword/Gate/Ranking/DB·Cache/API 전 카테고리 커버.

## 42. 전체 Backend pytest 결과
`263 passed`(신규 84 + 기존 179) — **연속 2회** 전체 재실행하여 안정성 확인, 모두 통과.

## 43. Frontend 수정 여부
**없음.** STEP7은 Backend API/테스트만 구현(요청서 24항 "Web UI 범위" 지침에 따라 관리 UI 확장을 하지 않음).

## 44. Frontend build 여부
불필요(Frontend 미변경) — 미실행. 단 워크스페이스 산출물 규칙에 따라 `python scripts/package-deploy.py`는 재실행하여 `산출물/서버PC/deploy/backend/app/` 최신화.

## 45. 기존 STEP 1~6 회귀 확인
전체 pytest suite(Equipment/Git Repository/Yona/Trace/PPT Candidate/Change Item/Cache 등 기존 테스트 179개) 모두 그대로 통과. STEP7 코드는 기존 서비스를 호출만 하고 내부 로직을 변경하지 않았습니다.

## 46. 구현 중 실패 이력
전체 suite 최초 1회 실행에서 `test_evidence_response_shape[evidence_links]` 1건 실패 (`zipfile.BadZipFile`).

## 47. 실패 원인
`ppt_analysis_service._run_progressive_fallback`(기존 STEP6 코드)가 `get_or_parse_document` 성공 후 곧바로 `change_item_cache_service.parse_and_store_change_items`에서 **같은 파일을 재차 `Presentation()`으로 여는데, 이 두번째 open이 try/except로 보호되지 않아** 드물게(Windows 파일 접근 타이밍) 발생하는 파싱 실패가 그대로 전체 요청을 크래시시키는 **STEP6부터 존재하던 잠재 버그**였습니다. 제 STEP7 Evidence API가 이 fallback 경로를 넓은 키워드 폭으로 처음 안정적으로 트리거한 것입니다.

## 48. 수정 내용
`change_item_cache_service.parse_and_store_change_items`의 `Presentation(path)` 호출을 `ppt_parser_service.parse_pptx_file`과 동일한 그레이스풀 디그레이드 정책(try/except + warning 로그 + 빈 결과 반환, 기존 캐시는 보존)으로 감쌌습니다. Change Item 파싱/스코어링 로직 자체는 변경 없음 — 순수 크래시 방어입니다.

## 49. 재테스트 결과
수정 후 관련 테스트 재실행 통과, 전체 suite **2회 연속 263 passed**로 안정성 재확인.

## 50. STEP 8 미진행 확인
Ollama 연동, LLM Prompt, VSCode Continue/MCP 연동 등 STEP8/9 범위는 전혀 손대지 않았습니다. STEP7은 여기서 종료합니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- STEP 7은 매우 큰 작업이므로, 먼저 기존 구조(Git Candidate, Change Item, Config, DB 패턴)를 파악한 뒤 설계·구현하겠습니다. 작업 목록을 세우고 병렬로 탐색을 시작합니다.
- Git Candidate / Trace 구조 확인 완료. 이어서 Config, keyword_extractor, ppt_date_parser, DB migration, API router 패턴을 확인합니다.
- `ppt_date_parser`가 이미 공통 Utility임을 확인했습니다 (재구현 불필요). PROJECT_SPEC v2의 STEP 7 관련 부분을 자세히 확인합니다.
- 探索이 끝났습니다. 이제 핵심 설계(Path/Symbol Normalize, Link Score Config)부터 구현을 시작합니다.
- 이제 유틸리티부터 순서대로 작성합니다.
- 이제 Link Score Config, Migration 스키마를 작성합니다.
- Now 핵심 Link Score Service를 작성합니다.
- trace_service.py에 diff 조회 헬퍼를 추가합니다.

- 사용 도구: TodoWrite×3, Read×27, Glob×3, Grep×11, Write×11, StrReplace×7, ReadLints×2, Shell×11, AwaitShell×2 (총 77회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [003]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #51  |  Monday, Jul 13, 2026, 9:32 AM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

STEP 7 완료 보고 검토 결과 두 가지 구현 확인 및 최소 보완이 필요하다.

이번 작업에서는 STEP 7 Architecture, Weight, Gate, change_link Schema, Evidence API 구조를 재설계하지 마.

## 1. TRACE_LINK_MIN_SCORE Config 이름 확인

STEP 7 완료 보고 11번에는:

TRACE_LINM_MIN_SCORE

라고 표기되어 있다.

문맥상 TRACE_LINK_MIN_SCORE의 오타로 보인다.

먼저 실제 Code 전체를 확인해.

확인 대상:

- Settings/Config
- os.getenv 또는 환경변수 참조
- link_score_config
- Tests
- .env example 또는 운영 문서
- deploy 산출 대상 Source

실제 구현은 이미 TRACE_LINK_MIN_SCORE인데 완료 보고만 오타라면 Code 수정하지 마.

실제 구현도 TRACE_LINM_MIN_SCORE라면:

TRACE_LINK_MIN_SCORE

로 수정해.

기존 잘못된 이름을 호환 Alias로 유지할 필요는 없다.
아직 운영 확정 전 단계이므로 올바른 이름으로 정리해.

관련 Test 실행.

## 2. CSR Exact Match 구현 확인

STEP 7 완료 보고에는 CSR Match 정책을:

- exact match

라고 설명했지만 구현 설명에는:

case-insensitive substring 검사

라고 되어 있다.

현재 실제 csr_exact 판단 코드를 확인해.

다음 오연결이 가능한지 확인해.

Change Item CSR:
SR260529_42025

Git Message:
SR260529_420251 수정

이 경우 csr_exact가 발생하면 안 된다.

CSR Prefix를 SR 또는 C 등으로 하드코딩하지 마.

Change Item Parser가 추출한 csr_no 문자열을 기준으로 비교해.

CSR 값의 앞뒤가 identifier character:

A-Z
a-z
0-9
_

에 연결되어 있으면 동일 CSR로 인정하지 않는 Boundary Match 방식을 검토해.

예상:

"SR260529_42025 반영"
→ Match

"[SR260529_42025]"
→ Match

"CSR:SR260529_42025"
→ Match

"SR260529_420251"
→ No Match

"XSR260529_42025"
→ No Match

대소문자 무시 정책은 현재대로 유지 가능.

기존 Generic CSR 정책 유지.
특정 Prefix Regex 하드코딩 금지.

csr_exact Weight 35와 Primary Evidence 정책은 변경하지 마.

필요하면 CSR Match Helper를 명확한 Utility로 분리해.

## 3. Weak Gate는 이번 작업에서 변경 금지

현재:

Primary Evidence 1개 이상
OR
서로 다른 Weak Evidence Type 2개 이상

정책은 이번 수정에서 변경하지 마.

date + raw_text 등 약한 조합의 실제 오연결 가능성은 운영 Evidence API 테스트 후 판단한다.

Weight와 TRACE_LINK_MIN_SCORE도 이름 오타 외에는 변경하지 마.

## 4. 테스트

최소 다음을 확인해.

Config:
- TRACE_LINK_MIN_SCORE 이름
- Environment override 적용

CSR:
- exact CSR
- case-insensitive CSR
- brackets around CSR
- colon before CSR
- longer CSR suffix false positive 방지
- leading identifier false positive 방지
- different CSR
- no CSR

전체 Backend:

python -m pytest tests/ -q

Frontend 수정 금지.
STEP 8 진행 금지.

## 5. 완료 보고

1. TRACE_LINM_MIN_SCORE가 보고 오타였는지 실제 Code 오타였는지
2. 최종 Config 이름
3. CSR 기존 구현 방식
4. CSR substring false positive 재현 여부
5. CSR 최종 Match 방식
6. 추가/수정 Test
7. 전체 pytest 결과
8. Frontend 미수정 확인
9. STEP 8 미진행 확인

결과만 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

## 완료 보고

1. **TRACE_LINM_MIN_SCORE** — 완료 보고 오타. 코드/env/deploy/테스트는 처음부터 `TRACE_LINK_MIN_SCORE`였고 수정 없음.

2. **최종 Config 이름** — `TRACE_LINK_MIN_SCORE` (기본값 10, `os.getenv` override 유지)

3. **CSR 기존 구현** — `csr.lower() in haystack.lower()` substring → `SR260529_42025`가 `SR260529_420251`에도 매칭됨

4. **False positive 재현** — 확인됨. 위 케이스로 `csr_exact`가 잘못 발생

5. **최종 Match 방식** — `csr_utils.csr_appears_in_text()`: Parser `csr_no` 기준, 대소문자 무시, 앞뒤가 `[A-Za-z0-9_]`이면 불인정. Prefix 하드코딩 없음. Weight 35 / Primary 유지

6. **추가/수정 Test** — `test_csr_utils.py`(9), `test_link_score_config.py`(2), `test_link_score_service.py` CSR 경계 케이스 4개 추가

7. **전체 pytest** — **278 passed**, 1 warning

8. **Frontend** — 미수정

9. **STEP 8** — 미진행

산출물 `deploy/`는 backend 반영 후 `package-deploy.py`로 현행화함.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- STEP 7 최소 보완만 진행합니다. Config 이름과 CSR 매칭 구현부터 코드에서 확인합니다.
- Config는 보고 오타만 확인됐습니다. CSR은 substring이라 false positive가 가능하므로 boundary match로 수정합니다.

- 사용 도구: Grep×3, TodoWrite×5, Read×3, Write×3, StrReplace×3, Shell×4, AwaitShell (총 22회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [004]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #52  |  Monday, Jul 13, 2026, 9:44 AM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

STEP 7 보완 결과는 확인했다.

- TRACE_LINK_MIN_SCORE는 정상
- CSR boundary match 수정 완료
- 278 passed
- Frontend 미수정
- STEP 8 미진행

이제 실제 운영 데이터로 `/api/trace/evidence` 결과를 검증하려고 한다.

이번 작업은 STEP 8 구현이 아니라 STEP 7 Evidence API 운영 검증을 쉽게 하기 위한 최소 지원 작업이다.

목표:

1. 운영 PC에서 Evidence API를 쉽게 호출하고 결과를 확인할 수 있게 한다.
2. Git Candidate, Change Item Candidate, Evidence Link, match_reasons를 사람이 검증하기 쉽게 보여준다.
3. STEP 8, Ollama, Continue 연동은 진행하지 않는다.

우선 다음 중 가장 작은 방법을 선택해.

A. 기존 Web UI에 임시 `Evidence Link 검증` 영역 추가
B. 별도 간단한 HTML/페이지 추가
C. API 호출 예시와 curl/PowerShell 테스트 스크립트 제공

가능하면 A를 선호한다.
하지만 전체 UI를 크게 바꾸지 마.

## 표시해야 할 정보

입력:

- equipment 선택
- query 입력
- file_path optional
- selected_code optional
- 실행 버튼

결과:

1. Git Candidate 목록
   - rank
   - commit hash short
   - date
   - message
   - file_path
   - git_candidate_score

2. Change Item Candidate 목록
   - rank
   - change_title
   - document filename
   - slide_no
   - source/function
   - change_item_search_score

3. Evidence Link 목록
   - rank
   - link_score
   - git commit hash short
   - git_file_path
   - change_title
   - document filename
   - slide_no
   - match_reasons

match_reasons는 반드시 사람이 읽기 쉽게 보여줘.

예:

same_function_exact +40
  Git: calculate_fare
  Change Item: calculate_fare()

same_file_basename +25
  Git: src/fare/fare_calc.c
  Change Item: subwaylib/fare/src/fare_calc.c

date_0_7_days +15
  distance_days: 3

diff_excerpt가 있으면 접힘 영역으로 표시해.
기본 펼침으로 전체 화면을 길게 만들지 마.

## 중요한 검증 포인트

Evidence Link 1위가 다음처럼 강한 근거를 갖는지 확인할 수 있어야 한다.

- same_function_exact
- same_file_path / same_file_basename
- csr_exact
- commit_message_change_title

반대로 다음처럼 약한 근거만 있는 Link가 상위에 올라오는지 확인할 수 있어야 한다.

- date only
- raw_text only
- date + raw_text only

이번 작업에서는 Link Score Weight, Gate, Threshold를 변경하지 마.
운영 결과를 보고 필요하면 다음 요청에서 조정한다.

## 테스트할 운영 케이스

UI 또는 테스트 가이드에 다음 케이스를 명시해.

1. 함수명 Query
2. 파일명 Query
3. 업무 키워드 Query
4. 날짜만 가까운 unrelated 결과가 상위에 나오지 않는지 확인
5. 동일 Change Title이 여러 Document에 있을 때 별도 Link로 유지되는지 확인

## 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Evidence Score 재설계
- Gate 변경
- Weight 변경
- DB Schema 변경
- Parser 변경
- Search Algorithm 변경
- 전체 UI 재설계

## 완료 보고

1. 선택한 검증 방식
2. Evidence API 호출 위치
3. 입력 UI 또는 테스트 스크립트
4. Git Candidate 표시 항목
5. Change Item Candidate 표시 항목
6. Evidence Link 표시 항목
7. match_reasons 표시 방식
8. diff_excerpt 표시 방식
9. Frontend 수정 여부
10. Frontend build 결과
11. Backend 수정 여부
12. pytest 실행 여부
13. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

## 완료 보고

1. **검증 방식** — A. 기존 Web UI에 `Evidence Link 검증` 탭 추가 (전체 UI 재설계 없음)

2. **API 호출** — Frontend `POST /api/trace/evidence` (`frontend/src/api/evidence.ts`)

3. **입력 UI** — 장비 선택, query, file_path(optional), selected_code(optional), Evidence 실행 버튼 + 운영 검증 케이스 가이드

4. **Git Candidate** — rank, short hash, date, message, file_path, git_candidate_score

5. **Change Item Candidate** — rank, change_title, document filename, slide_no, source/function, search_score

6. **Evidence Link** — rank, link_score, short hash, git_file_path, change_title, document, slide_no, match_reasons (+ Primary 유무 배지)

7. **match_reasons** — `type +score` / Git·Change Item 값 / distance_days / Primary|Weak 구분 표시

8. **diff_excerpt** — 기본 접힘, `diff_excerpt 보기`로 펼침

9. **Frontend 수정** — 있음 (탭 + API client + viewer)

10. **Frontend build** — 성공 (`tsc -b && vite build`)

11. **Backend 수정** — 없음 (Score/Gate/Weight/Schema 미변경)

12. **pytest** — 미실행 (Backend 미변경)

13. **STEP 8** — 미진행

산출물 `deploy/`도 재생성했습니다. 서버 재기동 후 운영 PC에서 `Evidence Link 검증` 탭으로 확인하면 됩니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 운영 Evidence API 검증용 최소 UI를 기존 Web에 추가합니다. 먼저 프론트엔드 구조와 API 호출 패턴을 확인합니다.
- 옵션 A로 기존 Web에 검증 탭만 최소 추가합니다.

- 사용 도구: TodoWrite×3, Glob, Grep×2, Read×9, Write×3, StrReplace×2, Shell×2 (총 22회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [005]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #53  |  Monday, Jul 13, 2026, 12:00 PM (UTC+9)                      ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

STEP 7 Evidence Link 검증 화면으로 운영 테스트를 진행했다.

테스트 결과 중요한 문제를 확인했다.

## 문제

장비를 `휴대용정산기`로 선택했는데 Change Item Candidate에 `개집표기` 변경내역서가 포함된다.

운영 문서 구조상:

- 변경내역서 파일명에는 항상 장비명이 포함된다.
- 문서 내부 1페이지에도 장비명과 버전 정보가 표시된다.
- 비슷한 장비 문서들이 같은 폴더에 저장되는 경우가 있다.
- 따라서 폴더 기준 검색만으로는 선택 장비와 다른 장비의 변경내역서가 후보에 섞일 수 있다.

예:

선택 장비:
휴대용정산기

검색 결과에 포함된 문서:
프로그램변경내역서_20260620_v1.71_개집표기_15분재승차.pptx

이 문서는 선택 장비와 다르므로 Change Item Candidate / Evidence Link 후보에서 제외되어야 한다.

이번 작업은 STEP 7 운영 검증 중 발견된 장비 불일치 문서 필터링 보완이다.

검색 Algorithm 전체 재설계, Link Score Weight 변경, Gate 변경, STEP 8 진행은 하지 마.

---

# 1. 장비 문서 필터링 목표

선택한 equipment.name과 관련 없는 변경내역서 문서는 PPT Candidate / Change Item Candidate / Evidence Link 후보에서 제외해야 한다.

핵심:

`장비 선택`
→ `해당 장비 변경내역서만 분석 대상`
→ `Change Item Candidate 생성`
→ `Evidence Link 생성`

이 되어야 한다.

현재처럼 같은 폴더 안의 다른 장비 변경내역서가 키워드만 맞는다는 이유로 후보에 포함되면 안 된다.

---

# 2. 우선 필터 기준: 파일명 장비명

운영 문서 규칙상 변경내역서 파일명에는 항상 장비명이 포함된다.

따라서 우선 다음 정책을 적용해.

선택 장비명:

equipment.name

문서 파일명:

document filename

비교:

- normalize 후 filename에 equipment.name이 포함되면 해당 장비 문서로 인정
- 포함되지 않으면 기본 제외

예:

equipment.name = "휴대용정산기"

프로그램변경내역서_20260620_v246_휴대용정산기_코레일15분재승차.pptx
→ 포함

프로그램변경내역서_20260620_v1.71_개집표기_15분재승차.pptx
→ 제외

문서 경로의 폴더명에 equipment.name이 포함되는지 여부는 보조 정보일 뿐, 같은 폴더에 여러 장비 문서가 섞일 수 있으므로 primary 판단으로 사용하지 마.

---

# 3. 1페이지 장비명 보조 검토

문서 내부 1페이지에도 장비명과 버전 정보가 표시된다.

가능하면 다음 보조 정책을 검토해.

- cover slide 또는 slide 1 text에서 equipment.name이 확인되면 해당 장비 문서로 인정
- filename이 애매한 경우 cover slide equipment match를 보조 근거로 사용

다만 이번 작업에서 문서 파싱 구조를 과도하게 변경하지 마.

이미 document_cache / slide_cache / raw slide text 또는 cover slide text가 있다면 재사용해.

새로 전체 PPT를 대량 재파싱하지 마.

우선 파일명 기준 필터만으로 충분히 해결 가능하면 파일명 기준을 먼저 적용해.

---

# 4. 장비명 Normalize

최소 Normalize:

- trim
- whitespace 제거 또는 통일
- 대소문자 무시
- 한글은 원문 유지
- `_`, `-`, 공백 차이 일부 흡수 검토

예:

"휴대용정산기"
"휴대용 정산기"

는 같은 장비명으로 판단할 수 있도록 검토.

단 너무 공격적인 fuzzy matching은 하지 마.

예:

"개집표기"
"휴대용정산기"

가 비슷한 장비라는 이유로 통과하면 안 된다.

---

# 5. 장비 별칭은 이번에 최소 검토만

향후 장비 관리 화면에 문서 장비명 별칭을 둘 수 있다.

예:

equipment.name = 휴대용정산기
aliases = 휴대용정산기, 휴대용 정산기, HHD

하지만 이번 작업에서 DB Schema를 크게 바꾸지 마.

현재 데이터에서 장비명이 파일명에 항상 들어가는 운영 규칙이 있으므로, 우선 equipment.name 기반 필터로 해결해.

별칭이 꼭 필요하다고 판단되면 완료 보고에 제안만 하고 이번 구현에서는 보류해.

---

# 6. 필터 적용 위치

가능하면 PPT Candidate 단계 또는 Change Item Candidate 생성 직전에 적용해.

중요:

선택 장비와 다른 문서는 다음 결과에 나오면 안 된다.

- PPT Candidate
- Change Item Candidate
- Evidence Link
- Evidence API response
- 변경내역서 분석 화면 결과

기존 Cache에 다른 장비 문서가 이미 들어 있어도, 검색 결과에서 선택 장비와 맞지 않으면 제외해야 한다.

즉 Cache 존재 여부와 무관하게 결과 필터링이 적용되어야 한다.

---

# 7. Debug 정보

운영 검증을 위해 분석 상태 상세 또는 Evidence Debug에 다음 Count를 표시할 수 있다.

- equipment filter excluded documents N
- excluded reason: filename equipment mismatch

단 일반 메인 화면에 과도하게 표시하지 마.

Evidence 검증 화면에서는 Debug로 보여도 된다.

---

# 8. Evidence 검증 화면 개선

현재 운영 테스트 화면에서 Git Candidate가 0건이고 Change Item Candidate만 다수 나오는 경우가 있었다.

예:

Git 0
Change Item 15
Evidence Link 0

이 경우 사용자가 왜 Evidence Link가 없는지 알기 어렵다.

다음 안내를 추가해.

Git Candidate가 0이면:

`Git 후보가 없어 Evidence Link를 생성할 수 없습니다.`

추가 안내:

`Git Repository 준비/동기화 상태, 검색어, file_path 입력 여부를 확인하세요.`

Evidence Link가 0이면 원인을 구분해서 표시해.

- Git Candidate 0
- Change Item Candidate 0
- Link Gate/Threshold 통과 결과 0

가능한 범위에서 분기 표시.

STEP 7 Score/Gate 자체는 변경하지 마.

---

# 9. Evidence 검증 화면 결과 순서

검증 화면은 현재 기능 확인용이므로 대규모 UI 개선은 하지 않는다.

다만 가능하면 Evidence Link를 Git/Change Item 후보보다 위에 표시하는 구조를 검토해.

추천:

1. Summary
2. Evidence Links
3. Git Candidates
4. Change Item Candidates

Evidence Link가 없는 경우:

`Evidence Link 없음 - 원인: Git Candidate 0건`

처럼 표시.

이번 작업에서 전체 UI 재설계는 하지 마.

---

# 10. 테스트

Synthetic 문서/후보 데이터로 테스트해.

실제 내부 변경내역서 원문이나 파일명 전체를 테스트 Fixture에 넣지 마.

장비명은 가상 값 사용.

예:

equipment.name = "PortableDevice"

문서명:

program_change_PortableDevice_feature_a.pptx
→ 포함

program_change_GateDevice_feature_a.pptx
→ 제외

필수 테스트:

1. filename contains selected equipment name → include
2. filename different equipment name → exclude
3. whitespace normalized equipment name → include
4. case-insensitive English equipment name → include
5. folder name contains selected equipment but filename different equipment → exclude
6. cached change_item from other equipment → exclude
7. Evidence API response excludes other equipment document
8. Change Item Candidate count reduced by equipment filter
9. Git Candidate 0 안내 메시지 표시
10. Evidence Link 0 원인 표시

Frontend 수정 시:

npm run build

Backend 수정 시:

python -m pytest tests/ -q

---

# 11. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Primary Evidence Gate 변경
- TRACE_LINK_MIN_SCORE 변경
- change_link Schema 변경
- 전체 PPT Pre-parse
- 전체 UI 재설계
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩

---

# 12. 완료 보고

다음을 보고해.

1. 장비 불일치 문서 필터 적용 위치
2. 파일명 기반 장비 필터 정책
3. Cover Slide 장비명 사용 여부
4. 장비명 Normalize 정책
5. 별칭 처리 여부
6. 기존 Cache 문서에 대한 필터 적용 여부
7. PPT Candidate 제외 여부
8. Change Item Candidate 제외 여부
9. Evidence Link 제외 여부
10. Debug Count 추가 여부
11. Git Candidate 0 안내 메시지
12. Evidence Link 0 원인 표시
13. Evidence 검증 화면 순서 변경 여부
14. 추가/수정 Test
15. Backend pytest 결과
16. Frontend build 결과
17. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

## 완료 보고

1. **필터 적용 위치** — PPT Candidate 스캔 직후 hard exclude + Change Item/Slide cache 결과 직전 재필터 (`ppt_candidate_service`, `ppt_analysis_service`)
2. **파일명 정책** — normalize 후 `equipment.name ⊆ filename`만 포함. 폴더명 매치는 포함 근거로 사용하지 않음
3. **Cover Slide** — 미사용 (파일명 필터로 충분)
4. **Normalize** — trim, lower, 공백/`_`/`-` 제거 후 포함 비교. fuzzy 없음
5. **별칭** — 미구현. 향후 `equipment.aliases` 제안만 보류
6. **기존 Cache** — Cache에 있어도 결과 단계에서 filename 불일치면 제외
7. **PPT Candidate** — 제외됨
8. **Change Item Candidate** — 제외됨
9. **Evidence Link** — 제외된 Change Item만 링킹하므로 함께 제외
10. **Debug Count** — `equipment_filter_excluded` + reason `filename equipment mismatch` (분석 상태 상세 / Evidence debug)
11. **Git 0 안내** — Evidence 화면에 안내 문구 추가
12. **Link 0 원인** — Git 0 / Change Item 0 / Gate·Threshold 0 분기 표시
13. **결과 순서** — Summary → Evidence Links → Git → Change Item
14. **Test** — `test_equipment_name_utils.py`, `test_equipment_document_filter.py` + fixture 파일명 보정
15. **pytest** — **290 passed**
16. **Frontend build** — 성공
17. **STEP 8** — 미진행

산출물 `deploy/` 현행화 완료. 서버 재기동 후 `휴대용정산기` 선택 시 `개집표기` 문서는 Candidate/Evidence에서 빠져야 합니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 장비명 파일명 필터와 Evidence 검증 화면 안내를 최소 보완합니다. 먼저 Candidate/분석 파이프라인 적용 지점을 확인합니다.
- 파일명 하드 필터를 구현하고, 기존 테스트 fixture 파일명도 장비명과 맞게 정리합니다.
- Evidence 검증 UI와 분석 상태 상세에 필터/0건 안내를 반영합니다.

- 사용 도구: TodoWrite×2, Read×22, Grep×9, Write×4, StrReplace×35, Shell×5, AwaitShell×2 (총 79회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [006]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #54  |  Monday, Jul 13, 2026, 2:09 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

운영 테스트 결과, 장비 필터링 문제가 아직 해결되지 않았다.

## 문제

변경내역서 분석 화면에서 장비를 `휴대용정산기`로 선택하고 `영수증 변경사항`을 검색했는데, 검색 결과에 여전히 `개집표기` 변경내역서 문서가 포함된다.

이 결과는 잘못된 결과다.

선택 장비가 `휴대용정산기`이면 `개집표기` 문서는 다음 어디에도 나오면 안 된다.

- 변경내역서 분석 결과
- Change Item Candidate
- Evidence 검증 화면의 Change Item Candidate
- Evidence Link 후보
- 기존 Cache 기반 검색 결과

이번 문제는 STEP 8 진행 전 반드시 수정해야 한다.

---

# 1. 핵심 요구사항

선택한 equipment.name과 맞지 않는 변경내역서 문서는 검색 결과에서 제외해야 한다.

운영 문서 규칙:

- 변경내역서 파일명에는 항상 장비명이 포함된다.
- 예:
  - 휴대용정산기 문서: 파일명에 `휴대용정산기` 포함
  - 개집표기 문서: 파일명에 `개집표기` 포함
- 비슷한 장비 문서가 같은 폴더 안에 섞여 있을 수 있다.
- 따라서 폴더 경로만으로 장비를 판단하면 안 된다.

예:

선택 장비:
`휴대용정산기`

포함:
`프로그램변경내역서_20260620_v246_휴대용정산기_코레일15분재승차.pptx`

제외:
`프로그램변경내역서_20260620_v1.71_개집표기_15분재승차.pptx`

---

# 2. 필터는 Cache 여부와 무관하게 적용

중요하다.

기존 document_cache, slide_cache, change_item_cache에 이미 다른 장비 문서가 들어 있어도, 현재 선택한 equipment.name과 문서 파일명이 맞지 않으면 결과에서 제외해야 한다.

즉 다음 경로 모두에서 장비 필터가 적용되어야 한다.

1. PPT Candidate 생성 단계
2. Progressive Fallback으로 추가 탐색한 문서
3. document_cache 기반 재사용 결과
4. slide_cache 기반 검색 결과
5. change_item_cache 기반 검색 결과
6. Change Item Candidate 반환 직전
7. Evidence API의 Change Item Candidate 반환 직전
8. Evidence Link 생성 직전

가장 안전한 방식은:

- 문서 후보 단계에서 1차 필터
- Change Item Candidate 반환 직전에 2차 필터

를 모두 적용하는 것이다.

---

# 3. 파일명 기준 필터를 우선 적용

선택 장비명:

`equipment.name`

문서 파일명:

`Path(document_path).name`

비교 정책:

- normalize 후 filename에 equipment.name이 포함되면 통과
- 포함되지 않으면 제외

Normalize 최소 정책:

- trim
- 공백 제거
- `_`, `-`, `.`, 괄호 등 구분자 차이 일부 무시 가능
- 영문은 대소문자 무시
- 한글은 원문 유지

예:

`휴대용정산기`
`휴대용 정산기`
`휴대용_정산기`

는 가능하면 같은 의미로 판단.

단 fuzzy matching은 하지 마.

`휴대용정산기`와 `개집표기`가 같은 장비로 통과하면 안 된다.

---

# 4. 폴더명으로 통과시키지 말 것

같은 폴더 안에 여러 장비 변경내역서가 섞여 있다.

따라서 folder path에 선택 장비명이 있거나 equipment.document_path에 속한다는 이유만으로 문서를 통과시키지 마.

판단 기준은 우선 document filename이다.

---

# 5. 문서 1페이지 장비명은 보조만 검토

문서 내부 1페이지에도 장비명과 버전이 표시된다.

가능하면 cover slide text에서 장비명을 추출해 보조적으로 사용할 수 있다.

하지만 이번 수정의 우선순위는 filename 기반 필터다.

이번 작업에서 전체 PPT 구조나 Parser를 크게 바꾸지 마.

파일명 기준만으로 해결 가능하면 cover slide parsing 추가는 보류해도 된다.

---

# 6. 장비 필터링 함수 분리

장비 문서 필터를 여러 곳에서 중복 구현하지 마.

공통 Utility 또는 Service 함수로 분리해.

예시 개념:

`is_document_for_equipment(document_path, equipment_name)`

또는 현재 프로젝트 naming convention에 맞는 이름.

이 함수는 다음에서 재사용 가능해야 한다.

- PPT Candidate filtering
- Change Item Candidate filtering
- Evidence Candidate filtering

---

# 7. Debug Count 추가

운영 검증을 위해 분석 상태 상세 또는 Evidence Debug에 다음 Count를 추가해.

예:

`장비 불일치 제외 문서 N건`

또는

`equipment_filter_excluded_documents`

일반 메인 화면에는 과도하게 표시하지 않아도 된다.

하지만 운영 검증 화면에서는 제외 여부를 확인할 수 있어야 한다.

---

# 8. 반드시 확인할 실제 운영 케이스

수정 후 다음을 운영 환경에서 확인할 예정이다.

장비:
`휴대용정산기`

검색어:
`영수증 변경사항`

기대:

- 휴대용정산기 변경내역서만 표시
- 개집표기 변경내역서 미표시
- 기존 Cache에 개집표기 문서가 있어도 미표시

장비:
`휴대용정산기`

검색어:
`15분 재승차 관련 변경 이유`

기대:

- 휴대용정산기 문서만 표시
- 개집표기 문서 미표시

---

# 9. 테스트

실제 내부 문서명이나 원문을 테스트 Fixture에 넣지 마.

Synthetic 이름으로 테스트해.

예:

equipment.name = `PortableDevice`

포함:
`program_change_20250101_PortableDevice_feature.pptx`

제외:
`program_change_20250101_GateDevice_feature.pptx`

필수 테스트:

1. filename contains selected equipment name → include
2. filename has different equipment name → exclude
3. same folder but different equipment filename → exclude
4. cached change_item from different equipment document → exclude
5. PPT Candidate excludes different equipment document
6. Change Item Candidate excludes different equipment document
7. Evidence API excludes different equipment document
8. Progressive Fallback result also filtered
9. whitespace normalized equipment name include
10. English case-insensitive include

Backend 수정 시:

`python -m pytest tests/ -q`

Frontend 수정 시:

`npm run build`

---

# 10. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Gate 변경
- TRACE_LINK_MIN_SCORE 변경
- change_link Schema 변경
- 전체 PPT Pre-parse
- 전체 UI 재설계
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩

---

# 11. 완료 보고

다음을 보고해.

1. 기존에 개집표기 문서가 섞였던 원인
2. 장비 필터 적용 위치
3. filename 기반 필터 정책
4. folder path만으로 통과시키지 않는지 여부
5. Cache 기반 검색 결과에도 필터가 적용되는지 여부
6. PPT Candidate 필터 적용 여부
7. Progressive Fallback 결과 필터 적용 여부
8. Change Item Candidate 필터 적용 여부
9. Evidence API 필터 적용 여부
10. 공통 Utility 함수명
11. Normalize 정책
12. Debug Count 추가 여부
13. 추가/수정 테스트 목록
14. 전체 pytest 결과
15. Frontend 수정 여부
16. Frontend build 결과
17. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 운영에서 필터가 여전히 뚫리는 원인을 코드 경로별로 추적합니다.

- 사용 도구: TodoWrite, Read×5, Grep×4, Shell (총 11회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [007]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #55  |  Monday, Jul 13, 2026, 2:09 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

운영 테스트 결과, 장비 필터링 문제가 아직 해결되지 않았다.

## 문제

변경내역서 분석 화면에서 장비를 `휴대용정산기`로 선택하고 `영수증 변경사항`을 검색했는데, 검색 결과에 여전히 `개집표기` 변경내역서 문서가 포함된다.

이 결과는 잘못된 결과다.

선택 장비가 `휴대용정산기`이면 `개집표기` 문서는 다음 어디에도 나오면 안 된다.

- 변경내역서 분석 결과
- Change Item Candidate
- Evidence 검증 화면의 Change Item Candidate
- Evidence Link 후보
- 기존 Cache 기반 검색 결과

이번 문제는 STEP 8 진행 전 반드시 수정해야 한다.

---

# 1. 핵심 요구사항

선택한 equipment.name과 맞지 않는 변경내역서 문서는 검색 결과에서 제외해야 한다.

운영 문서 규칙:

- 변경내역서 파일명에는 항상 장비명이 포함된다.
- 예:
  - 휴대용정산기 문서: 파일명에 `휴대용정산기` 포함
  - 개집표기 문서: 파일명에 `개집표기` 포함
- 비슷한 장비 문서가 같은 폴더 안에 섞여 있을 수 있다.
- 따라서 폴더 경로만으로 장비를 판단하면 안 된다.

예:

선택 장비:
`휴대용정산기`

포함:
`프로그램변경내역서_20260620_v246_휴대용정산기_코레일15분재승차.pptx`

제외:
`프로그램변경내역서_20260620_v1.71_개집표기_15분재승차.pptx`

---

# 2. 필터는 Cache 여부와 무관하게 적용

중요하다.

기존 document_cache, slide_cache, change_item_cache에 이미 다른 장비 문서가 들어 있어도, 현재 선택한 equipment.name과 문서 파일명이 맞지 않으면 결과에서 제외해야 한다.

즉 다음 경로 모두에서 장비 필터가 적용되어야 한다.

1. PPT Candidate 생성 단계
2. Progressive Fallback으로 추가 탐색한 문서
3. document_cache 기반 재사용 결과
4. slide_cache 기반 검색 결과
5. change_item_cache 기반 검색 결과
6. Change Item Candidate 반환 직전
7. Evidence API의 Change Item Candidate 반환 직전
8. Evidence Link 생성 직전

가장 안전한 방식은:

- 문서 후보 단계에서 1차 필터
- Change Item Candidate 반환 직전에 2차 필터

를 모두 적용하는 것이다.

---

# 3. 파일명 기준 필터를 우선 적용

선택 장비명:

`equipment.name`

문서 파일명:

`Path(document_path).name`

비교 정책:

- normalize 후 filename에 equipment.name이 포함되면 통과
- 포함되지 않으면 제외

Normalize 최소 정책:

- trim
- 공백 제거
- `_`, `-`, `.`, 괄호 등 구분자 차이 일부 무시 가능
- 영문은 대소문자 무시
- 한글은 원문 유지

예:

`휴대용정산기`
`휴대용 정산기`
`휴대용_정산기`

는 가능하면 같은 의미로 판단.

단 fuzzy matching은 하지 마.

`휴대용정산기`와 `개집표기`가 같은 장비로 통과하면 안 된다.

---

# 4. 폴더명으로 통과시키지 말 것

같은 폴더 안에 여러 장비 변경내역서가 섞여 있다.

따라서 folder path에 선택 장비명이 있거나 equipment.document_path에 속한다는 이유만으로 문서를 통과시키지 마.

판단 기준은 우선 document filename이다.

---

# 5. 문서 1페이지 장비명은 보조만 검토

문서 내부 1페이지에도 장비명과 버전이 표시된다.

가능하면 cover slide text에서 장비명을 추출해 보조적으로 사용할 수 있다.

하지만 이번 수정의 우선순위는 filename 기반 필터다.

이번 작업에서 전체 PPT 구조나 Parser를 크게 바꾸지 마.

파일명 기준만으로 해결 가능하면 cover slide parsing 추가는 보류해도 된다.

---

# 6. 장비 필터링 함수 분리

장비 문서 필터를 여러 곳에서 중복 구현하지 마.

공통 Utility 또는 Service 함수로 분리해.

예시 개념:

`is_document_for_equipment(document_path, equipment_name)`

또는 현재 프로젝트 naming convention에 맞는 이름.

이 함수는 다음에서 재사용 가능해야 한다.

- PPT Candidate filtering
- Change Item Candidate filtering
- Evidence Candidate filtering

---

# 7. Debug Count 추가

운영 검증을 위해 분석 상태 상세 또는 Evidence Debug에 다음 Count를 추가해.

예:

`장비 불일치 제외 문서 N건`

또는

`equipment_filter_excluded_documents`

일반 메인 화면에는 과도하게 표시하지 않아도 된다.

하지만 운영 검증 화면에서는 제외 여부를 확인할 수 있어야 한다.

---

# 8. 반드시 확인할 실제 운영 케이스

수정 후 다음을 운영 환경에서 확인할 예정이다.

장비:
`휴대용정산기`

검색어:
`영수증 변경사항`

기대:

- 휴대용정산기 변경내역서만 표시
- 개집표기 변경내역서 미표시
- 기존 Cache에 개집표기 문서가 있어도 미표시

장비:
`휴대용정산기`

검색어:
`15분 재승차 관련 변경 이유`

기대:

- 휴대용정산기 문서만 표시
- 개집표기 문서 미표시

---

# 9. 테스트

실제 내부 문서명이나 원문을 테스트 Fixture에 넣지 마.

Synthetic 이름으로 테스트해.

예:

equipment.name = `PortableDevice`

포함:
`program_change_20250101_PortableDevice_feature.pptx`

제외:
`program_change_20250101_GateDevice_feature.pptx`

필수 테스트:

1. filename contains selected equipment name → include
2. filename has different equipment name → exclude
3. same folder but different equipment filename → exclude
4. cached change_item from different equipment document → exclude
5. PPT Candidate excludes different equipment document
6. Change Item Candidate excludes different equipment document
7. Evidence API excludes different equipment document
8. Progressive Fallback result also filtered
9. whitespace normalized equipment name include
10. English case-insensitive include

Backend 수정 시:

`python -m pytest tests/ -q`

Frontend 수정 시:

`npm run build`

---

# 10. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Gate 변경
- TRACE_LINK_MIN_SCORE 변경
- change_link Schema 변경
- 전체 PPT Pre-parse
- 전체 UI 재설계
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩

---

# 11. 완료 보고

다음을 보고해.

1. 기존에 개집표기 문서가 섞였던 원인
2. 장비 필터 적용 위치
3. filename 기반 필터 정책
4. folder path만으로 통과시키지 않는지 여부
5. Cache 기반 검색 결과에도 필터가 적용되는지 여부
6. PPT Candidate 필터 적용 여부
7. Progressive Fallback 결과 필터 적용 여부
8. Change Item Candidate 필터 적용 여부
9. Evidence API 필터 적용 여부
10. 공통 Utility 함수명
11. Normalize 정책
12. Debug Count 추가 여부
13. 추가/수정 테스트 목록
14. 전체 pytest 결과
15. Frontend 수정 여부
16. Frontend build 결과
17. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

장비 필터를 basename 전용 공통 함수 + 반환 직전 2차 필터로 강화했습니다. **STEP 8 미진행.**

---

### 완료 보고

1. **원인**
   같은 `document_path` 폴더에 장비별 PPT가 섞여 있고, 과거 파싱으로 `document_cache`/`change_item_cache`에 다른 장비 문서가 남아 있음. 이전 필터는 후보/캐시 일부에만 있었고, **반환·Evidence 직전 최종 게이트**와 **경로→basename 강제**가 약해 누출 여지가 남았음.

2. **필터 적용 위치**
   PPT Candidate 생성 · Progressive Fallback · slide/change_item cache 검색 · CI 반환 직전 · Evidence CI 반환 직전 · Evidence Link 생성 직전

3. **filename 정책**
   `Path(document_path).name`에 `equipment.name`이 normalize 후 포함되면 통과, 아니면 제외 (fuzzy 없음)

4. **folder path만으로 통과?**
   **아니오.** basename만 사용. 폴더에 선택 장비명이 있어도 파일명이 다르면 제외

5. **Cache 기반 검색에도 적용?**
   **예.** `list_change_items_for_equipment` / slide cache 결과도 동일 필터

6. **PPT Candidate**
   **적용** (`search_ppt_candidates`, `list_scored_ppt_files_for_fallback`)

7. **Progressive Fallback**
   **적용** (목록·파싱·hit 수집 단계)

8. **Change Item Candidate**
   **적용** (캐시/funnel/fallback + **반환 직전 2차**)

9. **Evidence API**
   **적용** (CI 재필터 + Link 생성 직전 row 재확인)

10. **공통 함수**
    `is_document_for_equipment` (+ `document_basename`, `normalize_equipment_name`, `filename_matches_equipment`)

11. **Normalize**
    trim · lower · 공백/`_`/`-`/`.`/`()`/`[]`/`{}` 제거 · 한글 원문 · fuzzy 없음

12. **Debug Count**
    `equipment_filter_excluded` (분석 상세 / Evidence debug: `filename equipment mismatch`)

13. **테스트**
    `test_equipment_name_utils.py`, `test_equipment_document_filter.py` — include/exclude, same folder, cache, PPT/CI/Evidence, fallback, whitespace, case, final gate, folder-false-positive

14. **pytest**
    **299 passed**

15. **Frontend**
    **수정 없음** (기존 debug 표시 유지)

16. **Frontend build**
    **미실행** (FE 변경 없음)

17. **STEP 8**
    **미진행**

---

**산출물:** `python scripts/package-deploy.py` 완료 → `산출물/서버PC/deploy/` 현행화

운영 재검증 시 **서버 프로세스 재시작** 후 `휴대용정산기` + `영수증 변경사항` / `15분 재승차 관련 변경 이유`로 확인하세요.
참고: **「분석 Cache 보기」**는 과거 파싱 원본 목록이라 다른 장비 파일이 보일 수 있고, 검색/분석 결과·Evidence에는 나오면 안 됩니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 원인: 1차 필터는 있으나 반환 직전 최종 필터가 없고, 경로 전체 매칭 시 폴더명으로 오통과될 수 있습니다. basename 전용 `is_document_for_equipment`와 전 경로 2차 필터를 적용합니다.

- 사용 도구: Grep×13, Read×16, Shell×6, TodoWrite×4, Write×3, StrReplace×10, AwaitShell×2 (총 54회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [008]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #57  |  Monday, Jul 13, 2026, 2:50 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

Evidence Link 검증 화면에서 운영 테스트를 진행했다.

## 문제

장비 `휴대용정산기`, query `영수증 변경사항`으로 검색했는데 Evidence Link 상위 결과에 `경기버스 요금인상`, `카드맵 변경사항` 등 영수증과 직접 관련 없는 변경 항목이 표시된다.

HTML 저장 결과를 보면 Evidence Link 상위는 다음과 같은 근거로 높은 link_score를 받았다.

- same_file_path
- same_function_exact
- commit_message_change_title
- diff_change_title
- diff_source_function

즉 Git Commit과 Change Item 사이의 구조적 연결은 강하지만, 사용자 query `영수증 변경사항`과 직접 관련 있는지에 대한 근거가 부족하다.

현재 결과는 사용자가 보기에는 다음 의문이 생긴다.

`왜 영수증 변경사항을 검색했는데 경기버스/카드맵 변경이 나오는가?`

이번 작업의 목적은 STEP 7 Evidence 결과에 Query 관련성 근거를 추가하고, 최종 Evidence Ranking에서 Query 관련성이 낮은 강한 Link가 상위에 올라오는 문제를 완화하는 것이다.

STEP 8, Ollama, Continue 연동은 진행하지 마.

---

# 1. 핵심 개념 분리

Evidence Link에는 두 가지 의미가 있다.

1. Query Relevance
   - 이 Git Candidate 또는 Change Item Candidate가 사용자 query와 얼마나 관련 있는가?

2. Link Strength
   - 이 Git Commit/File과 Change Item이 서로 얼마나 강하게 연결되는가?

현재 STEP 7은 Link Strength는 잘 보여주지만 Query Relevance가 부족하다.

따라서 Evidence Link 결과에 Query Relevance 정보를 추가해.

---

# 2. Query 핵심 키워드 정제

사용자 Query에서 의도 표현/일반 단어를 강한 검색어로 쓰지 않도록 개선해.

예:

query:
`영수증 변경사항`

핵심 키워드:
`영수증`

약한/제외 키워드:
`변경사항`

query:
`15분 재승차 관련 변경 이유`

핵심 키워드:
`15분`
`재승차`

약한/제외 키워드:
`관련`
`변경`
`이유`

query:
`file_close_init 함수 변경 이유?`

핵심 키워드:
`file_close_init`

약한/제외 키워드:
`함수`
`변경`
`이유`

다음과 같은 한국어 의도 표현은 Query Relevance 강한 키워드에서 제외하거나 매우 낮은 가중치로 처리해.

- 변경
- 변경사항
- 변경 이유
- 관련
- 이유
- 뭐야
- 무엇
- 왜
- 함수
- 소스
- 내용
- 사항

단 C 함수명, 파일명, 숫자+업무 키워드는 유지.

기존 keyword_extractor를 무조건 크게 바꾸지 말고, Evidence API용 query intent stopword / core keyword 필터를 별도로 두는 것을 우선 검토해.

기존 STEP4/STEP6 검색 회귀를 깨지 마.

---

# 3. Query Match Reason 추가

Evidence API 응답에 Query Match 정보를 추가해.

최소 구조 예:

query_keywords:
[
  "영수증"
]

weak_query_terms:
[
  "변경사항"
]

각 Git Candidate 또는 Change Item Candidate에 다음 정보를 추가할 수 있는지 검토해.

query_match_reasons:
[
  {
    "keyword": "영수증",
    "field": "change_title",
    "value": "김포골드라인 사업자 변경으로 인하여 카드 충전/환불 영수증...",
    "score": 40
  }
]

또는 현재 API Convention에 맞는 유사 구조.

중요:

- 어떤 키워드가
- 어느 필드에서
- 왜 검색 결과에 포함되었는지

사람이 확인할 수 있어야 한다.

원문 전체를 대량 복사하지 마.
필드 일부 또는 매치 키워드 중심으로만 표시해.

---

# 4. Evidence Link 최종 Ranking 개선

현재 정렬이 link_score 중심이라 Query와 관련 없는 강한 Link가 상위에 올라올 수 있다.

최종 Evidence Ranking에는 Query Relevance를 반영해.

개념:

final_rank_score
=
query_relevance_score
+
link_score

또는

query_relevance_gate 통과 후 link_score 정렬

둘 중 현재 구조에 맞는 방식을 검토해.

내 추천은 Gate + Score 방식이다.

## Query Relevance Gate

Evidence Link가 최종 결과로 나오려면 최소 하나는 만족해야 한다.

- Git Candidate가 core query keyword와 직접 매칭
- Change Item Candidate가 core query keyword와 직접 매칭
- file_path 또는 selected_code가 제공되었고 해당 Git/Change Item source/function과 매칭

예:

query `영수증 변경사항`

Core keyword:
`영수증`

`경기버스 요금인상 카드맵` Link는 core keyword `영수증`과 Git/Change Item 어느 쪽도 직접 매칭되지 않으면 최종 Evidence Link에서 제외하거나 낮은 순위로 내려야 한다.

단, 사용자가 file_path / selected_code를 명시한 경우에는 file/function match를 Query Relevance로 인정할 수 있다.

---

# 5. 일반 단어만 매칭된 결과는 상위 제외

`변경사항`, `관련`, `이유` 같은 일반 단어만 매칭된 Git/Change Item은 Query Relevance가 낮아야 한다.

예:

query:
`영수증 변경사항`

Git Commit:
`경기마을버스요금인상 관련 ... 카드맵 변경사항 적용`

이 경우 `변경사항`만 매칭되었다면 Query Relevance가 낮다.

이 결과는 강한 same_file/function link가 있더라도 `영수증` 관련 결과보다 상위에 오면 안 된다.

---

# 6. Query Match 없는 Strong Link 처리 정책

Git-PPT Link 자체가 강하더라도 Query Core Keyword와 무관하면 다음 중 하나로 처리해.

A. 최종 Evidence Link에서 제외

또는

B. `Query 관련성 낮음`으로 분류하고 기본 접힘/하위 표시

이번 POC에서는 우선 A를 추천한다.

단 운영 데이터에서 결과가 너무 사라지는 경우를 대비해 Debug에는 제외 Count를 남겨라.

예:

debug:
query_relevance_excluded_links: N

---

# 7. Evidence 검증 화면 UI 보완

Evidence Link Card에 다음을 추가해.

- Query Match 수준
  - 높음
  - 보통
  - 낮음
  - 없음

- Query Match 근거
  예:
  `영수증` matched in Change Item title
  `영수증` matched in To-Be
  `file_close_init` matched in selected_code/source_function

- Link Match 근거
  기존 match_reasons 유지

화면에서 다음을 구분할 수 있어야 한다.

Query Match:
왜 사용자 질문과 관련 있는가?

Link Match:
왜 이 Git과 이 Change Item이 연결되는가?

현재 match_reasons는 Link Match 근거이므로 유지하되, Query Match 근거와 섞지 마.

---

# 8. Change Item Candidate 표에도 검색 근거 표시

Change Item Candidates 표에 최소한 다음 중 하나를 추가해.

- matched keywords
- query match field
- query relevance level

예:

search_score 100 옆에:

`영수증 · change_title`

또는 상세/tooltip:

`영수증 matched in change_title`

이렇게 표시하면 사용자가 왜 이 후보가 나왔는지 알 수 있다.

---

# 9. Git Candidate 표에도 검색 근거 표시

Git Candidates에도 왜 검색됐는지 표시해.

예:

`변경사항 matched in commit_message`

또는:

`영수증 matched in commit_message`

이 차이가 매우 중요하다.

`영수증 변경사항` 검색에서 Git Candidate가 단지 `변경사항` 때문에 검색된 것이라면 화면에서 드러나야 한다.

---

# 10. 기존 Link Score 변경 최소화

이번 작업에서 same_file_path, same_function_exact, csr_exact 등 Link Strength Weight를 크게 바꾸지 마.

문제는 Link Strength 자체가 아니라 Query Relevance가 최종 Ranking에 반영되지 않는 것이다.

필요하면 final ranking score를 추가하되 기존 link_score는 그대로 유지해.

예:

link_score:
Git-PPT 연결 강도

query_relevance_score:
사용자 질문 관련성

final_rank_score:
최종 표시 순위

---

# 11. 테스트 케이스

Synthetic 데이터로 테스트해.

실제 내부 문서명/원문 사용 금지.

필수 테스트:

1. query `receipt change`
   - Change Item title contains receipt
   - Evidence 상위 포함

2. query `receipt change`
   - unrelated strong link with only generic word `change`
   - 최종 Evidence에서 제외 또는 하위 처리

3. query `영수증 변경사항`
   - `영수증`은 core keyword
   - `변경사항`은 weak/stopword

4. query `15분 재승차 관련 변경 이유`
   - `15분`, `재승차` core
   - `관련`, `변경`, `이유` weak/stopword

5. query `file_close_init 함수 변경 이유`
   - `file_close_init` core
   - `함수`, `변경`, `이유` weak/stopword

6. strong file/function link but no core query match
   - final Evidence 상위에 오지 않음

7. selected_code가 제공된 경우 function match는 query relevance로 인정

8. file_path가 제공된 경우 file match는 query relevance로 인정

9. Query Match Reason이 API 응답에 포함

10. Evidence 검증 화면에서 Query Match 근거 표시

Backend 수정 시:
python -m pytest tests/ -q

Frontend 수정 시:
npm run build

---

# 12. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Strength Weight 대규모 변경
- change_link Schema 변경
- 기존 STEP4/STEP6 검색 회귀 유발
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩
- 전체 UI 재설계

---

# 13. 완료 보고

다음을 보고해.

1. 기존에 영수증 query에서 경기버스/카드맵 Link가 상위에 나온 원인
2. Query Core Keyword 추출 정책
3. Stopword/Weak Query Term 목록
4. Query Relevance Score 또는 Gate 정책
5. 기존 link_score 유지 여부
6. final_rank_score 도입 여부
7. Query Match Reason API 구조
8. Git Candidate Query Match 표시
9. Change Item Candidate Query Match 표시
10. Evidence Link Query Match 표시
11. Query 관련성 낮은 Strong Link 처리 정책
12. debug 제외 Count 추가 여부
13. 추가/수정 테스트
14. Backend pytest 결과
15. Frontend build 결과
16. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

Query Relevance를 Evidence에 분리 반영했습니다. **STEP 8 미진행.**

---

### 완료 보고

1. **원인**
   정렬이 `link_score`(same_file/function 등) 중심이라, query의 일반어(`변경사항`)로만 잡힌 Git/Change Item도 구조적 Link가 강하면 상위에 올랐음. Query core keyword(`영수증`) 관련성은 반영되지 않았음.

2. **Core Keyword 정책**
   Evidence 전용 `split_evidence_query_intent()` — identifier / 한글 / `15분` 형태 / 파일명 유지. STEP4 `keyword_extractor`는 변경하지 않음.

3. **Stopword/Weak**
   변경, 변경사항, 관련, 이유, 뭐야, 무엇, 왜, 함수, 소스, 내용, 사항 + EN(change/related/reason/…)
   활용형(`함수가`, `변경됐어`)은 prefix 규칙으로 weak 처리.

4. **Gate 정책**
   core keyword가 Git 또는 Change Item에 직접 매칭되거나, `file_path`/`selected_code` 매칭이 있어야 최종 Evidence Link 유지. weak만 매칭 → 제외.

5. **link_score 유지**
   **예.** Weight/Gate/Schema(`change_link`) 미변경.

6. **final_rank_score**
   **도입.** `query_relevance_score + link_score`로 정렬. 표시용 `link_score`는 그대로.

7. **Query Match Reason API**
   `query_keywords`, `weak_query_terms`
   후보/Link: `query_match_reasons[{keyword, field, value, score, strength}]`, `query_relevance_score/level`

8. **Git Candidate 표시**
   query match 수준 + `keyword · field`

9. **Change Item Candidate 표시**
   동일 (search_score 옆)

10. **Evidence Link 표시**
    Query Match / Link Match 분리, `final_rank` 표시

11. **Strong Link + Query 무관**
    **A. 최종 Evidence에서 제외**

12. **Debug**
    `query_relevance_excluded_links` (+ intent keywords)

13. **테스트**
    `test_query_relevance.py`, `test_evidence_api.py` 확장 (intent/gate/selected_code/file_path/API)

14. **pytest**
    **311 passed**

15. **Frontend build**
    **성공**

16. **STEP 8**
    **미진행**

공통 모듈: `backend/app/services/query_relevance_service.py`
산출물: `package-deploy.py` 반영 완료. 서버 재시작 후 `영수증 변경사항` 재검증하세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Query Relevance를 Evidence에 분리 반영합니다. STEP4/6 검색은 유지하고, Evidence 전용 core keyword·Gate·UI부터 구조를 확인합니다.
- Evidence 전용 query intent·relevance 서비스를 추가하고 API·UI에 연동합니다.

- 사용 도구: TodoWrite×4, Task, Grep×3, Read×17, Glob, Write×4, StrReplace×18, Shell×7, AwaitShell×3 (총 58회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [009]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #60  |  Monday, Jul 13, 2026, 5:50 PM (UTC+9)                       ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

이번 작업은 소스 변경 이력 화면의 사용성 개선이다.

현재 소스 변경 이력 화면에서 Commit 목록이 많을 때 페이지 전체가 스크롤된다.

문제:

- Commit 목록을 아래로 스크롤한 상태에서 Commit을 클릭하면 오른쪽 Commit 상세 영역이 화면 위쪽에 있어 다시 위로 스크롤해야 한다.
- Commit 목록과 Commit 상세를 비교하기 어렵다.
- Commit 목록 스크롤 위치와 상세 확인 흐름이 불편하다.

목표:

소스 변경 이력 화면에서 Commit 목록만 별도 스크롤되도록 개선한다.

---

# 1. Layout 목표

소스 변경 이력 화면은 다음 구조가 되도록 한다.

상단:
- 장비 선택
- Repository 선택
- Git 동기화
- 검색 조건 영역

하단 결과 영역:
- 왼쪽 Commit 목록 패널
- 오른쪽 Commit 상세 패널

하단 결과 영역은 화면 높이에 맞게 표시하고, 페이지 전체가 길게 늘어나지 않도록 한다.

왼쪽 Commit 목록은 자체 스크롤을 가진다.

오른쪽 Commit 상세도 내용이 길 경우 자체 스크롤을 가진다.

---

# 2. Commit 목록 스크롤

Commit 목록 영역에만 세로 스크롤을 적용한다.

예상 동작:

- Commit 목록이 많아도 브라우저 페이지 전체가 계속 내려가지 않는다.
- 사용자는 왼쪽 Commit 목록 안에서만 스크롤한다.
- Commit을 클릭해도 왼쪽 목록 스크롤 위치는 유지된다.
- 오른쪽 Commit 상세는 즉시 보인다.
- 상세 확인을 위해 페이지 상단으로 다시 올릴 필요가 없어야 한다.

---

# 3. Commit 상세 영역

오른쪽 Commit 상세 패널은 선택한 Commit의 상세 정보와 Diff를 보여준다.

상세 내용이 길 경우 오른쪽 패널 내부에서만 스크롤되게 한다.

Diff가 긴 경우 기존 정책 유지:

- 가로 스크롤 허용
- 강제 줄바꿈으로 Diff 가독성을 해치지 말 것
- 상세 패널 폭이 Commit 선택 전후로 흔들리지 않게 유지

---

# 4. 화면 높이 계산

검색 조건 영역 아래의 남은 화면 높이를 결과 영역이 사용하도록 한다.

CSS 예시 개념:

- `.git-history` 또는 화면 Root는 column layout
- `.git-history-body`는 flex layout
- `.commit-list-panel`, `.commit-detail-panel`은 `overflow-y: auto`
- 필요한 경우 `min-height: 0`을 반드시 적용

중요:

flex child에서 스크롤이 정상 동작하려면 `min-height: 0`이 필요할 수 있다.

브라우저 전체 페이지가 아니라 내부 패널이 스크롤되어야 한다.

---

# 5. 검색 조건 영역은 과도하게 고정하지 말 것

검색 조건 영역까지 sticky로 고정할 필요는 없다.

이번 목표는 Commit 목록/상세의 내부 스크롤이다.

검색 영역을 새로 크게 재설계하지 마.

기존 compact 검색 영역 정책 유지.

---

# 6. Commit 목록과 상세 비율 유지

기존에 합의한 정책을 유지한다.

- Commit 목록 영역은 너무 넓지 않게
- Commit 상세 영역을 더 넓게
- 대략 25:75 또는 28:72 비율 유지

이번 작업으로 Commit 목록이 다시 화면 절반 이상을 차지하지 않게 한다.

---

# 7. 선택 상태 유지

Commit 목록에서 특정 Commit을 선택한 상태로 목록을 스크롤해도 선택 표시가 유지되어야 한다.

선택한 Commit 상세는 오른쪽에 유지되어야 한다.

다른 Commit 클릭 시 상세만 변경되고, 전체 페이지 스크롤이 튀지 않게 한다.

---

# 8. Pagination 위치

현재 Commit 목록 하단에 Pagination이 있다면 다음 중 더 자연스러운 방식을 선택한다.

권장:

- Commit 목록 패널 내부 하단에 유지
- 목록 스크롤과 함께 자연스럽게 접근 가능

또는:

- Commit 목록 패널 하단에 고정

복잡한 sticky pagination이 필요 없다면 기존 위치를 유지하되 내부 스크롤 영역 안에서 동작하게 한다.

---

# 9. 회귀 금지

다음 기존 기능을 변경하지 마.

- 장비 선택
- Repository 선택
- Git 동기화
- 검색 조건
- 기간 지정 정책
- 파일 경로 검색
- 작성자 검색
- Commit 목록 조회
- Commit 상세 조회
- Diff 표시
- Pagination
- 선택 Commit 표시
- Tab 이동 시 상태 유지
- Tab 복귀 시 자동 재검색 금지
- 완료 Toast 반복 금지

---

# 10. 테스트

Frontend 위주로 확인한다.

필수 확인:

1. Commit 목록이 많을 때 왼쪽 Commit 목록 패널만 스크롤되는지
2. 브라우저 페이지 전체가 과도하게 길어지지 않는지
3. Commit 클릭 후 오른쪽 상세가 즉시 보이는지
4. Commit 목록 스크롤 위치가 유지되는지
5. 오른쪽 상세 내용이 길면 상세 패널 내부에서 스크롤되는지
6. Diff 가로 스크롤이 유지되는지
7. 검색 실행 후 Layout이 깨지지 않는지
8. Pagination 동작 유지
9. Tab 이동 후 복귀 시 Layout/상태 유지
10. 작은 화면 또는 낮은 해상도에서 최소 사용 가능

Frontend:

npm run build

Backend 수정 금지.

Search Algorithm, Git Sync, Evidence Link, PPT 분석, STEP 8 관련 코드는 변경하지 마.

---

# 11. 금지

- STEP 8
- Ollama
- Evidence Link 로직 변경
- Git 검색 로직 변경
- Backend API 변경
- DB 변경
- 전체 UI 재설계
- 새로운 UI Framework 도입
- Commit 목록 가상 스크롤 신규 도입
- 무리한 Sticky Header/Sticky Search 영역 추가

---

# 12. 완료 보고

다음을 보고해.

1. 변경한 파일
2. Commit 목록 내부 스크롤 적용 방식
3. Commit 상세 내부 스크롤 적용 방식
4. 화면 높이 계산 방식
5. `min-height: 0` 적용 여부
6. Commit 목록/상세 비율
7. Pagination 위치 정책
8. 선택 Commit 상태 유지 여부
9. Tab 상태 회귀 여부
10. Frontend build 결과
11. Backend 미수정 확인
12. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

Commit 목록/상세를 패널 내부 스크롤로 분리했습니다. 페이지 전체 스크롤 없이 상세를 바로 볼 수 있습니다.

### 완료 보고

1. **변경 파일**
   `frontend/src/components/GitHistory.tsx`, `frontend/src/components/GitHistory.css`

2. **목록 스크롤**
   `.commit-list-scroll`에 `overflow-y: auto` — 목록만 세로 스크롤

3. **상세 스크롤**
   `.commit-detail-scroll`에 `overflow-y: auto` — Diff는 기존처럼 `overflow-x: auto` + `white-space: pre`

4. **높이 계산**
   `.git-history` = `flex` column + `height: calc(100vh - 3.25rem)`
   `.git-history-body` = `flex: 1`로 검색 영역 아래 남은 높이 사용

5. **`min-height: 0`**
   body / panel / scroll 영역에 적용

6. **비율**
   **28% : 72%** 유지 (`minmax(220px, 28%)` / `minmax(0, 72%)`)

7. **Pagination**
   목록 패널 **하단 고정**(목록 스크롤 영역 밖) — 스크롤과 무관하게 접근

8. **선택 상태**
   React state 유지 — 목록 스크롤/클릭 시 선택·상세 유지, 페이지 스크롤 점프 없음

9. **Tab 회귀**
   로직/상태 로직 미변경 — Tab 유지 정책 그대로

10. **Frontend build**
    **성공**

11. **Backend**
    **미수정**

12. **STEP 8**
    **미진행**

산출물: `package-deploy.py`로 `산출물/서버PC/deploy/` 현행화 완료.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 소스 변경 이력 화면의 Commit 목록/상세 내부 스크롤만 개선합니다. 관련 컴포넌트부터 확인합니다.

- 사용 도구: Glob×2, Grep×6, Read×6, StrReplace×2, Write, Shell×3 (총 20회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [010]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #61  |  Tuesday, Jul 14, 2026, 10:16 AM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

Evidence Link 검증 화면을 테스트한 결과, 기능적으로는 file/function 기반 Evidence Link가 생성되고 있으나 Query Intent 표시와 결과 표현이 너무 디버그 중심이라 실무자가 이해하기 어렵다.

이번 작업은 STEP 7 Evidence 검증 화면의 Query Intent 분류와 표시 방식 개선이다.

Search Algorithm, Link Score Weight, Gate, DB Schema는 변경하지 마.

---

# 1. Query Intent core / weak 분류 개선

현재 query:

file_close_init 함수 변경 내역을 보여줘

결과:

core: file_close_init, 내역을, 보여줘, file_save_mgt.c, file_save_mgt
weak: 함수, 변경

문제:

`내역을`, `보여줘`는 검색 핵심어가 아니라 사용자 요청 표현이다.
core에 들어가면 안 된다.

수정 방향:

core:
- file_close_init
- file_save_mgt.c
- file_save_mgt

weak 또는 ignored:
- 함수
- 변경
- 내역
- 내역을
- 보여줘
- 보여
- 줘
- 이유
- 관련
- 사항
- 뭐야
- 무엇
- 왜
- 알려줘

한국어 조사/어미가 붙은 표현도 고려해.

예:

내역
내역을
내역이

보여줘
보여줘요
알려줘
알려줘요

이런 표현은 core keyword가 되면 안 된다.

단 C 함수명, 파일명, 숫자+업무 키워드는 유지해야 한다.

---

# 2. file_path 입력은 Query Intent에서 별도 표시

file_path 입력값에서 파생된:

file_save_mgt.c
file_save_mgt

는 일반 query keyword와 섞어서 보여주기보다 별도 표시하는 것을 검토해.

예:

Query Intent

요청 함수:
file_close_init

요청 파일:
file_save_mgt.c

제외/약한 표현:
함수, 변경, 내역, 보여줘

현재처럼 core 한 줄에 모두 나열하는 방식은 이해하기 어렵다.

---

# 3. Query Match 표시 요약

현재 Query Match 영역에 너무 많은 match reason이 기본 펼침으로 표시된다.

예:

file_save_mgt matched in commit_message
file_save_mgt matched in git_file_path
file_save_mgt matched in source_function
file_save_mgt matched in raw_text
변경 matched in change_title weak
...

이 방식은 검증용으로도 너무 길다.

기본 화면에서는 요약만 보여줘.

예:

Query Match 높음

- 요청 함수 file_close_init 일치
- 요청 파일 file_save_mgt.c 일치
- 변경내역서 소스/함수 항목에 file_close_init() 존재

상세 match reason은 접힘 영역으로 이동해.

버튼 예:

[Query Match 상세 보기]

---

# 4. Link Match 표시 요약

Link Match도 기본 화면에서는 핵심 Primary 근거 위주로 요약해.

예:

Link Match

- 같은 파일: file_save_mgt.c
- 같은 함수: file_close_init()
- 관련 Diff 키워드: 시간초과

상세 점수 정보는 접힘 영역에 유지.

예:

[Link Score 상세 보기]

상세 안에는 기존처럼 다음 표시 가능:

same_file_path +35
same_function_exact +40
diff_change_title +15
date_31_90_days +5

---

# 5. Evidence Link Card 기본 정보 정리

Evidence Link Card 기본 표시 순서를 다음처럼 정리해.

1. Rank / Query Match 수준 / Primary 개수
2. Change Item 제목
3. Git Commit short hash + file path
4. 문서명 + Slide
5. Query Match 요약
6. Link Match 요약
7. 상세 보기 버튼들

현재처럼 link_score, final_rank, query_relevance 숫자가 가장 먼저 강조되면 실무자가 이해하기 어렵다.

숫자는 검증에는 필요하지만 기본 강조를 낮춰라.

예:

기본:
관련성 높음 · Primary 2

상세:
link_score 120
query_relevance 360
final_rank 480

---

# 6. core/weak 용어 설명 추가

검증 화면 상단 또는 Query Intent 영역에 짧은 설명을 추가해.

예:

core: 실제 검색 의도로 판단한 핵심어
weak: 질문 표현 또는 일반 단어로 판단한 보조어

단 실무 최종 화면에서는 core/weak 용어를 그대로 노출하지 않을 가능성이 있으므로, 검증 화면에서만 사용한다.

---

# 7. 실제 사용자 화면과 검증 화면 구분

현재 Evidence Link 검증 화면은 개발/운영 검증용이므로 상세 정보가 많은 것은 허용된다.

하지만 기본 화면은 사람이 빠르게 이해 가능해야 한다.

기본 표시:
- 요약
- 핵심 근거

접힘 상세:
- Raw match reasons
- score details
- diff_excerpt

이 구조로 정리해.

---

# 8. 테스트

Frontend 중심.

확인:

1. `file_close_init 함수 변경 내역을 보여줘`
   - core에 file_close_init 포함
   - 내역/보여줘가 core에 포함되지 않음

2. file_path 입력:
   - file_save_mgt.c가 요청 파일로 표시됨

3. weak/ignored:
   - 함수, 변경, 내역, 보여줘가 약한 표현 또는 제외 표현으로 표시됨

4. Query Match 기본 표시가 요약형으로 나옴

5. Query Match 상세 접힘에서 raw reason 확인 가능

6. Link Match 기본 표시가 요약형으로 나옴

7. Link Score 상세 접힘에서 기존 match_reasons 확인 가능

8. 기존 Evidence Link 결과 수와 Ranking은 변경되지 않음

Frontend:

npm run build

Backend는 Query Intent 분류에 필요한 최소 수정 외에는 변경하지 마.
Link Score Weight, Gate, DB Schema 변경 금지.

---

# 9. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Gate 변경
- DB Schema 변경
- Evidence API 구조 대규모 변경
- 전체 UI 재설계

---

# 10. 완료 보고

1. core/weak 분류 수정 내용
2. 추가한 intent stopword/ignored term
3. file_path 표시 정책
4. Query Intent 표시 방식
5. Query Match 요약 방식
6. Query Match 상세 표시 방식
7. Link Match 요약 방식
8. Link Match 상세 표시 방식
9. score 숫자 강조도 변경 여부
10. Evidence Link Card 표시 순서
11. Frontend build 결과
12. Backend 수정 여부
13. Backend pytest 실행 여부
14. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

Evidence 검증 화면의 Query Intent 분류와 요약 표시를 정리했습니다. Link Score/Gate/검색 알고리즘은 그대로입니다.

### 완료 보고

1. **core/weak 분류**
   요청 표현(`내역/보여줘/알려줘` 등)·일반어는 weak. C 식별자·CamelCase는 `request_functions`, 업무어는 `query_keywords`, `file_path`는 `request_files`로 분리.

2. **추가 stopword**
   내역, 보여/보여줘/보여줘요, 알려/알려줘/알려줘요, 해줘, 줘, 좀, 대한/대해/관한, 요청/검색/조회/확인/설명, show/please/tell 등 (+ 조사·어미 prefix 규칙)

3. **file_path 표시**
   `request_files`로 분리 표시 (예: `file_save_mgt.c`, `file_save_mgt`) — core 목록에 섞지 않음

4. **Query Intent UI**
   요청 함수 / 요청 파일 / 핵심 업무어 / 제외·약한 표현 + core/weak 짧은 설명

5. **Query Match 요약**
   예: `요청 함수 file_close_init 일치`, `요청 파일 … 일치`

6. **Query Match 상세**
   `[Query Match 상세 보기]` 접힘에 raw reason 유지

7. **Link Match 요약**
   Primary 중심: 같은 파일 / 같은 함수 / Diff·제목 키워드

8. **Link Match 상세**
   `[Link Score 상세 보기]`에 type + score 유지

9. **score 강조**
   기본에서 숫자 강조 제거 → `[점수 상세 보기]`에 link_score / query_relevance / final_rank

10. **Card 순서**
    Rank·관련성·Primary → 제목 → Git → 문서/Slide → Query Match 요약 → Link Match 요약 → 상세 버튼

11. **Frontend build**
    **성공**

12. **Backend**
    Intent 분류·응답 필드(`request_functions`, `request_files`)만 최소 수정. Weight/Gate/Schema 미변경

13. **pytest**
    **312 passed**

14. **STEP 8**
    **미진행**

산출물: `package-deploy.py`로 deploy 현행화 완료.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Evidence 검증 화면의 Query Intent 분류와 요약 표시를 개선합니다. Search/Link Score/Gate는 유지하고, intent 분류와 UI만 손보겠습니다.
- Intent 분류를 분리·보강하고, Evidence UI는 요약+접힘 구조로 정리합니다.

- 사용 도구: TodoWrite×3, Read×11, Grep, StrReplace×15, Write×3, Shell×6, AwaitShell×2 (총 41회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [011]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #62  |  Tuesday, Jul 14, 2026, 2:11 PM (UTC+9)                      ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

Evidence Link 검증 화면에서 운영 테스트 중 Query Relevance 오판 사례를 확인했다.

## 문제 사례

장비:
휴대용정산기

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

실제 기대:
file_close_init 함수와 직접 관련된 Git/Change Item Evidence가 상위에 나와야 한다.

현재 결과:
1위 Evidence가 `후불기후동행카드 bin 2종 추가`로 표시됨.
이는 file_close_init 함수 변경과 직접 관련 없어 보인다.

화면상 Query Intent에서 file_path 입력 `common/lib/src/`가 `요청 파일: src`로 해석되었고, `src`가 core query relevance에 사용된 것으로 보인다.

이로 인해 `src`가 commit_message, git_file_path, source_function, raw_text 등에 반복 매칭되며 query_relevance가 과대 계산되고, 관련 없는 결과가 `관련성 높음`으로 올라온다.

이번 작업은 Query Relevance / Query Intent 처리 보완이다.

Search Algorithm 전체 재설계, Link Score Weight, Link Gate, DB Schema, STEP 8은 변경하지 마.

---

# 1. file_path 입력 해석 정책 수정

file_path 입력값을 무조건 파일명으로 해석하지 마.

다음 두 경우를 구분해.

## A. 파일 경로

예:

common/lib/src/file_save_mgt.c
common/lib/include/file_save_mgt.h
subwaylib/fare/src/fare_calc.c

파일 확장자 또는 명확한 파일명 패턴이 있으면:

- 요청 파일: file_save_mgt.c
- 요청 파일 stem: file_save_mgt

를 core query relevance로 사용할 수 있다.

## B. 디렉터리 경로

예:

common/lib/src/
common/lib/src
common/lib/
src/

파일 확장자가 없고 마지막 segment가 일반 디렉터리명인 경우:

- 요청 파일로 표시하지 마
- 마지막 segment를 core keyword로 사용하지 마
- `src`를 요청 파일로 표시하지 마

대신 필요하면 다음처럼 표시해.

검색 범위 경로:
common/lib/src/

디렉터리 경로는 Git 후보 검색 범위 보조 정보로 사용할 수는 있지만, Query Relevance를 강하게 올리는 core keyword로 사용하면 안 된다.

---

# 2. 일반 Path Segment Stopword 추가

다음과 같은 일반 디렉터리명은 core query keyword로 쓰지 마.

예:

- src
- source
- lib
- common
- include
- inc
- proc
- app
- device
- card
- fare
- util
- utils
- api
- test
- tests

단, 실제 파일명 stem인 경우는 조심해야 한다.

예:

card.c
fare.c

처럼 파일명 자체라면 무조건 제외하면 안 된다.

정책:

- file_path가 명확한 파일 경로일 때 filename/stem은 core 가능
- directory segment만으로 나온 `src`, `lib`, `common` 등은 core 금지

---

# 3. Query Relevance에서 Directory-only Path는 약하게 처리

사용자가 file_path에 directory path를 입력한 경우:

common/lib/src/

이 값은 다음 정도로만 사용해.

- Git Candidate 검색 범위 힌트
- git_file_path prefix/suffix 보조
- debug 표시

하지만 Query Match `높음`의 근거가 되면 안 된다.

특히 다음은 금지:

- `src matched in commit_message`
- `src matched in git_file_path`
- `src matched in source_function`
- `src matched in raw_text`

같은 이유만으로 Query Match 높음 처리.

---

# 4. Query Relevance 반복 누적 제한

현재 같은 core keyword가 여러 필드에서 반복 매칭되면 query_relevance가 과하게 커질 수 있다.

예:

src matched in commit_message
src matched in git_file_path
src matched in source_function
src matched in raw_text
...

이런 반복으로 unrelated 결과가 상위에 올라오면 안 된다.

정책을 검토해.

권장:

- 동일 keyword는 동일 Evidence Link 내에서 과도하게 반복 가산하지 않음
- field별 가중치를 주더라도 keyword별 최대 점수 cap 적용
- 일반 path segment는 아예 제외
- core keyword 중 함수명/파일명/업무 키워드만 높은 점수

예:

file_close_init
→ 함수명 core, 높은 relevance 가능

file_save_mgt.c
→ 파일명 core, 높은 relevance 가능

src
→ directory generic, relevance 제외 또는 매우 낮음

---

# 5. Query Intent 표시 개선

현재 표시:

요청 파일: src

이건 잘못이다.

수정 후 기대:

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

Query Intent 표시:

요청 함수:
file_close_init

검색 범위 경로:
common/lib/src/

제외/약한 표현:
함수, 변경, 내역, 보여줘

요청 파일:
없음

또는 요청 파일 영역은 표시하지 않음.

file_path가:

common/lib/src/file_save_mgt.c

인 경우에는:

요청 함수:
file_close_init

요청 파일:
file_save_mgt.c

검색 범위 경로:
common/lib/src/

정도로 표시 가능.

---

# 6. 이번 문제의 기대 결과

동일 입력:

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

수정 후 기대:

- `src`만 매칭된 Evidence가 관련성 높음으로 올라오지 않아야 함
- file_close_init 직접 매칭이 있는 Evidence가 우선되어야 함
- file_close_init이 없는 결과는 Query Match 낮음 또는 제외되어야 함
- 1위 결과가 후불기후동행 bin 추가처럼 무관한 항목이면 안 됨

---

# 7. Evidence Link Card 표시

Query Match 요약에서 다음처럼 보여야 한다.

좋은 예:

Query Match 높음
- 요청 함수 file_close_init 일치
- 변경내역서 소스/함수 항목에 file_close_init() 존재

나쁜 예:

Query Match 높음
- src matched in commit_message
- src matched in git_file_path
- src matched in raw_text

`src` 같은 일반 디렉터리명은 기본 Query Match 요약에 표시하지 마.

필요하면 Debug 상세에서만 확인 가능하게 해도 된다.

---

# 8. 테스트

Synthetic 데이터로 테스트해.

실제 내부 문서명/원문 사용 금지.

필수 테스트:

1. file_path = common/lib/src/
   - requested_file 없음
   - path_scope는 common/lib/src
   - src는 core keyword 아님

2. file_path = common/lib/src/file_save_mgt.c
   - requested_file = file_save_mgt.c
   - file_save_mgt는 core 가능

3. query = file_close_init 함수 변경 내역을 보여줘
   - core: file_close_init
   - weak/ignored: 함수, 변경, 내역, 보여줘

4. directory segment src만 매칭된 Evidence
   - Query Match 높음이 되지 않음

5. function file_close_init 직접 매칭 Evidence
   - Query Match 높음

6. same_file_path/same_function Link는 유지

7. 기존 link_score는 변경되지 않음

8. final ranking에서 directory-only token 때문에 unrelated result가 1위가 되지 않음

9. Query Intent UI에서 `요청 파일: src`가 표시되지 않음

10. Query Intent UI에서 directory path는 `검색 범위 경로`로 표시됨

Backend 수정 시:

python -m pytest tests/ -q

Frontend 수정 시:

npm run build

---

# 9. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Primary Evidence Gate 변경
- change_link Schema 변경
- 전체 검색 구조 재설계
- Parser 변경
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩

---

# 10. 완료 보고

다음을 보고해.

1. 기존에 `src`가 요청 파일로 잡힌 원인
2. file_path 파일/디렉터리 구분 정책
3. 요청 파일 추출 정책
4. 검색 범위 경로 표시 정책
5. 일반 path segment stopword 목록
6. Query Relevance 반복 누적 제한 여부
7. `src` 매칭으로 Query Match 높음이 되지 않는지
8. file_close_init 직접 매칭 우선 여부
9. Query Intent UI 변경 내용
10. 추가/수정 테스트
11. Backend pytest 결과
12. Frontend build 결과
13. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 디렉터리 `file_path`가 `src`로 core에 잡히는 문제를 고칩니다. 파일/디렉터리 구분과 Query Relevance 누적 제한부터 확인합니다.
- file_path 파일/디렉터리 구분과 Query Relevance 점수 cap을 구현합니다.

- 사용 도구: TodoWrite×2, Read×7, Grep, StrReplace×12, Shell×5, Write, AwaitShell×2 (총 30회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [012]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #63  |  Tuesday, Jul 14, 2026, 2:11 PM (UTC+9)                      ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 8은 아직 진행하지 마.

Evidence Link 검증 화면에서 운영 테스트 중 Query Relevance 오판 사례를 확인했다.

## 문제 사례

장비:
휴대용정산기

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

실제 기대:
file_close_init 함수와 직접 관련된 Git/Change Item Evidence가 상위에 나와야 한다.

현재 결과:
1위 Evidence가 `후불기후동행카드 bin 2종 추가`로 표시됨.
이는 file_close_init 함수 변경과 직접 관련 없어 보인다.

화면상 Query Intent에서 file_path 입력 `common/lib/src/`가 `요청 파일: src`로 해석되었고, `src`가 core query relevance에 사용된 것으로 보인다.

이로 인해 `src`가 commit_message, git_file_path, source_function, raw_text 등에 반복 매칭되며 query_relevance가 과대 계산되고, 관련 없는 결과가 `관련성 높음`으로 올라온다.

이번 작업은 Query Relevance / Query Intent 처리 보완이다.

Search Algorithm 전체 재설계, Link Score Weight, Link Gate, DB Schema, STEP 8은 변경하지 마.

---

# 1. file_path 입력 해석 정책 수정

file_path 입력값을 무조건 파일명으로 해석하지 마.

다음 두 경우를 구분해.

## A. 파일 경로

예:

common/lib/src/file_save_mgt.c
common/lib/include/file_save_mgt.h
subwaylib/fare/src/fare_calc.c

파일 확장자 또는 명확한 파일명 패턴이 있으면:

- 요청 파일: file_save_mgt.c
- 요청 파일 stem: file_save_mgt

를 core query relevance로 사용할 수 있다.

## B. 디렉터리 경로

예:

common/lib/src/
common/lib/src
common/lib/
src/

파일 확장자가 없고 마지막 segment가 일반 디렉터리명인 경우:

- 요청 파일로 표시하지 마
- 마지막 segment를 core keyword로 사용하지 마
- `src`를 요청 파일로 표시하지 마

대신 필요하면 다음처럼 표시해.

검색 범위 경로:
common/lib/src/

디렉터리 경로는 Git 후보 검색 범위 보조 정보로 사용할 수는 있지만, Query Relevance를 강하게 올리는 core keyword로 사용하면 안 된다.

---

# 2. 일반 Path Segment Stopword 추가

다음과 같은 일반 디렉터리명은 core query keyword로 쓰지 마.

예:

- src
- source
- lib
- common
- include
- inc
- proc
- app
- device
- card
- fare
- util
- utils
- api
- test
- tests

단, 실제 파일명 stem인 경우는 조심해야 한다.

예:

card.c
fare.c

처럼 파일명 자체라면 무조건 제외하면 안 된다.

정책:

- file_path가 명확한 파일 경로일 때 filename/stem은 core 가능
- directory segment만으로 나온 `src`, `lib`, `common` 등은 core 금지

---

# 3. Query Relevance에서 Directory-only Path는 약하게 처리

사용자가 file_path에 directory path를 입력한 경우:

common/lib/src/

이 값은 다음 정도로만 사용해.

- Git Candidate 검색 범위 힌트
- git_file_path prefix/suffix 보조
- debug 표시

하지만 Query Match `높음`의 근거가 되면 안 된다.

특히 다음은 금지:

- `src matched in commit_message`
- `src matched in git_file_path`
- `src matched in source_function`
- `src matched in raw_text`

같은 이유만으로 Query Match 높음 처리.

---

# 4. Query Relevance 반복 누적 제한

현재 같은 core keyword가 여러 필드에서 반복 매칭되면 query_relevance가 과하게 커질 수 있다.

예:

src matched in commit_message
src matched in git_file_path
src matched in source_function
src matched in raw_text
...

이런 반복으로 unrelated 결과가 상위에 올라오면 안 된다.

정책을 검토해.

권장:

- 동일 keyword는 동일 Evidence Link 내에서 과도하게 반복 가산하지 않음
- field별 가중치를 주더라도 keyword별 최대 점수 cap 적용
- 일반 path segment는 아예 제외
- core keyword 중 함수명/파일명/업무 키워드만 높은 점수

예:

file_close_init
→ 함수명 core, 높은 relevance 가능

file_save_mgt.c
→ 파일명 core, 높은 relevance 가능

src
→ directory generic, relevance 제외 또는 매우 낮음

---

# 5. Query Intent 표시 개선

현재 표시:

요청 파일: src

이건 잘못이다.

수정 후 기대:

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

Query Intent 표시:

요청 함수:
file_close_init

검색 범위 경로:
common/lib/src/

제외/약한 표현:
함수, 변경, 내역, 보여줘

요청 파일:
없음

또는 요청 파일 영역은 표시하지 않음.

file_path가:

common/lib/src/file_save_mgt.c

인 경우에는:

요청 함수:
file_close_init

요청 파일:
file_save_mgt.c

검색 범위 경로:
common/lib/src/

정도로 표시 가능.

---

# 6. 이번 문제의 기대 결과

동일 입력:

query:
file_close_init 함수 변경 내역을 보여줘

file_path:
common/lib/src/

수정 후 기대:

- `src`만 매칭된 Evidence가 관련성 높음으로 올라오지 않아야 함
- file_close_init 직접 매칭이 있는 Evidence가 우선되어야 함
- file_close_init이 없는 결과는 Query Match 낮음 또는 제외되어야 함
- 1위 결과가 후불기후동행 bin 추가처럼 무관한 항목이면 안 됨

---

# 7. Evidence Link Card 표시

Query Match 요약에서 다음처럼 보여야 한다.

좋은 예:

Query Match 높음
- 요청 함수 file_close_init 일치
- 변경내역서 소스/함수 항목에 file_close_init() 존재

나쁜 예:

Query Match 높음
- src matched in commit_message
- src matched in git_file_path
- src matched in raw_text

`src` 같은 일반 디렉터리명은 기본 Query Match 요약에 표시하지 마.

필요하면 Debug 상세에서만 확인 가능하게 해도 된다.

---

# 8. 테스트

Synthetic 데이터로 테스트해.

실제 내부 문서명/원문 사용 금지.

필수 테스트:

1. file_path = common/lib/src/
   - requested_file 없음
   - path_scope는 common/lib/src
   - src는 core keyword 아님

2. file_path = common/lib/src/file_save_mgt.c
   - requested_file = file_save_mgt.c
   - file_save_mgt는 core 가능

3. query = file_close_init 함수 변경 내역을 보여줘
   - core: file_close_init
   - weak/ignored: 함수, 변경, 내역, 보여줘

4. directory segment src만 매칭된 Evidence
   - Query Match 높음이 되지 않음

5. function file_close_init 직접 매칭 Evidence
   - Query Match 높음

6. same_file_path/same_function Link는 유지

7. 기존 link_score는 변경되지 않음

8. final ranking에서 directory-only token 때문에 unrelated result가 1위가 되지 않음

9. Query Intent UI에서 `요청 파일: src`가 표시되지 않음

10. Query Intent UI에서 directory path는 `검색 범위 경로`로 표시됨

Backend 수정 시:

python -m pytest tests/ -q

Frontend 수정 시:

npm run build

---

# 9. 금지

- STEP 8
- Ollama
- LLM Prompt
- Continue 연동
- Link Score Weight 변경
- Primary Evidence Gate 변경
- change_link Schema 변경
- 전체 검색 구조 재설계
- Parser 변경
- 실제 내부 문서명/원문을 테스트 Fixture에 하드코딩

---

# 10. 완료 보고

다음을 보고해.

1. 기존에 `src`가 요청 파일로 잡힌 원인
2. file_path 파일/디렉터리 구분 정책
3. 요청 파일 추출 정책
4. 검색 범위 경로 표시 정책
5. 일반 path segment stopword 목록
6. Query Relevance 반복 누적 제한 여부
7. `src` 매칭으로 Query Match 높음이 되지 않는지
8. file_close_init 직접 매칭 우선 여부
9. Query Intent UI 변경 내용
10. 추가/수정 테스트
11. Backend pytest 결과
12. Frontend build 결과
13. STEP 8 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

디렉터리 `file_path`가 `src`로 core에 잡히던 문제를 막았습니다. Link Score/Gate는 그대로입니다.

### 완료 보고

1. **원인**
   `common/lib/src/`를 `Path.name`으로만 해석해 `src`를 요청 파일/core로 취급 → 여러 필드에 `src`가 반복 매칭되며 query_relevance가 과대 계산됨.

2. **파일/디렉터리 구분**
   코드 확장자 있으면 파일, trailing `/` 또는 확장자 없으면 디렉터리 (`parse_file_path_input`).

3. **요청 파일 추출**
   파일일 때만 `name` + `stem`을 `request_files`에 추가. 디렉터리면 추가하지 않음.

4. **검색 범위 경로**
   디렉터리(및 파일의 parent)는 `path_scopes`로 표시. core keyword로는 사용하지 않음(약힌 path_scope 힌트만).

5. **Path segment stopword**
   `src, source, lib, common, include, inc, proc, app, device, card, fare, util(s), api, test(s), ...`
   파일 stem(`card.c`)은 파일 경로일 때 허용.

6. **반복 누적 제한**
   **적용.** 동일 keyword core 점수 **cap 50**. generic segment core 매칭 제거.

7. **`src`로 높음?**
   **아님.** directory-only 매칭은 관련성 낮음/없음 + Gate 미통과.

8. **`file_close_init` 우선**
   **예.** 함수 직접 매칭만 관련성 높음 + Gate 통과.

9. **Query Intent UI**
   요청 파일(있을 때만) / **검색 범위 경로** / 요청 함수 / 약한 표현. `요청 파일: src` 제거.

10. **테스트**
    directory/file 파싱, src 비고, function 높음, score cap 등 추가·수정.

11. **pytest**
    **318 passed**

12. **Frontend build**
    **성공**

13. **STEP 8**
    **미진행**

산출물 deploy 현행화 완료. 서버 재시작 후 동일 케이스로 재검증하면 됩니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 사용 도구: Read, TodoWrite (총 2회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [013]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #64  |  Wednesday, Jul 15, 2026, 10:28 AM (UTC+9)                   ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
STEP 8은 아직 진행하지 마.

Evidence Link 검증 화면 테스트 결과 Query Intent 분류가 전보다 좋아졌지만,
query `file_close_init 함수 변경 내역을 보자`에서 `보자`가 핵심 업무어로 분류되는 문제가 확인됐다.

`보자`는 검색 의도어가 아니라 사용자 요청 표현이므로 core/business keyword에 포함되면 안 된다.

다음 표현들을 Evidence Query Intent의 ignored/weak request expression으로 추가해.

- 보자
- 보자고
- 보여줘
- 보여줘요
- 보여
- 알려줘
- 알려줘요
- 찾아줘
- 찾아줘요
- 확인해줘
- 확인
- 내역
- 내역을
- 목록
- 목록을

단 C 함수명, 파일명, 숫자+업무 키워드는 기존대로 유지한다.

예상 결과:

query:
file_close_init 함수 변경 내역을 보자

core/requested function:
file_close_init

weak/ignored:
함수, 변경, 내역, 보자

business keyword:
없음

`보자`가 핵심 업무어에 표시되면 안 된다.

기존 Link Score Weight, Gate, Evidence Ranking, DB Schema는 변경하지 마.
STEP 8도 진행하지 마.

테스트:
1. `file_close_init 함수 변경 내역을 보자`
   - 보자 core 아님
   - 보자 business keyword 아님
   - file_close_init 요청 함수 유지

2. `영수증 변경사항 보자`
   - 영수증 core
   - 변경사항/보자 weak 또는 ignored

3. `15분 재승차 내역을 보여줘`
   - 15분, 재승차 core
   - 내역, 보여줘 ignored

Frontend build와 필요한 Backend test 결과를 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

요청 표현어를 `EVIDENCE_QUERY_STOPWORDS`에 추가했습니다. Link Score / Gate / Ranking / Schema / STEP 8은 변경하지 않았습니다.

### 원인
`보자`가 stopword 목록에 없어 `_KOREAN_RE`로 추출된 뒤 `query_keywords`(핵심 업무어)로 분류됨.

### 변경
`backend/app/services/query_relevance_service.py`에 추가:

- `보자`, `보자고`
- `찾아`, `찾아줘`, `찾아줘요`
- `확인해줘`
- `내역을`, `목록`, `목록을`

기존 항목(`보여`, `보여줘`, `보여줘요`, `알려줘`, `알려줘요`, `확인`, `내역`)은 유지. 접미사 형태(`내역을`, `보자고` 등)는 기존 prefix 규칙으로 weak 처리.

### 테스트 결과

| 쿼리 | 기대 | 결과 |
|------|------|------|
| `file_close_init 함수 변경 내역을 보자` | `file_close_init` 요청 함수, `보자` 비-core | ✅ |
| `영수증 변경사항 보자` | `영수증` core, `변경사항`/`보자` weak | ✅ |
| `15분 재승차 내역을 보여줘` | `15분`/`재승차` core, `내역`/`보여줘` weak | ✅ |

- **Backend pytest** (`test_query_relevance.py`): **20 passed**
- **Frontend build**: **성공** (코드 변경 없음, 회귀 확인용)
- **산출물 deploy**: 현행화 완료

서버 재시작 후 Evidence Link 검증 화면에서 `file_close_init 함수 변경 내역을 보자` 입력 시 **핵심 업무어: 없음**, **요청 함수: file_close_init**, **제외/약한 표현: 함수, 변경, 내역, 보자**로 표시되어야 합니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Query Intent의 weak/ignored 표현 목록을 찾아 `보자` 등 요청 표현이 core/business로 분류되지 않도록 수정합니다.
- `보자` 등이 stopword 목록에 없어 business keyword로 분류되고 있습니다. 목록에 추가하고 테스트를 작성합니다.

- 사용 도구: Grep×2, Read×3, StrReplace×2, Shell×5 (총 12회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [014]  STEP 7 — Git-PPT 근거 연계                                               ║
║  메인 turn #65  |  Tuesday, Jul 21, 2026, 10:58 AM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
STEP 8은 아직 진행하지 마.

Evidence Query Intent 테스트 결과가 전반적으로 좋아졌지만,
`file_close_init 함수의 변경 이력을 보자`에서 `이력` 또는 `이력을`이 핵심 업무어로 분류되는 문제가 남아 있다.

다음 표현은 검색 핵심어/core/business keyword로 사용하지 말고 weak/ignored 표현으로 처리해.

- 이력
- 이력을
- 내역
- 내역을
- 변경이력
- 변경이력을
- 변경내역
- 변경내역을
- 사항
- 사항을
- 내용
- 내용을

예상 결과:

query:
file_close_init 함수의 변경 이력을 보자

요청 함수:
file_close_init

핵심 업무어:
없음

제외/약한 표현:
함수, 변경, 이력, 보자

기존 Link Score, Gate, Ranking, DB Schema는 변경하지 마.
STEP 8은 진행하지 마.

테스트:
1. `file_close_init 함수의 변경 이력을 보자`
   - file_close_init은 요청 함수
   - 이력/이력을은 core 아님
   - 보자는 core 아님

2. `영수증 변경내역을 보여줘`
   - 영수증은 core
   - 변경내역/보여줘는 ignored 또는 weak

3. `15분 재승차 변경사항 알려줘`
   - 15분, 재승차는 core
   - 변경사항/알려줘는 ignored 또는 weak

Frontend build와 필요한 Backend test 결과를 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

`이력`·`변경이력` 계열을 weak/ignored로 추가했습니다. Link Score / Gate / Ranking / Schema / STEP 8은 변경하지 않았습니다.

### 원인
`이력`이 stopword에 없어 `_KOREAN_RE`로 추출된 뒤 핵심 업무어로 분류됨. `변경내역`처럼 붙여 쓴 복합어도 별도 등록이 필요했음.

### 추가 stopword
`이력`, `이력을`, `변경이력`, `변경이력을`, `변경내역`, `변경내역을`, `사항을`, `내용을` (+ 기존 `내역`/`사항`/`내용` 유지)

### 테스트

| 쿼리 | 기대 | 결과 |
|------|------|------|
| `file_close_init 함수의 변경 이력을 보자` | 요청 함수만, 이력/보자 비-core | ✅ |
| `영수증 변경내역을 보여줘` | 영수증 core, 변경내역/보여줘 weak | ✅ |
| `15분 재승차 변경사항 알려줘` | 15분·재승차 core, 변경사항/알려줘 weak | ✅ |

- **Backend pytest** (`test_query_relevance.py`): **23 passed**
- **Frontend build**: **성공**
- **산출물 deploy**: 현행화 완료
- **STEP 8**: 미진행

### ◇ 진행 과정 요약（도구·짧은 안내만）

- `이력`·`변경이력` 등이 core로 잡히지 않도록 stopword 목록을 보강하고 테스트를 추가합니다.
- `이력`·`변경이력` 등 복합어가 통째로 추출되는 경우를 포함해 stopword를 보강합니다.

- 사용 도구: Read, Grep, StrReplace×2, Shell×3 (총 7회)

---
