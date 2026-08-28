# STEP 8. Ollama 근거 기반 변경 사유 분석

> **범위**: Cursor 메인 개발 대화 turn **#66 ~ #71** （6턴）
> **이 STEP 요지**: Ollama(선택) 근거 기반 변경 사유 문장 생성

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #66 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세 파일로 사용해.…
2. 메인 #67 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
3. 메인 #68 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
4. 메인 #69 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
5. 메인 #70 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…
6. 메인 #71 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해. ST…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #66  |  Tuesday, Jul 21, 2026, 11:17 AM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세 파일로 사용해.

기존 `PROJECT_SPEC.md` 또는 이전 명세와 충돌하면 v2 명세를 우선 적용해.

이제 STEP 8을 진행한다.

# STEP 8
Ollama 기반 Evidence Grounded Answer 생성

STEP 7 운영 검증 결과:

- Evidence API 정상 동작
- Git Candidate / Change Item Candidate / Evidence Link 생성 확인
- same_file_path, same_function_exact 등 Primary 근거 확인
- Query Match와 Link Match 분리 확인
- 장비 불일치 문서 필터링 적용
- Query Relevance 개선
- `file_close_init 함수 변경 이력` 테스트에서 적절한 Evidence Link 확인
- 관련성이 낮은 Strong Link가 상위에 올라오는 문제 개선
- Query Intent에서 요청 함수 / 검색 범위 / 약한 표현 분리 확인

이제 STEP 8에서는 STEP 7 Evidence Set을 기반으로 Ollama가 사용자에게 읽기 쉬운 답변을 생성하도록 구현한다.

중요:

- STEP 8은 LLM 답변 생성 단계다.
- Evidence 검색/연결 로직을 다시 설계하지 마.
- Link Score Weight 변경 금지.
- Query Relevance Gate 변경 금지.
- change_link Schema 변경 금지.
- Parser 변경 금지.
- Cache 구조 변경 금지.
- STEP 9 Continue 연동은 아직 진행하지 마.

---

# 1. STEP 8 목표

사용자 질문:

예:

`file_close_init 함수 변경 이력을 보여줘`

현재 STEP 7 Evidence 결과:

- Git Candidate
- Change Item Candidate
- Evidence Link
- Query Match
- Link Match
- match_reasons
- diff_excerpt

STEP 8 목표:

위 Evidence를 바탕으로 다음 형태의 답변을 생성한다.

예상 답변 개념:
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

Deploy is fully in sync. STEP 8 backend + UI implementation is complete.

## 완료 보고

### 구현 내용 (STEP 8: Ollama 근거 기반 Evidence Grounded Answer)

**흐름 준수**: `query → Git Search → PPT 후보 → Cache → Git-PPT Link → 상위 Evidence 선정 → Ollama` — STEP 7의 `build_evidence()`를 그대로 재사용하고, 그 결과(Top Evidence Link)만 Ollama에 전달합니다. Search/Link/Gate 로직은 재실행/재설계하지 않았습니다.

**신규 파일**
- `backend/app/services/ollama_service.py` — Context 생성, Ollama 호출(`httpx`), JSON 파싱, 장애 처리
- `backend/app/schemas/analysis.py`, `backend/app/api/analysis.py` — `POST /api/trace/analyze`
- `frontend/src/api/analysis.ts`, `EvidenceLinkViewer.tsx`/`.css`에 AI 분석 패널 추가

**핵심 정책**
1. **근거 선정**: Evidence Link Top `OLLAMA_MAX_EVIDENCE`(기본 3)개. 없으면 Query 관련성 "높음/보통"인 Git만(문서 근거 없음 명시). 둘 다 없으면 **Ollama 호출 자체를 생략**하고 결정론적 "확인 불가" 반환 — 근거 없는 사유 생성을 원천 차단.
2. **Evidence 신뢰성**: 사용자에게 보이는 `evidence`(Commit/File/Slide)는 항상 **서버가 실제로 Ollama에 보낸 근거에서 직접 도출** — AI가 응답한 evidence 필드는 참고만 하고 신뢰하지 않음(할루시네이션 방지, "Evidence 누락 감지"는 로그로 기록).
3. **장애 격리**: Timeout/연결 실패/JSON 파싱 실패 모두 500 에러로 전파되지 않고 `ai_available=false` 또는 `parse_error=true`로 degrade. Git/PPT Evidence는 항상 그대로 반환(원칙 13).
4. **Prompt 크기**: diff는 기존 STEP 7의 windowed `diff_excerpt`(±5줄)만 사용, 전체 Diff/전체 PPT는 전달하지 않음(원칙 15/16/17).
5. **로그**: `Ollama Request`/`Ollama Error`만 기록, Full Prompt/전체 Diff는 기록하지 않음.

**금지 항목 확인**: Link Score Weight/Gate/Ranking/`change_link` Schema/Parser/Cache 구조 변경 없음. STEP 9(Continue) 연동/MCP/Tool wiring은 진행하지 않음 — `/api/trace/analyze`는 STEP 9 스펙에 계약으로만 언급된 "Backend 핵심 API"이며, 이번 작업은 이 백엔드 엔드포인트만 구현했습니다.

### 테스트
- `test_ollama_service.py` (신규 23개): 근거 없음 skip, 정상 응답, Git-only, 관련성 낮은 Git 무시, JSON 외 텍스트 혼합, 잘못된 JSON, Timeout, 연결 실패, 한글 답변, confidence 값 검증, evidence 누락 감지, 전체 diff 미포함 등
- `test_analysis_api.py` (신규): `/api/trace/analyze` 정상/무근거/AI장애/파싱오류/404/422, `/evidence`와 Link Score 동일성 검증

### Backend pytest
**347 passed** (전체 스위트, 회귀 없음)

### Frontend build
**성공** — `tsc -b && vite build` 통과, 새 AI 분석 패널 포함

### 산출물
`package-deploy.py` 재실행 완료 — `deploy/backend/app/{api,services,schemas}/…`, `.env.example`(OLLAMA_ENABLED/TIMEOUT/MAX_EVIDENCE 추가), `frontend/dist` 모두 현행화됨. `00_읽어보세요.md`/`테스트_체크리스트.md`/`OPERATING_TEST_STEP6.md`는 기존에 API 레벨 절차를 다루지 않아 구조 충돌 없음(수정 불필요).

### STEP 9
미진행 (Continue/MCP 연동 없음).

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Now let's add Ollama configuration and build the STEP 8 service.
- Now the core Ollama service:
- Now the schema and API layer:
- Now let's check the linter and write backend tests.
- Now let's write the tests for `ollama_service.py` and the `/api/trace/analyze` endpoint. Let's first check how existing tests set up equipment/git/change_item fixtures (for the API-level test).
- Good, these fixtures exist. Now let's write the unit tests for `ollama_service.py`.
- Now the API-level integration test for `/api/trace/analyze`:
- Now let's run these two new test files.

