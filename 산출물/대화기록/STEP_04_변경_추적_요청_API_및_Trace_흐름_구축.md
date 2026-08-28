# STEP 4. 변경 추적 요청 API 및 Trace 흐름 구축

> **범위**: Cursor 메인 개발 대화 turn **#5 ~ #5** （1턴）
> **이 STEP 요지**: Trace 검색·후보 랭킹 등 변경 추적 요청 흐름

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #5 — md파일을 업데이트 했어 변경된 파일은 @AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 4 — 변경 추적 요청 API 및 Trace 흐름 구축                                  ║
║  메인 turn #5  |  Monday, Jul 6, 2026, 2:08 PM (UTC+9)                         ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
md파일을 업데이트 했어 변경된 파일은 @AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md 파일이야.

프로젝트 방향이 기존의 전체 PPT 사전 분석 및 웹 통합 검색 중심 구조에서, VSCode Continue에서 변경 사유를 질문하는 사용 시나리오 중심 구조로 변경되었다.

새 md파일을 처음부터 끝까지 다시 검토해.

STEP 0~3은 현재 완료된 구현을 유지한다.
새 방향에 맞춘다는 이유로 기존 STEP 0~3 기능을 임의로 재작성하거나 대규모 리팩터링하지 마.

기존 STEP 4 계획은 폐기한다.

새 PROJECT_SPEC.md의 STEP 4인 "변경 추적 요청 API 및 Trace 흐름 구축"만 구현해.

이번 STEP에서는 PPT Parsing, PPT Cache, Git-PPT 연계, Ollama, Continue 연계 기능을 구현하지 마.

구현 완료 후 PROJECT_SPEC.md의 Cursor 단계별 완료 보고 형식에 따라 결과를 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 4 완료 보고

## 프로젝트 방향 변경 이해 (v2)

| 구분 | 기존 | v2 |
|---|---|---|
| 핵심 UX | 웹 통합 검색 | **VSCode Continue** 자연어 질문 |
| PPT | 전체 사전 분석 | **On-demand + Cache** |
| Web UI | 검색 중심 | **관리/검증** 보조 |
| STEP 0~3 | — | **유지** (재작성 없음) |
| 구(舊) STEP 4 | PPT 사전 분석 | **폐기** |

---

## 1. 구현한 기능

- **`POST /api/trace/search`** — 변경 추적 요청 API
- **Git Candidate 검색** — DB Git 이력 기반 점수화·Top 5 반환
- **규칙 기반 Keyword 추출** — LLM 미사용
- **Search Context 생성** — PPT 후보 탐색용 (STEP 5 준비)
- **Logging** — Trace search 시작/완료

**미구현 (의도적):** PPT Parsing, Cache, Git-PPT 연계, Ollama, Continue

---

## 2. 생성 또는 수정한 파일

| 구분 | 파일 |
|---|---|
| Config | `backend/app/core/trace_config.py` |
| Schema | `backend/app/schemas/trace.py` |
| Service | `backend/app/services/trace_service.py`, `keyword_extractor.py` |
| API | `backend/app/api/trace.py`, `main.py` |
| Tests | `backend/tests/test_trace.py` |
| Docs | `README.md`, `TEST_PLAN.md` |

---

## 3. 핵심 구현 방식

### API

```http
POST /api/trace/search
```

```json
{
  "equipment_id": 1,
  "query": "CalcFare 함수가 왜 변경됐어?",
  "file_path": "FareCalc.c",
  "selected_code": "optional"
}
```

### Candidate Score (`TRACE_SCORE_CONFIG`)

| 항목 | 점수 | match_reason |
|---|---|---|
| 현재 파일 일치 | 30 | `file_path` |
| Symbol 일치 (diff) | 25 | `diff_symbol` |
| Commit Message Keyword | 20 | `commit_message_keyword` |
| Diff Keyword | 20 | `diff_keyword` |
| 파일명 Context | 5 | `query_keyword` |

- 상한 100, **Top 5** 반환
- 정렬: `score DESC` → `commit_date DESC`

### Keyword 추출 (규칙 기반)

- C/C++ Identifier, `UPPER_SNAKE` Symbol
- 파일명/ stem (`file_path`)
- 한글 2자 이상 (`어린이`, `요금`)
- `selected_code`에서 Symbol 추출
- 한글 조사 붙은 Symbol: `CHILD_FARE가` → `CHILD_FARE` (loose regex)

### Search Context

- **keywords**: query 추출 + 상위 Candidate 파일명/Symbol 병합
- **date_from / date_to**: 상위 Candidate Commit Date ± **90일**

---

## 4. 실행 방법

```bat
scripts\start-dev.bat
```

```powershell
# 1. 장비 등록 + Git 동기화 (변경 이력 탭 또는 API)
# 2. Trace 요청
Invoke-RestMethod -Method POST -Uri http://localhost:8010/api/trace/search `
  -ContentType "application/json" `
  -Body '{"equipment_id":1,"query":"CHILD_FARE가 왜 추가됐어?","file_path":"FareCalc.c"}'
```

---

## 5. 테스트 방법

```bat
scripts\test-backend.bat
# 67 passed
```

---

## 6. 테스트 결과

| 테스트 | 결과 |
|---|---|
| CHILD_FARE / CalcFare / 어린이 카드 | **PASS** |
| file_path → FareCalc.c 우선 | **PASS** |
| selected_code → Symbol 추출 | **PASS** |
| search_context keywords/date | **PASS** |
| match_reasons 포함 | **PASS** |
| equipment 404 | **PASS** |
| Git 미동기화 → 빈 candidates | **PASS** |
| **pytest 전체** | **67 passed** |

**테스트 실패 이력:** 없음

---

## 7. 현재 제한 사항

- PPT 후보 탐색/분석 — **STEP 5~6**
- Ollama 분석 — **STEP 8**
- Continue 연계 — **STEP 9+**
- Trace API는 **Git Candidate + Context**만 반환 (최종 답변 없음)
- Keyword 추출은 규칙 기반 (NLP/LLM 없음)
- Frontend Trace UI 없음 (Backend API만, Web UI는 STEP 0~3 유지)

---

## 8. 다음 STEP 진행 전 확인 사항

**STEP 5: Git 기반 PPT 후보 탐색**

1. `equipment.document_path` 재귀 `.pptx` 탐색
2. Search Context(keywords, date range)로 **파일명/수정일** 기반 후보 점수
3. PPT **내용 Parsing은 아직 하지 않음** (파일 메타만)
4. `~$*.pptx`, `.ppt` 제외

---

STEP 5 진행을 원하시면 말씀해 주세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- 새 PROJECT_SPEC v2를 검토하고 STEP 4 범위만 확인합니다.
- STEP 4 Trace API 구현을 시작합니다. 기존 STEP 0~3 코드는 유지합니다.

- 사용 도구: Grep×2, Read×9, Glob, Write×6, StrReplace×10, Shell×2 (총 30회)

---