- 사용 도구: Grep×5, Read×19, Shell×5, Glob×3, StrReplace×11, Write×6, ReadLints×2, AwaitShell (총 52회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [002]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #67  |  Wednesday, Jul 22, 2026, 12:08 PM (UTC+9)                   ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 9는 아직 진행하지 마.

STEP 8 운영 테스트 중 문제를 확인했다.

## 문제

Evidence 검증 화면에서 `AI 분석 실행 (STEP 8)`을 실행하면 다음처럼 표시된다.

- 확신도 알 수 없음
- 응답 형식 오류
- Git 근거와 변경내역서 근거만 일부 표시
- 자연어 답변 또는 fallback 답변이 명확히 표시되지 않음

테스트 입력:

query:
file_close_init 함수 변경 이력을 보여줘

Evidence Link 1위는 정상적으로 보인다.

- Change Item: 시간초과 하차 거래 데이터 변경
- Query Match: 높음
- Primary 3
- same_file_path
- same_function_exact
- Commit 메시지에 file_close_init 포함

따라서 Evidence는 충분하다.

문제는 STEP 8 Answer 표시/파싱/Degrade 처리 쪽으로 보인다.

---

# 1. Ollama JSON parse error 시 fallback answer를 반드시 표시

Ollama가 JSON 형식으로 응답하지 못하거나 JSON parsing이 실패해도 사용자 화면에는 자연어 fallback 답변이 표시되어야 한다.

현재처럼 `응답 형식 오류`만 보이고 실제 답변이 보이지 않으면 안 된다.

Fallback 답변 예:

가장 관련 높은 변경 항목은 `시간초과 하차 거래 데이터 변경`입니다.

연결 근거:
- Git 변경 파일과 변경내역서의 소스 파일이 file_save_mgt.c로 일치합니다.
- 변경내역서의 소스/함수 항목에 file_close_init()이 포함되어 있습니다.
- Commit 메시지에도 file_close_init이 포함되어 있습니다.

근거:
- Commit b46aceb
- 프로그램변경내역서_20200619_V130_V209_휴대용정산기.pptx, Slide 3

Ollama parse error는 debug 또는 상태 표시로만 보여주고, 답변 영역은 fallback으로 채워라.

---

# 2. confidence는 Ollama parse 성공 여부와 분리

현재 화면에 `확신도 알 수 없음`이 표시된다.

하지만 Evidence 1위가 Query Match 높음 + Primary 3이면 rule-based confidence는 high가 되어야 한다.

Confidence는 Ollama가 만든 JSON 값에 의존하지 말고, 서버 Evidence 기준 Rule로 계산해라.

Ollama 응답 파싱 실패 시에도 다음처럼 표시되어야 한다.

- 신뢰도: 높음
- AI 응답 상태: 응답 형식 오류, fallback 표시

즉 parse_error 때문에 confidence가 unknown/null이 되면 안 된다.

---

# 3. answer_status 정리

현재 `응답 형식 오류` 상태가 사용자에게 너무 기술적으로 보인다.

상태는 내부적으로 parse_error를 유지해도 되지만 UI 표시를 개선해라.

권장:

Backend:
- answer_status = partial 또는 ollama_parse_error
- parse_error = true
- answer = fallback answer

Frontend:
- 표시: `AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다.`
- 신뢰도는 Evidence 기준 표시
- debug에는 parse_error 표시 가능

---

# 4. AI가 준 evidence는 신뢰하지 말고 서버 evidence를 쓰는 정책 유지

기존 완료보고 정책은 좋다.

- 사용자에게 보이는 evidence는 서버가 실제 Ollama에 보낸 근거에서 도출
- AI가 응답한 evidence 필드는 참고만 함

이 정책은 유지해.

이번 수정은 parse error fallback과 UI 표시 문제다.

---

# 5. 전체 답변 보기 버튼 확인

현재 `[전체 답변 보기]` 버튼이 보인다.

이 버튼을 눌러야만 답변이 보이는 구조라면 UX가 좋지 않다.

기본 Answer Panel에는 최소 요약 답변이 바로 보여야 한다.

`전체 답변 보기`는 긴 답변 또는 raw AI response 확인용으로만 사용해라.

Fallback 답변은 기본으로 표시되어야 한다.

---

# 6. Ollama Prompt의 JSON 응답 안정성도 점검

가능하면 Prompt에서 JSON-only 응답을 더 강하게 유도해라.

단 JSON parse가 실패해도 fallback이 있으므로 API가 깨지면 안 된다.

검토:

- Ollama 응답 앞뒤 설명 텍스트 제거 처리
- ```json code fence 제거 처리
- JSON object extraction
- 잘못된 JSON일 경우 fallback

이미 일부 구현되어 있다면 회귀 확인만 해라.

---

# 7. 테스트

Backend 테스트 추가/수정:

1. Ollama가 plain text로 응답
   - parse_error true
   - answer는 fallback으로 채워짐
   - confidence는 evidence 기준 high/medium/low 유지

2. Ollama가 잘못된 JSON 응답
   - fallback answer 표시
   - API 200
   - evidence/citations 유지

3. Evidence high + parse error
   - confidence high 유지

4. Evidence 없음 + parse error
   - no_evidence 또는 확인 불가 유지

Frontend 확인:

1. parse_error 상태에서도 답변 본문 표시
2. `확신도 알 수 없음` 대신 Evidence 기준 신뢰도 표시
3. 사용자 메시지는 기술 용어보다 이해 가능한 문구
4. Git 근거 / 변경내역서 근거 유지
5. 기존 Evidence Link 화면 회귀 없음

Backend:
python -m pytest tests/ -q

Frontend:
npm run build

---

# 8. 금지

- STEP 9
- Continue 연동
- Link Score Weight 변경
- Query Relevance 변경
- Evidence Ranking 변경
- Parser 변경
- Cache 변경
- 전체 UI 재설계

---

# 완료 보고

다음을 보고해.

1. parse_error 시 기존 동작
2. fallback answer가 안 보인 원인
3. 수정 후 answer_status
4. parse_error 시 answer 필드 정책
5. confidence 계산 위치
6. parse_error 시 confidence 유지 여부
7. Frontend 표시 문구
8. 전체 답변 보기 버튼 정책
9. 추가/수정 Backend Test
10. Frontend build 결과
11. Backend pytest 결과
12. STEP 9 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

parse_error 시에도 Evidence 기반 fallback 답변·신뢰도가 바로 보이도록 수정했습니다. STEP 9 / Link Score / Query Relevance는 건드리지 않았습니다.

### 완료 보고

1. **기존 parse_error 동작**
   `summary/reason=None`, `confidence=unknown`, `answer`에 “응답 형식 오류…” 메시지만 넣고 Evidence refs만 붙임.

2. **fallback이 안 보인 원인**
   - Backend가 의미 있는 fallback 본문을 만들지 않음
   - Frontend가 `summary` 없을 때(특히 parse_error) 본문을 숨기고, 실제 `answer`는 **전체 답변 보기** 뒤에만 둠

3. **수정 후 `answer_status`**
   `ok` | `partial` | `ollama_parse_error` | `ollama_unavailable` | `ollama_disabled` | `no_evidence`

4. **parse_error 시 `answer` 정책**
   Evidence Link 1위 기준으로 fallback 생성 (제목 + 연결 근거 + Commit/문서·Slide). `parse_error=true` 유지.

5. **confidence 계산 위치**
   서버 `compute_evidence_confidence()` — Query Match 수준 + Primary 개수. **Ollama JSON confidence 무시**.

6. **parse_error 시 confidence**
   **유지.** Query Match 높음 + Primary ≥1 → `high`.

7. **Frontend 문구**
   - `신뢰도 높음/보통/낮음`
   - `AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다.`
   - summary/reason 기본 표시

8. **전체 답변 보기**
   요약은 기본 노출. 버튼은 긴 `answer` 전문 확인용.

9. **테스트**
   plain text / bad JSON → fallback + high confidence, fence 파싱, Ollama confidence 무시, API 200 등.

10. **Frontend build** — **성공**

11. **Backend pytest** — **348 passed**

12. **STEP 9** — **미진행**

산출물 deploy 현행화 완료. 서버 재시작 후 동일 케이스로 재검증하면 됩니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- parse_error 시 fallback 답변·Evidence 기준 confidence·UI 표시를 점검하고 수정합니다.
- `ollama_service`에 Evidence 기반 fallback·confidence·answer_status를 넣고, Frontend는 기본 답변 표시로 수정합니다.
- 테스트를 새 fallback/confidence 정책에 맞게 수정·추가합니다.

- 사용 도구: Read×8, Grep×3, TodoWrite×3, Write, StrReplace×8, Shell×4, AwaitShell (총 28회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [003]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #68  |  Wednesday, Jul 22, 2026, 3:51 PM (UTC+9)                    ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 9는 아직 진행하지 마.

STEP 8 운영 테스트 결과를 공유한다.

현재 Evidence 검색과 fallback은 정상 동작한다.

확인된 정상 동작:
- 존재하지 않는 함수 query는 no_evidence / 신뢰도 낮음으로 처리됨
- Evidence가 있는 file_close_init query는 fallback 답변으로 관련 변경 항목, Commit, 문서/Slide가 표시됨
- parse_error 또는 Ollama timeout이 API 500으로 전파되지 않음
- Evidence Link 결과는 계속 표시됨

하지만 Ollama 실제 응답 쪽에서 문제가 있다.

## 문제 1. JSON parse 실패가 자주 발생

서버 콘솔에 다음 로그가 반복된다.

`Ollama response JSON parse failed - using evidence fallback`

Ollama가 응답은 했지만 서버가 기대한 JSON 형식으로 응답하지 못하는 것으로 보인다.

현재 내부 모델은 qwen3.5:9b이다.

이 모델이 JSON strict format을 안정적으로 지키지 못할 수 있으므로, STEP 8 응답 처리 방식을 더 현실적으로 보완해라.

---

# 1. Ollama 응답을 JSON-only로 강제하지 않는 방향 검토

현재는 Ollama 응답 JSON 파싱에 실패하면 fallback으로 내려간다.

하지만 실제 필요한 것은 자연어 답변 본문이다.

따라서 다음 중 더 안정적인 방식을 선택해라.

## 권장 방식 A: Markdown answer mode

Ollama에게 JSON을 요구하지 말고, Evidence 기반 한국어 Markdown 답변만 생성하게 한다.

서버는 다음 필드를 계속 직접 만든다.

- answer_status
- confidence
- citations
- evidence links
- debug
- ai_available
- parse_error 여부

Ollama는 answer 문자열만 만든다.

즉 AI가 만든 evidence/confidence/status를 신뢰하지 않는다.

## 대안 방식 B: JSON 우선 + plain text fallback

Ollama 응답에 대해 JSON 파싱을 먼저 시도한다.

JSON 파싱 실패 시, 응답 본문이 비어 있지 않고 지나치게 짧지 않으면 plain text answer로 사용한다.

이 경우:
- parse_error=true 유지 가능
- answer_status는 partial 또는 answered_with_plain_text 등으로 구분 가능
- confidence는 서버 Evidence 기준 유지
- citations는 서버 Evidence 기준 유지

두 방식 중 현재 코드 구조에 더 안전한 방식을 선택하되, qwen3.5:9b 운영 안정성을 우선한다.

---

# 2. Evidence 없는 경우에는 기존처럼 Ollama 호출 생략

Evidence가 없는 경우에는 Ollama를 호출하지 않는 정책을 유지해라.

없는 함수 query:

`abcxyz_unknown_function 함수 변경 이유`

결과:
- no_evidence
- 신뢰도 낮음
- 근거 없음 안내

이 동작은 정상이다. 변경하지 마.

---

# 3. Ollama timeout 보완

운영 로그에 다음 오류가 있었다.

`Ollama error: Ollama 응답이 시간 내에 도착하지 않았습니다.`

현재 timeout 설정과 Evidence context 크기를 확인해.

보완 방향:

- OLLAMA_TIMEOUT_SECONDS 기본값을 현실적으로 조정 검토
- 내부망 qwen3.5:9b 기준 60초 정도 검토
- 너무 긴 prompt를 줄이기 위해 Evidence limit 조정 검토

단 무작정 Prompt를 길게 만들지 마.

권장:
- Evidence Link Top 2 또는 3 유지
- Field truncation 유지
- 전체 diff / 전체 raw_text 전달 금지 유지

완료 보고에 timeout 기본값과 근거를 기록해라.

---

# 4. 화면 문구 개선

현재 Ollama 실패 시 화면에:

`AI 분석 사용 불가`

가 표시된다.

이 문구는 사용자가 “전체 AI 분석 기능이 고장났다”고 오해할 수 있다.

상황별 문구를 구분해라.

## Ollama timeout / 연결 실패

`Ollama 응답 실패 - 근거 기반 요약을 표시합니다.`

## JSON parse 실패 후 plain text 사용

`AI 응답 형식은 표준과 달랐지만, 응답 본문을 표시합니다.`

또는 Markdown answer mode로 전환한 경우 이 문구 자체가 필요 없을 수 있다.

## JSON parse 실패 후 fallback 사용

`AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다.`

## no evidence

`관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다.`

---

# 5. 기존 안정성 유지

다음은 유지해라.

- Evidence 없는 경우 Ollama 호출 생략
- Evidence Link는 STEP 7 결과 재사용
- Link Score Weight 변경 금지
- Query Relevance 변경 금지
- Parser 변경 금지
- Cache 변경 금지
- AI가 만든 evidence/confidence를 신뢰하지 않음
- 서버 Evidence 기준 citations 유지
- 전체 Diff 전달 금지
- 전체 PPT raw_text 전달 금지

---

# 6. 테스트

Backend 테스트 추가/수정:

1. Ollama Markdown/plain text 정상 응답
   - answer에 해당 text 사용
   - confidence는 서버 Evidence 기준
   - citations는 서버 Evidence 기준

2. Ollama JSON 응답
   - 기존 호환 가능하면 유지

3. Ollama bad JSON but meaningful text
   - plain text answer로 사용하거나 선택 정책에 맞게 처리

4. Ollama empty response
   - fallback answer 사용

5. Ollama timeout
   - fallback answer 사용
   - API 200

6. no evidence
   - Ollama 호출 안 함

7. 전체 diff/raw_text 미전달 유지

Frontend:

1. Markdown/plain text answer 표시
2. Timeout 시 fallback 표시
3. no evidence 메시지 표시
4. 기존 Evidence Link UI 회귀 없음

Backend:
python -m pytest tests/ -q

Frontend:
npm run build

---

# 7. 완료 보고

다음을 보고해.

1. 기존 JSON parse 실패 원인 분석
2. 최종 선택한 Ollama 응답 방식
3. JSON-only 유지 여부
4. Markdown/plain text answer 허용 여부
5. answer_status 변경 여부
6. parse_error 처리 정책
7. confidence 서버 계산 유지 여부
8. citations 서버 Evidence 기준 유지 여부
9. timeout 기본값
10. Evidence limit 유지/변경 여부
11. Prompt 변경 내용
12. 화면 문구 변경 내용
13. 추가/수정 Backend Test
14. Backend pytest 결과
15. Frontend build 결과
16. STEP 9 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

qwen3.5:9b 운영 안정성을 위해 **Markdown/plain-text 우선**으로 전환했습니다. Evidence 검색·fallback·서버 confidence/citations 정책은 유지합니다.

### 완료 보고

1. **JSON parse 실패 원인**
   Prompt가 JSON-only를 강제하고 `format=json`까지 썼는데, qwen3.5:9b가 스키마를 자주 깨뜨려 서버가 응답을 버리고 fallback만 씀.

2. **최종 선택**
   **방식 A 중심 + B 호환**: Markdown/평문 답변 우선, JSON이면 summary/reason 추출, 깨진 JSON blob만 fallback.

3. **JSON-only**
   **유지하지 않음.** `format=json` 제거.

4. **Markdown/plain text**
   **허용.** 의미 있는 본문은 `answer`로 사용.

5. **answer_status**
   추가/정리: `ok`, `answered_with_plain_text`, `ollama_parse_error`, `ollama_empty_response`, `ollama_timeout`, `ollama_unavailable`, `ollama_disabled`, `no_evidence`, `partial`

6. **parse_error**
   - 빈/깨진 JSON → `true` + Evidence fallback
   - 평문 성공 → `false`
   - JSON 모양인데 평문으로 살린 경우 → `answered_with_plain_text` (+ 안내)

7. **confidence**
   **서버 Evidence rule 유지** (Ollama 값 무시)

8. **citations**
   **서버 Evidence 기준 유지** (AI evidence 미신뢰)

9. **timeout 기본값**
   **30초 → 60초** (내부망 qwen3.5:9b 부하 시 30초 타임아웃이 잦았음). env로 조정 가능.

10. **Evidence limit**
    **Top 3 유지** (`OLLAMA_MAX_EVIDENCE=3`). 필드 truncate(400자), diff excerpt truncate(1200자), raw_text 미전달.

11. **Prompt**
    한국어 Markdown/평문만 요청. JSON·code fence 금지. 사용자 suffix로 재강조.

12. **화면 문구**
    - timeout/연결: `Ollama 응답 실패 — 근거 기반 요약을 표시합니다.`
    - plain salvage: `AI 응답 형식은 표준과 달랐지만, 응답 본문을 표시합니다.`
    - fallback: `AI 응답 형식을 해석하지 못해 근거 기반 요약을 표시합니다.`
    - no_evidence: 기존 확인 불가 문구
    - 답변 본문 기본 표시 (`AI 분석 사용 불가` 일괄 문구 제거)

13. **테스트**
    Markdown 본문 사용, 깨진 JSON fallback, empty, timeout(`ollama_timeout`), plain salvage, JSON 호환, no_evidence skip 등.

14. **pytest** — **353 passed**

15. **Frontend build** — **성공**

16. **STEP 9** — **미진행**

산출물 deploy 현행화 완료. `.env`에 `OLLAMA_TIMEOUT_SECONDS=30`이 있으면 60으로 올리거나 항목을 제거한 뒤 서버를 재시작하세요.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- qwen3.5:9b 안정성을 위해 Markdown/plain-text 우선 응답 처리로 전환하고, timeout·화면 문구를 보완합니다.
- Markdown answer mode로 전환하고, JSON은 호환용으로만 유지합니다. timeout은 60초로 올립니다.
- 테스트을 Markdown/plain-text 정책에 맞게 수정합니다.

- 사용 도구: Read×4, Grep×2, TodoWrite×2, Write, StrReplace×7, Shell×4, AwaitShell (총 21회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [004]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #69  |  Thursday, Jul 23, 2026, 9:53 AM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 9는 아직 진행하지 마.

STEP 8 운영 테스트 결과, /api/trace/analyze에서 Ollama가 10건 이상 한 번도 정상 응답하지 못했다.

현재 증상:
- Evidence 검색과 fallback은 정상
- /api/trace/analyze는 200으로 반환
- 서버 로그에는 `Ollama request model=qwen3.5:9b timeout_s=60.0 git_evidence=3 document_evidence=3`
- 이후 `Ollama 응답이 시간 내에 도착하지 않았습니다.`
- 또는 JSON parse failed 후 fallback
- 실제 Ollama 자연어 답변 성공 사례는 아직 없음

이번 작업은 STEP 8 Ollama 응답 실패 원인을 분리 진단하기 위한 최소 보완이다.

Search, Evidence Link, Ranking, Parser, Cache, DB는 변경하지 마.

# 1. Ollama 진단 로그 추가

Ollama 요청 전후에 다음을 INFO 로그로 남겨라.

- model
- base_url
- timeout_seconds
- evidence_count
- git_evidence_count
- document_evidence_count
- prompt_chars
- prompt_estimated_tokens 가능하면
- max_diff_chars
- max_field_chars
- request_start_time
- elapsed_ms
- result_type
  - success
  - timeout
  - connection_error
  - parse_error
  - empty_response
  - fallback

주의:
Full Prompt, 전체 Diff, 전체 PPT raw_text는 로그에 남기지 마.

# 2. Ollama Health / Tiny Prompt 테스트 API 추가 검토

운영 진단용으로 아주 작은 API를 추가해도 된다.

예:
GET /api/trace/ollama-test

또는 기존 health 확장.

동작:
- Ollama에 아주 짧은 prompt 전송
- prompt: "안녕. 한 문장으로 답해줘."
- stream=false
- timeout은 별도 짧은 값 또는 기존 값 사용
- 응답 시간 elapsed_ms 반환
- 성공/실패 반환

이 API는 Git/PPT/Evidence와 무관하게 Ollama 단독 속도를 확인하기 위한 것이다.

응답 예:
{
  "ok": true,
  "model": "qwen3.5:9b",
  "elapsed_ms": 8421,
  "response_preview": "안녕하세요..."
}

실패 시:
{
  "ok": false,
  "error_type": "timeout",
  "elapsed_ms": 60000
}

# 3. Evidence 크기 축소 설정 확인

현재 Evidence 3개씩 전달하고 있다.

설정값을 확인하고 .env에서 조정 가능하게 해라.

- OLLAMA_MAX_EVIDENCE 또는 TRACE_ANSWER_EVIDENCE_LIMIT
- TRACE_ANSWER_MAX_DIFF_CHARS
- TRACE_ANSWER_MAX_FIELD_CHARS
- TRACE_ANSWER_MAX_PROMPT_CHARS
- OLLAMA_TIMEOUT_SECONDS

이미 있으면 문서화하고 로그에 표시해라.

없으면 최소한 기존 설정 구조에 맞춰 추가 검토.

기본값은 기존 유지 가능하나 운영 진단을 위해 다음 값을 테스트할 수 있어야 한다.

- evidence limit 1
- max diff chars 300
- max field chars 300
- timeout 120

# 4. Timeout 기본값 검토

현재 60초에도 qwen3.5:9b가 응답하지 못한다.

기본값을 바로 바꾸기보다, 설정으로 조정 가능하게 하고 완료 보고에 현재 기본값과 운영 권장값을 분리해서 제안해라.

예:
기본값: 60초
운영 진단 권장: 120초

# 5. 테스트

Backend 테스트:
- tiny prompt 성공 mock
- tiny prompt timeout mock
- analyze 로그 메타 생성
- full prompt가 로그에 포함되지 않는지
- evidence limit 1 적용
- max diff chars 적용
- timeout 설정 override

Frontend 수정이 필요하면 npm run build.
Backend 수정 시 python -m pytest tests/ -q.

# 6. 금지

- STEP 9
- Continue 연동
- Evidence Link 재설계
- Link Score 변경
- Query Relevance 변경
- Parser 변경
- Cache 변경
- 전체 Diff 로그 출력
- Full Prompt 로그 출력
- 내부 문서 원문 로그 출력

# 7. 완료 보고

다음을 보고해.

1. Ollama timeout 원인 진단을 위해 추가한 로그 항목
2. prompt_chars 확인 방법
3. elapsed_ms 기록 위치
4. tiny prompt 테스트 API 추가 여부
5. Evidence limit 설정명
6. diff/field/prompt 길이 제한 설정명
7. timeout 설정명
8. 운영 테스트 권장 설정값
9. Full Prompt 미로그 확인
10. Backend pytest 결과
11. Frontend build 결과
12. STEP 9 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

Ollama 단독 진단용 로그·설정·`/api/trace/ollama-test`를 추가했습니다. Search/Evidence/Link/Ranking은 변경하지 않았습니다.

### 완료 보고

1. **추가 로그 항목**
   `request_start`/`request_end`: model, base_url, timeout_seconds, evidence_count, git/document_evidence_count, prompt_chars, prompt_estimated_tokens, max_diff/field/prompt_chars, request_start_time, elapsed_ms, result_type (`success|timeout|connection_error|parse_error|empty_response|fallback`)

2. **prompt_chars 확인**
   서버 로그 `Ollama request_start ... prompt_chars=N` 또는 `prompt_estimated_tokens≈N/4`

3. **elapsed_ms**
   `_call_ollama_raw` 전후 `perf_counter` → `request_end` 로그

4. **tiny prompt API**
   **추가함**: `GET /api/trace/ollama-test`
   Evidence/Git/PPT 무관. 짧은 “안녕. 한 문장으로 답해줘.”만 전송.

5. **Evidence limit**
   `OLLAMA_MAX_EVIDENCE` (alias: `TRACE_ANSWER_EVIDENCE_LIMIT`)

6. **길이 제한**
   `TRACE_ANSWER_MAX_DIFF_CHARS`, `TRACE_ANSWER_MAX_FIELD_CHARS`, `TRACE_ANSWER_MAX_PROMPT_CHARS`

7. **timeout**
   `OLLAMA_TIMEOUT_SECONDS` (+ optional `OLLAMA_TEST_TIMEOUT_SECONDS`)

8. **운영 진단 권장**
   | 항목 | 코드 기본 | 진단 권장 |
   |------|-----------|-----------|
   | timeout | **60** | **120** |
   | evidence | 3 | **1** |
   | max diff | 1200 | **300** |
   | max field | 400 | **300** |

   절차: 먼저 `/api/trace/ollama-test`로 단독 지연 확인 → 느리면 timeout 120 + evidence 1로 `/analyze` 재시험.

9. **Full Prompt 미로그**
   테스트로 확인 (query 전문/diff marker/raw_text 미포함)

10. **pytest** — **361 passed**

11. **Frontend build** — **해당 없음** (FE 변경 없음)

12. **STEP 9** — **미진행**

산출물 deploy 현행화 완료. 서버 재시작 후 `.env`에 진단값을 넣고 `GET /api/trace/ollama-test`부터 확인하면 됩니다.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Ollama 단독 진단용 로그·설정·tiny test API를 추가합니다. Evidence/Search 로직은 건드리지 않습니다.
- 산출물 동기화는 워크스페이스 규칙상 필요합니다. 승인 후 `package-deploy`를 재실행합니다.

- 사용 도구: Read×8, Grep×3, TodoWrite×3, StrReplace×10, Write×2, Shell×4, AwaitShell (총 31회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [005]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #70  |  Thursday, Jul 23, 2026, 2:45 PM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 9는 아직 진행하지 마.

이번 작업은 STEP 8 AI 분석 화면과 `/api/trace/analyze` 요청 정책 보완이다.

현재 운영 테스트 결과:

- qwen3.5:9b + evidence limit 2에서 보고용으로 사용할 만한 AI 답변 품질 확인
- 다만 Ollama 서버는 여러 사람이 공유하므로 응답이 오래 걸릴 수 있음
- 서버 근거 기반 요약은 항상 안정적으로 표시되어야 함
- AI 보조 설명은 기본 ON으로 사용하되, 사용자가 체크 해제하면 Ollama를 호출하지 않고 서버 근거 요약만 표시하고 싶음

운영 권장 env는 유지한다.

OLLAMA_ENABLED=true
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_MAX_EVIDENCE=2
TRACE_ANSWER_MAX_DIFF_CHARS=300
TRACE_ANSWER_MAX_FIELD_CHARS=300
TRACE_ANSWER_MAX_PROMPT_CHARS=6000

# 목표

AI 보조 설명 생성은 기본 ON.
사용자가 체크 해제하면 Ollama 호출 없이 서버 근거 기반 요약만 표시.

# 1. UI 체크박스 추가

AI 분석 실행 버튼 근처에 체크박스를 추가한다.

표시:

[✓] AI 보조 설명 생성

기본값은 true.

도움말 문구:

AI 보조 설명은 내부 Ollama 서버 상태에 따라 1분 이상 걸릴 수 있습니다. 체크 해제 시 빠른 서버 근거 요약만 표시합니다.

# 2. /api/trace/analyze request에 use_ollama 반영

Request에 use_ollama boolean을 추가하거나 기존 유사 필드가 있으면 재사용한다.

기본값 true.

예:

{
  "equipment_id": 1,
  "query": "file_close_init 함수 변경 이력을 보여줘",
  "file_path": "lib/libfare_mgt/src/file_save_mgt.c",
  "selected_code": "",
  "use_ollama": true
}

정책:

use_ollama=true:
- Ollama 보조 설명 생성 시도
- 서버 근거 요약은 항상 표시

use_ollama=false:
- Ollama 호출 생략
- 서버 근거 기반 요약만 반환
- confidence, citations, evidence는 정상 반환
- debug 또는 status에 Ollama 미사용 상태가 드러나야 함

# 3. 서버 근거 요약 우선 표시

화면 기본 표시 순서:

1. 신뢰도
2. 서버 근거 기반 요약
3. Git 근거
4. 변경내역서 근거
5. AI 보조 설명
6. 상세 Evidence

AI 보조 설명이 서버 근거 요약을 대체하면 안 된다.

# 4. 상태 문구

use_ollama=false:

AI 보조 설명을 사용하지 않고 서버 근거 기반 요약만 표시합니다.

Ollama timeout / 연결 실패:

Ollama 응답 실패 - 서버 근거 기반 요약을 표시합니다.

Ollama 성공:

AI 보조 설명이 생성되었습니다.

no evidence:

관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다.

# 5. 테스트

Backend:

1. use_ollama=true → Ollama 호출 시도
2. use_ollama=false → Ollama 호출 안 함
3. use_ollama=false여도 서버 근거 요약 반환
4. no_evidence → Ollama 호출 안 함
5. Ollama 실패 → 서버 근거 요약 유지

Frontend:

1. 체크박스 기본 ON
2. 체크 ON → use_ollama=true 요청
3. 체크 OFF → use_ollama=false 요청
4. 체크 OFF 상태에서 서버 근거 요약 표시
5. 기존 Evidence UI 회귀 없음

실행:

Backend 수정 시 python -m pytest tests/ -q
Frontend 수정 시 npm run build

# 금지

- STEP 9 진행
- Continue 연동
- Evidence Link 재설계
- Link Score 변경
- Query Relevance 변경
- Parser 변경
- Cache 변경
- DB Schema 변경
- Ollama 실패를 API 실패로 전파

# 완료 보고

1. AI 보조 설명 체크박스 추가 여부
2. 기본값 true 여부
3. use_ollama request 반영 여부
4. use_ollama=false 시 Ollama 호출 생략 확인
5. 서버 근거 요약 기본 표시 유지 여부
6. AI 보조 설명 표시 정책
7. 상태 문구
8. Backend test 결과
9. Frontend build 결과
10. STEP 9 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_

### ◇ 진행 과정 요약（도구·짧은 안내만）

- _(도구 호출 없음)_

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [006]  STEP 8 — Ollama 근거 기반 변경 사유 분석                                       ║
║  메인 turn #71  |  Thursday, Jul 23, 2026, 2:45 PM (UTC+9)                     ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 기준 명세로 사용해.

STEP 9는 아직 진행하지 마.

이번 작업은 STEP 8 AI 분석 화면과 `/api/trace/analyze` 요청 정책 보완이다.

현재 운영 테스트 결과:

- qwen3.5:9b + evidence limit 2에서 보고용으로 사용할 만한 AI 답변 품질 확인
- 다만 Ollama 서버는 여러 사람이 공유하므로 응답이 오래 걸릴 수 있음
- 서버 근거 기반 요약은 항상 안정적으로 표시되어야 함
- AI 보조 설명은 기본 ON으로 사용하되, 사용자가 체크 해제하면 Ollama를 호출하지 않고 서버 근거 요약만 표시하고 싶음

운영 권장 env는 유지한다.

OLLAMA_ENABLED=true
OLLAMA_MODEL=qwen3.5:9b
OLLAMA_TIMEOUT_SECONDS=120
OLLAMA_MAX_EVIDENCE=2
TRACE_ANSWER_MAX_DIFF_CHARS=300
TRACE_ANSWER_MAX_FIELD_CHARS=300
TRACE_ANSWER_MAX_PROMPT_CHARS=6000

# 목표

AI 보조 설명 생성은 기본 ON.
사용자가 체크 해제하면 Ollama 호출 없이 서버 근거 기반 요약만 표시.

# 1. UI 체크박스 추가

AI 분석 실행 버튼 근처에 체크박스를 추가한다.

표시:

[✓] AI 보조 설명 생성

기본값은 true.

도움말 문구:

AI 보조 설명은 내부 Ollama 서버 상태에 따라 1분 이상 걸릴 수 있습니다. 체크 해제 시 빠른 서버 근거 요약만 표시합니다.

# 2. /api/trace/analyze request에 use_ollama 반영

Request에 use_ollama boolean을 추가하거나 기존 유사 필드가 있으면 재사용한다.

기본값 true.

예:

{
  "equipment_id": 1,
  "query": "file_close_init 함수 변경 이력을 보여줘",
  "file_path": "lib/libfare_mgt/src/file_save_mgt.c",
  "selected_code": "",
  "use_ollama": true
}

정책:

use_ollama=true:
- Ollama 보조 설명 생성 시도
- 서버 근거 요약은 항상 표시

use_ollama=false:
- Ollama 호출 생략
- 서버 근거 기반 요약만 반환
- confidence, citations, evidence는 정상 반환
- debug 또는 status에 Ollama 미사용 상태가 드러나야 함

# 3. 서버 근거 요약 우선 표시

화면 기본 표시 순서:

1. 신뢰도
2. 서버 근거 기반 요약
3. Git 근거
4. 변경내역서 근거
5. AI 보조 설명
6. 상세 Evidence

AI 보조 설명이 서버 근거 요약을 대체하면 안 된다.

# 4. 상태 문구

use_ollama=false:

AI 보조 설명을 사용하지 않고 서버 근거 기반 요약만 표시합니다.

Ollama timeout / 연결 실패:

Ollama 응답 실패 - 서버 근거 기반 요약을 표시합니다.

Ollama 성공:

AI 보조 설명이 생성되었습니다.

no evidence:

관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다.

# 5. 테스트

Backend:

1. use_ollama=true → Ollama 호출 시도
2. use_ollama=false → Ollama 호출 안 함
3. use_ollama=false여도 서버 근거 요약 반환
4. no_evidence → Ollama 호출 안 함
5. Ollama 실패 → 서버 근거 요약 유지

Frontend:

1. 체크박스 기본 ON
2. 체크 ON → use_ollama=true 요청
3. 체크 OFF → use_ollama=false 요청
4. 체크 OFF 상태에서 서버 근거 요약 표시
5. 기존 Evidence UI 회귀 없음

실행:

Backend 수정 시 python -m pytest tests/ -q
Frontend 수정 시 npm run build

# 금지

- STEP 9 진행
- Continue 연동
- Evidence Link 재설계
- Link Score 변경
- Query Relevance 변경
- Parser 변경
- Cache 변경
- DB Schema 변경
- Ollama 실패를 API 실패로 전파

# 완료 보고

1. AI 보조 설명 체크박스 추가 여부
2. 기본값 true 여부
3. use_ollama request 반영 여부
4. use_ollama=false 시 Ollama 호출 생략 확인
5. 서버 근거 요약 기본 표시 유지 여부
6. AI 보조 설명 표시 정책
7. 상태 문구
8. Backend test 결과
9. Frontend build 결과
10. STEP 9 미진행 확인
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

#### 응답 1/5

I need to add a `use_ollama` flag to the AnalysisRequest schema that lets users opt out of AI assistance, then pass it through to the evidence analysis while still computing confidence scores and citations. The key is distinguishing between a system-level Ollama disabled status versus a user choosing to disable it, since they need different messaging according to the spec.

Let me check the current ollama_service.py to see how to integrate this properly.

#### 응답 2/5

I'm planning to add a `use_ollama` parameter to the `analyze_evidence()` function that lets users disable the Ollama call entirely, returning a fallback summary instead. When disabled, I need to decide on the status code—something like `STATUS_USER_DISABLED` with `ai_available=False`—though I'm reconsidering the current semantics where `ai_available=True` even when there's no evidence, which feels inconsistent.

For the implementation, I'll update the request schema to include `use_ollama: bool = True`, pass it through the API layer, and add a Korean message for when AI assistance is skipped. On the frontend, I need to add a checkbox to control this setting and reorder the analysis panel to always show the server-based summary first, then conditionally show the AI explanation only when Ollama is enabled and available. The spec also defines a specific display order starting with confidence, server summary, Git evidence, and document changes.

To support this properly, I'm restructuring the response to separate `server_summary` and `server_reason` (always populated from Evidence) from a new `ai_answer` field (only present when Ollama generates output), so the UI can display them in the correct order and only show the AI section when it's actually available. Refactoring the result structure to cleanly separate server evidence from AI-generated content: `summary` and `reason` will always contain the server's evidence data, while `ai_answer` captures Ollama's output when available, with None in cases where Ollama is disabled, unavailable, or fails to parse. I need to keep `summary` and `reason` fields but redefine them to always reflect server-based evidence rather than AI content, which also fixes the issue where AI explanations were replacing the evidence summary on the frontend. I'm restructuring the response fields so that `ai_answer` holds the Ollama output separately, and adding `use_ollama` for transparency about whether the model was actually invoked. I'll keep `answer` as the fully composed text for backward compatibility with the full detail view, but the primary display will pull directly from the evidence summary, reason, and AI answer fields. Since this involves substantial changes to the test suite across multiple files, I need to methodically update all the assertions that currently expect AI content in the summary field.

Actually, reconsidering the requirement — it's really about display priority at the frontend level rather than backend restructuring. I can satisfy this by exposing both the server-only evidence fields and the AI-generated fields in the response. The fallback fields are already being computed server-side but just not exposed, so I'll add them as new response fields like `server_summary` and `server_answer` to represent the evidence-only content that's always available, while keeping the existing `summary` and `answer` fields for AI-generated content. This minimizes backend risk while giving the frontend both options. So I'd add two new fields to capture server-only evidence: `evidence_summary` and `evidence_answer` (always populated from the fallback logic), plus `ai_answer` which only contains text when Ollama actually succeeded—otherwise it's None for cases like timeouts, parse errors, or when AI is disabled.

I'd also add `ai_used` to track whether Ollama was invoked. The existing `summary`, `reason`, and `answer` fields stay as-is for backward compatibility, representing whichever source had content (AI if available, otherwise fallback).

Now implementing the `use_ollama` parameter: when it's False and evidence exists, I'd skip the Ollama call entirely and go straight to populating the result with server evidence, while the "no evidence" branch remains unchanged—always skipped regardless of the flag.

Defining the response structure for the disabled case... Configuring result fields... In the no-evidence branch, I'm setting evidence_summary to the fallback summary since it already contains the right value, then assigning the fallback answer and marking ai_answer as null with ai_used as false. For the use_ollama=False case, I need to check this condition after the no-evidence check but before the OLLAMA_ENABLED check, then skip the regular Ollama call when it's false.

When Ollama is disabled at the system level, the existing message about the feature being inactive stays the same with the disabled status flag. For actual Ollama attempts, I'm setting ai_used to true before the call, then handling the error case where ai_used remains true but ai_answer stays null, and the success case where I compute the ai_answer normally.

Now I need to update all the return statements throughout the function to include these new fields, then refactor the entire analyze_evidence function along with the exception handling, no-evidence returns, and disabled state returns, plus update the dataclass definition.

For the schemas, I'm adding use_ollama as a boolean flag to AnalysisRequest, and extending AnalysisResponse with evidence_summary, evidence_answer, ai_answer, ai_used, and echoing back the use_ollama flag. I'm also updating the API layer to pass the request's use_ollama setting through to analyze_evidence and populate all the new response fields, plus adding the appropriate constants to the Ollama service for the user-disabled state. On the frontend side, I need to add use_ollama to the AnalysisRequest interface...

Adding UI controls and response handling...

#### 응답 3/5

All 361 tests are passing, which confirms the new fields with their defaults don't break anything. The test run took a bit longer than expected, likely due to some unrelated network timeouts, but my changes didn't introduce any failures. Now I'm ready to move on to the next part.

I need to add tests for the Ollama integration behavior. Looking at the requirements, I should test scenarios where use_ollama is true or false, verify that server-based summaries are returned regardless, handle the no_evidence case, and ensure graceful fallback if Ollama fails. Let me check the existing test files to match the current testing style and patterns.

#### 응답 4/5

Let me check exact wording expectations more carefully and align backend messages with the exact phrasing requested.

Now I'm finalizing the completion report and verifying I've covered all the requirements: the UI checkbox with default enabled state and help text, the use_ollama parameter added to the request schema and wired through the frontend call, and reordering the analysis panel to display server-based summaries first.

I've also added the status messages matching the spec, including the disabled message and success confirmation when AI explanations are generated, while keeping the existing timeout and parse error messages. Tests are passing with 372 backend tests, and the frontend builds successfully. I'm double-checking that the Korean wording matches exactly what was requested, with minor formatting differences like em dashes versus hyphens that preserve the intended meaning. I need to update the backend message constants in ollama_service.py to include "서버" in both the timeout and unavailable error messages, so they match the user's exact wording of "Ollama 응답 실패 — 서버 근거 기반 요약을 표시합니다." This is a straightforward fix that ensures consistency between what the backend sends and what the user expects to see.

#### 응답 5/5

산출물 동기화 완료. 완료 보고입니다.

## 완료 보고

**1. AI 보조 설명 체크박스 추가 여부**
추가함. `EvidenceLinkViewer.tsx`의 "AI 분석 실행 (STEP 8)" 버튼 옆에 `[✓] AI 보조 설명 생성` 체크박스와 도움말 문구(`.ev-hint`)를 배치.

**2. 기본값 true 여부**
`useState(true)` — 기본 ON.

**3. use_ollama request 반영 여부**
`AnalysisRequest.use_ollama: bool = True` (backend `schemas/analysis.py`), FE `fetchAnalysis` 호출 시 체크박스 상태를 그대로 전송.

**4. use_ollama=false 시 Ollama 호출 생략 확인**
`analyze_evidence(evidence_result, use_ollama=...)`에서 no_evidence 체크 다음, `OLLAMA_ENABLED` 체크보다 먼저 `use_ollama` 분기 처리. `_call_ollama_raw`가 절대 호출되지 않음을 단위 테스트(`test_use_ollama_false_skips_ollama_call` 등)로 `AssertionError` 강제 검증.

**5. 서버 근거 요약 기본 표시 유지 여부**
`OllamaAnalysisResult`/`AnalysisResponse`에 `evidence_summary`, `evidence_answer` 필드를 신설 — Ollama 성공/실패/스킵 여부와 무관하게 항상 서버 Evidence 기반으로 채워짐. `confidence`, `citations(evidence)`는 기존과 동일하게 Evidence 규칙 기반 유지.

**6. AI 보조 설명 표시 정책**
Panel 표시 순서를 스펙대로 재배치: 신뢰도(head) → 서버 근거 기반 요약(`evidence_summary`/`evidence_answer`) → Git 근거/변경내역서 근거(`EvidenceRefList`) → AI 보조 설명(`ai_answer`, `ai_used`가 true이고 실제 생성된 텍스트가 있을 때만 별도 블록으로 표시, 서버 요약을 대체하지 않음) → 상세 Evidence(기존 하단 섹션 유지).

**7. 상태 문구**
- `use_ollama=false`: "AI 보조 설명을 사용하지 않고 서버 근거 기반 요약만 표시합니다." (신규 status `ollama_skipped_by_user`)
- timeout/연결 실패: "Ollama 응답 실패 — 서버 근거 기반 요약을 표시합니다." (기존 문구에 "서버" 추가)
- 성공: "AI 보조 설명이 생성되었습니다."
- no evidence: "관련 Git 또는 변경내역서 근거를 찾지 못해 변경 사유를 확인할 수 없습니다." (기존 유지)

**8. Backend test 결과**
`test_ollama_service.py`에 5개, `test_analysis_api.py`에 6개 신규 테스트 추가 (use_ollama true/false, no_evidence 우선순위, Ollama 실패 시 서버 요약 유지, 기본값 true 등). 전체 `python -m pytest tests/ -q` → **372 passed**.

**9. Frontend build 결과**
`npm run build` → 성공 (tsc + vite build, 오류 없음).

**10. STEP 9 미진행 확인**
Continue 연동, STEP 9 관련 코드는 전혀 건드리지 않음. Link Score/Query Relevance/Parser/Cache/DB Schema 변경 없음. `산출물/` 동기화(`package-deploy.py`)까지 재실행 완료.

### ◇ 진행 과정 요약（도구·짧은 안내만）

- Now implementing the backend changes.
- Now update `analyze_evidence` to accept `use_ollama` and populate the new fields consistently across all branches.
- Now update the timeout/error branch and the success path to set `evidence_summary`/`evidence_answer`/`ai_answer`/`ai_used`:
- Now let's wire `use_ollama` through the schema and API layer, plus the tiny-test/diagnostic status message list.
- Now update the frontend: API client + checkbox + reordered panel.
- Now let's view the full `AiAnalysisPanel` + status helpers + handler + button section to rewrite them cleanly.
- I'm reorganizing the panel structure to follow a specific order: confidence badge at the top, then the server evidence summary with supporting details, followed by Git evidence, changelog evidence, AI-assisted explanations if available, and finally the detailed evidence links section below.
- Now let's find where `fetchAnalysis` is called and where the "AI 분석 실행" button is, to add the checkbox and pass `use_ollama`.

- 사용 도구: Read×19, StrReplace×18, Grep×6, Shell×11, AwaitShell×3, ReadLints (총 58회)

---
