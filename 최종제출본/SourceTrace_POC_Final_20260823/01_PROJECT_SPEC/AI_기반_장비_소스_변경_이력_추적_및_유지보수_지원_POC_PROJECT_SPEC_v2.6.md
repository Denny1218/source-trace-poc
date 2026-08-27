# AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC
## PROJECT_SPEC v2.6 (현재 기준 명세)

- 문서 성격: 현재 구현·운영 기준의 통합 명세
- 작성 기준일: 2026-08-07
- 기반 문서: `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.5.1.md`
- 이전 기준: PROJECT_SPEC v2.5.1
- 우선순위: 본 문서(v2.6)가 현재 작업·검증·산출물의 최우선 기준이다. 이전 v2.5.1 및 기존 보완명세와 충돌하면 본 문서를 따른다.
- STEP 10: 별도 승인 없이 진행하지 않는다.
- v2.2 유지 정책: Git lifecycle과 관련 공식 문서는 별도 축으로 관리한다. 문서 역할을 추정 분류하지 않고 `Commit 직접 근거/단계 연결 근거/관련 참고`의 연결 강도로 표시한다.
- v2.3 유지 정책: Continue 연동을 프로젝트 공식 범위에서 제거하고 Source Trace VS Code Extension 직접 조회를 공식 사용자 경로로 유지한다.
- v2.4 유지 정책: 함수/Symbol 전체 이력 조회와 선택 코드(라인·블록) 변경 근거 조회를 분리하고, 선택 코드 조회는 Git blame과 line history를 우선한다.
- v2.5 유지 정책: Repository 식별·문서 관계 분리·함수 Diff 판정 보완 원칙은 내부 근거 검증에 유지한다.
- v2.6 핵심 정책: 사용자 결과는 `언제 변경되었는지 / 무엇이 변경되었는지 / 관련 문서가 무엇인지`를 빠르게 확인하는 데 집중한다. 주요 개발·보조 변경·유지보수, 공식/직접/단계/참고 문서 등급, 분석 신뢰도는 사용자 결과에서 제거한다. 선택 코드 조회는 Extension에서 별도 Repo 매칭으로 차단하지 않고 함수 조회와 동일한 Backend Repository resolver를 사용한다.
- 2026-08-23 종료 정책 (본 문서 in-place, 새 버전 번호 없음): Visual Studio 2017은 공식 지원 대상(VSIX 0.1.3). Visual Studio 2010은 legacy compatibility 지원 대상(VSIX 0.1.3). Visual Studio 2022는 현재 POC 공식 지원·배포 대상에서 제외한다. Web Manual Client는 공식 fallback client. Continue는 공식 범위 제외를 유지한다. Backend API는 IDE 공통이며 IDE별 API 분기가 없다. 공식 repository identity는 `equipment_id` + `repo_relative_path`이다.

---

## 0. 문서 관리

### 0.1 문서 관계

```text
PROJECT_SPEC v2
  → 초기 단계별 개발 작업지시서 (STEP 0~10 포함)

PROJECT_SPEC v2.1
  → v2 및 현행화 보완명세를 병합한 이전 기준 명세

PROJECT_SPEC v2.2
  → Git lifecycle과 관련 공식 문서의 독립 관리 정책을 반영한 이전 기준 명세

PROJECT_SPEC v2.3
  → Continue 연동을 공식 범위에서 제거하고 Source Trace Extension 단독 운영 정책을 반영한 이전 기준 명세

PROJECT_SPEC v2.4
  → 함수 전체 이력 조회와 선택 코드 변경 근거 조회를 분리하고 line-level Git 근거·분류 정확도·Output 복구 정책을 반영한 이전 기준 명세

PROJECT_SPEC v2.5
  → Repository 식별, 문서 관계 분리, lifecycle 승격 제한을 반영한 기준 명세

PROJECT_SPEC v2.5.1
  → 함수 Diff 판정 세분화, 선택 코드 Repo 매칭 보완, 관련 목록 표시 우선순위를 추가한 이전 기준 명세

PROJECT_SPEC v2.6 (본 문서)
  → 사용자 결과를 시간순 변경 이력과 관련 문서 중심으로 단순화하고, 선택 코드 조회의 Repository 해석을 함수 조회와 동일한 Backend resolver로 통합한 현재 기준 명세
```

### 0.2 버전 변경 이력

| 버전 | 기준일 | 핵심 변경 |
|---|---|---|
| v2.1 | 2026-07-31 | v2와 현행화 보완명세를 병합한 통합 기준 명세 |
| v2.2 | 2026-08-05 | Git lifecycle과 관련 공식 문서를 독립 관리하고, 문서의 공식/후속 역할 추정 및 270일 휴리스틱을 제거 |
| v2.3 | 2026-08-05 | Continue 연동 제거, Source Trace Extension 단독 공식 조회 정책, Continue 전용 API·설정·Output·문서·테스트 제거 |
| v2.4 | 2026-08-06 | 함수 전체 조회와 선택 코드 조회 분리, Git blame/line history 우선, 변경 성격 분류 보수화, Evidence Link 직접성 강화, 일반 Source Trace Output 복구 |
| v2.5 | 2026-08-07 | 선택 코드 repo 식별 계약 강화, 함수 수준 문서와 Commit 수준 연결 분리, Commit 상세의 참고 문서 남발 제거, 직접 Diff 없는 Commit의 주요 lifecycle 승격 차단 |
| v2.5.1 | 2026-08-07 | v2.5 실사용 보완: 함수 Diff 판정 세분화, 선택 코드 Repo 매칭 일관성/UX 개선, 관련 함수·소스 목록에서 조회 대상 우선 표시 |
| v2.6 | 2026-08-07 | 사용자 결과 단순화: 개발/유지보수·문서 등급·신뢰도 표시 제거, 시간순 변경 이력/관련 문서 중심 재구성, 함수·선택 코드 조회의 Backend Repository resolver 공통화. 이후 Git 이력 표기, 선택 Diff hunk 상세, short hash 8자리 통일, Extension command 기여 일관성 보완. ATEC Mobility 원본 로고·favicon·Extension 아이콘을 폐쇄망 패키지 자산으로 적용 |

### 0.3 적용 원칙

1. UI·결과 Markdown·변경내역서 연결·Extension 설정은 **§1.3, §3, §9~§12** 및 STEP 9(현행)를 우선한다.
2. STEP 0~8의 데이터 모델·API·Cache·Evidence Link·Ollama 원칙은 유지하되, 본 문서의 현행 정책과 충돌하면 현행 정책을 따른다.
3. 기능 수정 후 산출물(`산출물/서버PC`, `산출물/운영PC`, VSIX, 사용자 가이드)과 본 명세를 함께 갱신한다.

---

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
- VS Code Extension에서 함수/Symbol 전체 변경 lifecycle 조회
- VS Code Extension에서 선택한 라인·코드 블록의 실제 변경 Commit과 변경 근거 조회
- AI 답변에 Git Commit 및 변경내역서 근거 표시

본 POC의 핵심 사용자 경험은 다음과 같다.

```text
VS Code Source Trace Extension

개발자:
함수/코드 선택 → "장비 변경 이력 조회"
"CalcFare 함수가 왜 변경됐어?"

        ↓

현재 질문 / 파일 / 선택 코드 / Symbol

        ↓

Change Trace Backend

        ↓

Git 함수 lifecycle 구성

        ↓

Commit / Diff / 날짜 / 파일 / Keyword 추출

        ↓

관련 PPT 후보 탐색

        ↓

필요한 PPT만 On-demand 분석

        ↓

Git lifecycle과 관련 PPT 근거의 독립 연계

        ↓

(선택) Ollama 근거 기반 분석

        ↓

Extension Markdown 결과 / Output
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
시스템 상태 확인
장비 및 Git 저장소 관리
Git 동기화 및 변경 이력 검증
변경내역서 검색
PPT Cache 및 분석 상태 확인
Source Trace 조회 (Web Manual Client)
운영 및 장애 확인
```

실제 주요 사용자 인터페이스는 **Source Trace VS Code Extension**(Reference Client)이다.
추가 IDE Client로 **Eclipse Source Trace Plug-in**을 제공한다(Backend API 무수정 Adapter).

```text
주 사용 인터페이스 (Reference Client)
Source Trace VS Code Extension

추가 IDE Client
Eclipse Source Trace Plug-in (CDT C/C++ Editor)
Microsoft Visual Studio Source Trace Extension
  - Visual Studio 2017 / 15.x : 공식 지원, VSIX 0.1.3
  - Visual Studio 2010 / 10.x : legacy compatibility, VSIX 0.1.3 (VSIX schema 1.0)
  - Visual Studio 2022 / 17.x : 현재 POC 공식 지원·배포 대상에서 제외

보조 조회 Client
Web Manual Client
  - 장비 / 파일 / 함수 / 선택 코드를 사용자가 직접 입력
  - `POST /api/trace/report`, `POST /api/trace/selection` 그대로 사용
  - Backend `content`를 그대로 표시
  - 별도 Git/PPT 판정 로직 없음

보조 인터페이스
Web 관리 / 검증 UI

제외 범위 (현행)
VSCode Continue 연동
```

상세 정책은 §9를 따른다.

### 1.4 Continue 연동 제외 결정

2026-08-05 실사용 검증 결과, 오프라인 소형 모델과 Continue Context/Agent 방식은 다음 이유로 공식 근거 조회에 적합하지 않은 것으로 판단했다.

```text
모델별 답변 편차
확정 날짜·Commit·Slide·CSR·연결 유형 훼손
Markdown 표·details 구조 붕괴
원문에 없는 역할·업무 의미 생성
함수명을 Skill 또는 Tool 이름으로 오인
Source Trace Context 완료와 AI 최종 답변의 추적 범위 불일치
```

따라서 v2.3부터 Continue 연동을 프로젝트 범위에서 제거한다.

제거 원칙:

1. Source Trace Extension 직접 결과만 공식 변경 이력으로 인정한다.
2. Continue Context Provider·Tool·Skill·MCP를 제공하지 않는다.
3. Continue 설정 스니펫 생성·복사·파일 열기 명령을 제거한다.
4. Continue 전용 상태 API·polling·request_id·진행 Output을 제거한다.
5. Continue 전용 간략 Context 생성기와 보호 프롬프트를 제거한다.
6. Continue 문서·설정·체크리스트·테스트를 제거하거나 폐기 이력으로만 보존한다.
7. 기존 Continue 사용자 설정 파일은 자동 수정·삭제하지 않는다.
8. Backend Ollama의 선택적 근거 기반 분석 정책은 Continue와 별개이므로 STEP 8 정책에 따라 유지할 수 있다.
9. 향후 온라인 또는 충분한 성능의 내부 AI 연동은 별도 명세·승인·검증을 거쳐 신규 기능으로 재검토한다.
10. STEP 10은 계속 미완료 상태로 유지한다.


### 1.5 함수 전체 조회와 선택 코드 조회 분리

v2.4부터 Extension 조회 기능을 다음 두 모드로 명확히 분리한다.

```text
함수/Symbol 변경 이력 조회
→ 대상 함수 전체 lifecycle과 관련 공식 문서 조회

선택 코드 변경 근거 조회
→ 선택한 라인 또는 코드 블록의 실제 Git 변경 근거 조회
```

선택 코드 조회에 함수 전체 분석용 키워드 후보 검색을 그대로 사용하지 않는다.

#### 함수/Symbol 조회

입력:

```text
파일 경로
함수 또는 Symbol
선택적 사용자 질문
```

주요 처리:

```text
함수 범위 확인
함수 Git lifecycle 구성
Commit Diff 분류
관련 공식 문서 연결
전체 Markdown 보고서 생성
```

#### 선택 코드 조회

입력:

```text
파일 경로
선택 시작 행·종료 행
선택 코드
포함 함수/Symbol
현재 Git revision
```

주요 처리 우선순위:

```text
1. git blame -L <start>,<end>
2. blame Commit의 실제 Diff 확인
3. git log -L 또는 동등한 line history 추적
4. 선택 코드가 추가·수정·이동·삭제·주변 변경 중 무엇인지 판정
5. Commit 직접 연결 문서만 우선 표시
6. 직접 문서가 없으면 없다고 명시
```

선택 코드의 식별자·파일명·주변 키워드만으로 관련 Commit이나 PPT를 공식 근거로 승격하지 않는다.

라인 이동·대규모 리팩터링·매크로 전개 등으로 `git log -L` 추적이 제한되면 해당 제한을 결과에 명시하고, 함수 전체 이력을 자동으로 선택 코드의 직접 근거처럼 제시하지 않는다.



### 1.6 v2.5 보완 정책 — Repository 식별, 문서 관계 분리, lifecycle 승격 제한

#### 선택 코드 조회의 파일 식별

Remote-SSH, 다중 Git Repo, 서버측 별도 clone 환경을 고려하여 선택 코드 조회는 절대경로 문자열 일치에 의존하지 않는다.

기본 계약:

```text
equipment_id
repo_id
repo_relative_path
start_line
end_line
selected_code
enclosing_symbol
revision
```

Extension은 현재 파일이 속한 Git root를 식별하고 장비에 등록된 Repo와 매칭한 뒤 `repo_id + repo_relative_path`를 Backend에 전달한다.

Backend는 등록된 `repo_id`의 실제 서버측 Git root와 `repo_relative_path`를 결합하고 `resolve()`/정규화 후 Repository 내부 파일인지 검증한다.

절대경로·Workspace 경로·Remote SSH 경로는 진단 보조 정보일 수 있으나 공식 파일 식별 키로 사용하지 않는다.

#### 문서 관계 2단계 분리

관련 공식 문서는 다음 두 수준으로 분리한다.

```text
A. 함수 수준 관련 문서
B. Commit 수준 연결 문서
```

A. 함수 수준 관련 문서는 대상 함수 또는 대상 파일과 관련된 공식 변경내역서를 사용자에게 보여주기 위한 정보다. 함수 목록 exact match, 관련 소스 path match, 문서 기능 주제 등으로 판단할 수 있다.

B. Commit 수준 연결 문서는 특정 Git Commit과 공식 문서 사이의 연결이다. Commit 상세에는 다음만 표시한다.

```text
Commit 직접 근거
단계 연결 근거
```

단순 `관련 참고`는 Commit 상세에 붙이지 않는다. 관련 참고 문서는 함수 수준 `관련 공식 문서` 영역에서만 표시한다.

#### 주요 lifecycle 승격 제한

대상 함수의 실제 body Diff가 확인되지 않은 Commit은 기본적으로 주요 lifecycle로 승격하지 않는다.

```text
대상 함수 body Diff 확인
→ 주요 Git 변경

함수명·선언만 Diff에 존재
→ 확인 필요 / 연관 Git 이력

Commit 메시지만 관련
→ 연관 Git 이력

키워드 검색에서만 수집
→ 연관 Git 이력
```

Commit 메시지나 공식 문서가 관련 있다는 이유만으로 대상 함수 주요 변경으로 승격하지 않는다.

#### 최초 Commit 문서 연결 보호

최초 추가 Commit은 이후 공식 문서와 자동 단계 연결하지 않는다.

단계 연결하려면 다음과 같은 명시적 근거가 필요하다.

```text
문서가 초기 구현을 직접 참조
최초 Commit Diff와 문서의 As-Is/To-Be가 동일 기능을 설명
동일 CSR/릴리스 계보가 명확
```

그 외에는 문서 연결 없음으로 표시한다.


### 1.7 v2.5 보완 정책 — 함수 Diff 판정 정확도, Repo 매칭 일관성, 관련 목록 표시

본 보완은 v2.5의 정책 방향을 변경하지 않는다. 실제 운영 테스트에서 확인된 구현 회귀와 표시 문제를 보완한다.

#### 1) 함수 변경 근거 판정 세분화

함수 lifecycle에서 Git Diff 근거를 다음 수준으로 구분한다.

```text
DIRECT_BODY_CHANGE
→ 대상 함수 본문 내부의 실제 변경 hunk를 확인

FUNCTION_CONTEXT_CHANGE
→ Diff hunk가 대상 함수 범위에 속함을 확인했으나
   자동 body 범위 추출이 완전하지 않음

SYMBOL_ONLY
→ 함수 선언, prototype, 호출부, 이름 문자열 등 Symbol만 확인

MESSAGE_ONLY
→ 대상 함수 Diff는 확인하지 못했고 Commit 메시지만 관련
```

lifecycle 기본 분류:

```text
DIRECT_BODY_CHANGE
→ 주요 Git 변경

FUNCTION_CONTEXT_CHANGE
→ 주요 Git 변경 가능
   단, Git 근거를 `함수 변경 구간 확인` 등 보수적 표현으로 표시

SYMBOL_ONLY
→ 연관 Git 이력

MESSAGE_ONLY
→ 연관 Git 이력
```

금지:

```text
함수 변경 hunk를 확인했는데 단순히 함수명 추출 실패 때문에 SYMBOL_ONLY로 강등
SYMBOL_ONLY인데 `Diff상 대상 함수 기능이 변경되었다`고 단정
Commit 메시지만으로 주요 변경 승격
```

C 코드의 K&R/Allman 스타일, 다중 라인 시그니처, macro/attribute, 중괄호 위치 차이 때문에 함수 body 추출이 실패하지 않도록 한다.

#### 2) 선택 코드 조회의 Repo 매칭

v2.5의 공식 식별 계약 `repo_id + repo_relative_path`는 유지한다.

다만 Extension의 Repo 식별 단계가 함수 조회보다 불필요하게 엄격해 사용자가 추가 설정을 요구받는 구조가 되지 않도록 한다.

Repo 식별 우선순위:

```text
1. 이미 확정된 repo_id
2. canonical remote URL 정규화 매칭
3. 기존 함수 조회/장비 설정에서 사용 중인 Repo 식별 정보 재사용
4. Repo 이름/Workspace Git root 이름 보조 매칭
5. 장비에 ready Repo가 정확히 1개일 때만 single-repo fallback
```

remote URL 정규화는 최소한 다음 형태가 동일 Repository인지 비교할 수 있어야 한다.

```text
git@host:path/repo.git
ssh://git@host/path/repo.git
https://host/path/repo
https://host/path/repo.git
```

다중 Repo 환경에서는 이름만으로 임의 선택하지 않는다. 매칭 실패 시 Backend/API 장애로 오안내하지 않는다.

Repo 매칭 실패 Output:

```text
원인: 현재 파일의 Git Repository를 장비 등록 Repo와 매칭하지 못했습니다.

확인 사항:
- 현재 Git remote URL
- 장비에 등록된 Repo URL/이름
- 현재 파일이 속한 Git root
```

서버/API 연결 오류는 별도 메시지로 표시한다.

#### 3) 관련 공식 문서의 소스/함수 목록 표시

관련 공식 문서에서 `관련 소스` 또는 `관련 함수` 목록이 많아 일부만 표시할 경우, 현재 조회 대상 파일과 대상 함수는 실제 원본 목록에 존재하면 반드시 표시한다.

예:

```text
관련 함수가 30개이고 기본 표시 한도가 10개
→ 조회 대상 함수 1개를 우선 포함
→ 나머지 9개 표시
→ `외 20개` 표시
```

관련 소스도 동일 원칙을 적용한다.

중요:

```text
원본 related_functions / related_sources 판정 데이터는 자르지 않는다.
화면 Markdown 표시 목록만 제한한다.
Evidence Link 판정은 전체 원본 목록을 사용한다.
```

따라서 화면에 일부 목록만 보인다는 이유로 문서 관계를 제거하거나 Evidence Link 정책을 변경하지 않는다.

#### 4) v2.5 보완 회귀 원칙

- 기존 함수 수준 문서 / Commit 수준 문서 분리 유지
- Commit 상세에는 direct/stage만 표시
- 함수 수준 관련 참고 문서 유지
- 날짜 band 하드 게이트 금지 유지
- Continue 재도입 금지
- Source Trace Output 정책 유지
- STEP 10 미완료 유지


### 1.8 v2.6 핵심 정책 — 결과 단순화와 공통 Repository resolver

#### 1) 사용자 목적

본 POC의 공식 결과 화면은 분류 시스템 자체를 보여주기 위한 것이 아니다.

사용자가 유지보수 중 가장 빠르게 확인해야 하는 정보는 다음 세 가지다.

```text
언제 변경되었는가
무엇이 변경되었는가
관련 변경 문서는 무엇인가
```

따라서 사용자 결과를 만들기 위해 불필요한 업무 의미 분류를 추가하지 않는다.

사용자 화면에서 제거:

```text
주요 개발 / 보조 변경 / 유지보수
공식 문서 / Commit 직접 연결 / 단계 연결 / 관련 참고의 등급 표시
분석 신뢰도(낮음/보통/높음)
```

이 정보가 내부 검증·필터링에 필요하면 내부 데이터로 유지할 수 있으나 공식 Markdown, Extension Output, 사용자 매뉴얼의 기본 결과에는 노출하지 않는다.

#### 2) 할루시네이션 최소화 원칙

공식 결과의 문장은 반드시 확인 가능한 근거에 묶는다.

우선순위:

```text
대상 함수/선택 코드의 실제 Git Diff
> Git Commit 메시지
> 관련 문서의 실제 텍스트/As-Is/To-Be/변경 내용
> 기타 후보 정보
```

규칙:

```text
Diff로 확인한 내용만 `코드에서 ... 변경`으로 서술
Diff가 없으면 Commit 메시지를 사실 그대로 요약하거나 인용 수준으로 표시
대상 함수 Diff를 확보하지 못했으면 그 사실을 명시
문서가 관련 있다고 해서 특정 Commit의 원인이라고 단정하지 않음
날짜/CSR/버전/Slide/Commit hash를 추정 생성하지 않음
```

Ollama/LLM은 공식 근거가 아니다. 사용하더라도 이미 확인된 Git/PPT 사실을 벗어난 날짜·원인·분류·연결 관계를 생성해서는 안 된다. 공식 결과 렌더링은 LLM 없이도 완성 가능해야 한다.

#### 3) 함수 변경 이력의 사용자 결과

함수 조회는 최초 확인 이후 시간순 이력을 한 화면에서 파악할 수 있게 한다.

기본 구조:

```text
한눈에 보기
변경 이력
변경 상세
관련 문서
전체 참조 근거(접힘)
```

`주요 개발 → 보조 변경 → 유지보수` 흐름은 생성하지 않는다.

#### 4) 관련 문서의 사용자 결과

관련 문서는 모두 `관련 문서`로 표시한다.

사용자에게 다음 등급을 표시하지 않는다.

```text
Commit 직접 근거
단계 연결 근거
관련 참고
공식/비공식 역할
문서 신뢰도
```

내부적으로 direct/stage/reference 등 Evidence Link 데이터를 유지할 수 있으나 이는 잘못된 문서를 걸러내기 위한 내부 판단 자료다.

사용자에게는 실제 문서 사실만 표시한다.

```text
문서 제목
파일명
작성일
적용 버전
CSR
Slide
주요 변경 내용
관련 소스
관련 함수
```

#### 5) 선택 코드 조회의 Repository 해석

함수 변경 이력 조회와 선택 코드 변경 근거 조회는 **동일한 Backend Repository resolver**를 사용한다.

선택 코드 조회가 Extension 단계에서 별도의 remote URL/name 매칭에 실패하여 Backend 호출 전에 종료되는 구조를 공식 경로로 사용하지 않는다.

공식 흐름:

```text
Extension
→ equipment_id
→ repo-relative file path
→ 선택 line 범위
→ Backend 요청

Backend 공통 Repository resolver
→ 함수 조회와 동일한 장비 Repo 해석
→ 대상 Repo 및 서버 clone path 결정
→ git blame / git show / line history
```

`repo_id`는 이미 확정된 경우 힌트로 전달할 수 있으나, Extension에서 URL/name 매칭에 실패했다는 이유만으로 조회를 중단하는 필수 전제조건으로 사용하지 않는다.

다중 Repo에서 같은 상대경로가 실제로 둘 이상 존재하여 Backend도 유일하게 결정할 수 없는 경우에만 `AMBIGUOUS_REPOSITORY`와 같은 명확한 오류를 반환하고, 필요한 경우 사용자가 Repo를 선택하게 한다.

정상적인 함수 조회가 같은 파일에서 성공하는 환경이라면 선택 코드 조회를 위해 별도 Repo 설정을 다시 요구하지 않는다.

#### 6) 변경 이력 수의 의미

`이후 Git 이력 N건`은 사용자에게 복잡한 분류를 노출하지 않는 중립적 집계다.

기본 집계는 보고서에 표시되는 최초 확인 이후 Git 이력 항목 수와 일치해야 한다.

실제 함수 Diff가 확인된 Commit과 메시지/검색으로만 관련된 Commit이 함께 표시될 경우, 각 행의 `변경 내용` 문구에서 근거 수준을 사실적으로 표현한다.

예:

```text
10분 재승차 기능 추가
기후동행카드 적용 관련 Commit (대상 함수 Diff 미확인)
```

변경 내용 생성 우선순위:

```text
1. 대상 함수의 실제 Diff
2. Commit 메시지의 명시적 사실
```

Commit 메시지는 Diff보다 강하게 해석하지 않는다. 별도의 `주요/보조/유지보수` 숫자를 만들지 않는다.


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
- Source Trace Extension (VSIX)
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
19. 장비 ID·서버 IP를 환경 독립 기본값으로 하드코딩하지 않는다 (`equipment_id=1` 기본 금지).
20. Git lifecycle과 관련 공식 문서는 별도 축으로 관리하며, 문서를 `최초 적용/후속 적용` 단계로 추정 분류하지 않는다.
21. STEP 10은 별도 승인 없이 진행하지 않는다.

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

## VS Code Extension (주 연계)

```text
TypeScript
VS Code Extension API
VSIX 배포 (오프라인 설치)
```

## IDE Client Architecture (v2.6 현행)

```text
Source Trace Backend v2.6 [Freeze]
- 공통 Git / PPT / Repository / Trace API
- IDE 독립
- Eclipse 추가를 이유로 Backend를 수정하지 않음

        |
     HTTP API
   -----+-----
   |    |    |
VS Code  Eclipse  VS2010    VS2017
Adapter  Adapter  (legacy)  (공식)

Reference Client: VS Code Source Trace Extension
Additional Clients:
- Eclipse Source Trace Plug-in
- Microsoft Visual Studio Source Trace Extension
  - Visual Studio 2017 / 15.x : 공식 (source-trace-visualstudio2017-0.1.3.vsix)
  - Visual Studio 2010 / 10.x : legacy compatibility (source-trace-visualstudio2010-0.1.3.vsix, VSIX schema 1.0)
  - Visual Studio 2022 : 공식 지원·배포 대상에서 제외
  - 동일 Backend API / 업무 프로젝트 무수정 / IDE Adapter만 버전별 분리
  - 공식 파일 식별: equipment_id + repo_relative_path
```

공통 원칙:

1. IDE별 클라이언트는 Adapter 역할만 수행한다.
2. Git / PPT / 변경 근거 판정은 Backend만 수행한다.
3. 동일 입력은 IDE와 관계없이 동일 Backend 결과를 사용한다.
4. 공식 파일 식별은 `repo_relative_path` 기반이다.
5. IDE local/remote absolute path는 서버 식별 기준이 아니다.

Eclipse Plug-in 제공 기능:

```text
서버 URL / 장비 설정
함수 변경 이력 조회 (POST /api/trace/report)
선택 코드 변경 근거 조회 (POST /api/trace/selection)
Backend Markdown 결과 표시
오프라인 로컬 p2 Update Site ZIP 설치 (운영PC PDE 불필요)
SOURCE ZIP은 설치용이 아님 (개발/백업용)
```

Eclipse 범위 제외:

```text
Eclipse용 별도 분석 엔진
Backend / DB / API 변경
장비 프로젝트 소스·.project/.cproject 변경
```

Visual Studio Extension 제공 기능 (공식: VS2017 0.1.3 / VS2010 0.1.3):

```text
서버 URL / 장비 설정 (Visual Studio 옵션)
함수 변경 이력 조회 (POST /api/trace/report)
선택 코드 변경 근거 조회 (POST /api/trace/selection)
Backend Markdown 결과 Tool Window 표시
오프라인 VSIX 설치 (산출물/운영PC/visualstudio/)
```

설치 파일:

```text
VS2010: source-trace-visualstudio2010-0.1.3.vsix
VS2017: source-trace-visualstudio2017-0.1.3.vsix
VS2022: 공식 설치 파일 없음 (POC 배포 대상 제외)
```

Visual Studio 범위 제외:

```text
Visual Studio용 별도 분석 엔진
Backend / DB / API 변경
장비 .sln/.vcxproj/소스 변경
C# / JS / Python Editor
단일 VSIX로 2010+2017 동시 설치
Visual Studio 2022 공식 지원 복원 (현재 POC 범위 밖)
```

Backend는 Source Trace Extension과 분리된 HTTP Service API로 구현한다.

## Continue 연동 제외

Continue는 PROJECT_SPEC v2.4의 공식 기능과 운영 범위에서 제외한다.

제거 대상:

```text
Continue Context Provider / Custom Tool / MCP 연동
Continue config.yaml 스니펫 생성·복사·열기
Continue 전용 Backend Context 생성
Continue 상태 API와 request_id/request_sequence 추적
Extension의 Continue polling 및 진행 Output
Continue 전용 설정·문서·체크리스트·테스트
```

Source Trace의 공식 결과는 VS Code Extension이 직접 표시하는 Markdown이다. 일반적인 Continue 설치·사용은 사용자의 별도 개발 도구 선택이며 본 프로젝트가 설정하거나 지원하지 않는다.

---

# 4. 전체 시스템 구조

```text
┌─────────────────────────────────┐
│ Source Trace VS Code Extension  │
│                                 │
│ "이 코드가 왜 변경됐어?"        │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ Change Trace HTTP API           │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│ FastAPI Backend                 │
│                                 │
│ Trace API                       │
│ Git Search + Function Lifecycle │
│ PPT Candidate Service           │
│ PPT On-demand Parser            │
│ Evidence Link + Lifecycle PPT   │
│ Optional Ollama Analysis        │
└───────┬─────────┬───────────────┘
        │         │
        ▼         ▼
┌────────────┐  ┌─────────────────┐
│ Git Repos  │  │ PPT Documents   │
└─────┬──────┘  └────────┬────────┘
      │                  │
      ▼                  ▼
┌─────────────────────────────────┐
│ SQLite / Cache                  │
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
├── vscode-extension/
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── eclipse-plugin/          # Eclipse Source Trace Plug-in (Adapter)
│
├── visualstudio-extension/  # Visual Studio Source Trace Adapter
│   ├── src/                 # 과거 VS2022 트리 보존 (공식 배포 대상 아님)
│   ├── tests/
│   ├── build-vsix.ps1
│   ├── vs2017/              # VS2017 / 15.x 전용 VSIX (별도)
│   ├── vs2010/              # VS2010 / 10.x 전용 VSIX (별도, schema 1.0)
│   └── README.md
│
├── integration/
│   └── continue/          # 선택 호환 참고
│
├── 산출물/
│   ├── 서버PC/
│   └── 운영PC/
│
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
├── AI_기반_...PROJECT_SPEC_v2.md
├── AI_기반_...PROJECT_SPEC_v2.1.md   # 과거 기준
├── AI_기반_...PROJECT_SPEC_v2.2.md   # 이전 기준
├── AI_기반_...PROJECT_SPEC_v2.6.md   # 현재 기준
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

---

# 9. 현재 핵심 사용자 인터페이스 (현행)

## 9.1 주 사용 인터페이스

주 사용 인터페이스는 **Source Trace VS Code Extension**이다.

```text
VS Code에서 함수 또는 코드 선택
→ Source Trace: 장비 변경 이력 조회
→ 질문 입력
→ Backend 분석
→ Git 함수 lifecycle 및 변경내역서 근거 Markdown 표시
```

Continue 연동은 공식 범위에서 제외한다. Extension 설치와 사용에 Continue 또는 Continue 설정 파일이 관여하지 않는다.

## 9.2 Web UI 역할

Web UI는 다음 목적으로 사용한다.

```text
시스템 상태 확인
장비 및 Git 저장소 관리
Git 동기화 및 변경 이력 검증
변경내역서 검색
PPT Cache 및 분석 상태 확인
Source Trace 조회 (Web Manual Client)
운영 및 장애 확인
```

### 9.2.1 브랜드 자산 (폐쇄망)

```text
웹 관리페이지 헤더 좌측
→ ATEC Mobility 원본 로고(`logo_web_header.png`)를 변형 없이 사용

웹 favicon
→ 제공 로컬 자산(`favicon.ico` / PNG) 사용

VS Code Extension 아이콘
→ ATEC Mobility 워드마크형(`extension_icon_256.png`) 사용
```

모든 브랜드 자산은 배포 패키지 내부에 포함하며 외부 CDN/온라인 이미지에 의존하지 않는다.

## 9.3 Extension 서버 및 장비 설정

### 최초 설정

Extension에서 최초 분석을 실행했는데 서버 또는 장비 설정이 없으면 설정 흐름을 시작한다.

```text
서버 주소 입력
→ 서버 연결 확인
→ 서버에 등록된 장비 목록 조회
→ 장비명을 보고 선택
→ 설정 저장
→ 원래 분석 요청 계속
```

사용자는 `equipment_id` 숫자를 미리 알거나 직접 입력할 필요가 없어야 한다.

### 설정 저장 정책

```text
서버 주소: 사용자 또는 Workspace 설정
장비 선택: Workspace 설정 우선
Workspace가 없으면 사용자 설정 사용
```

장비를 임의로 기본 선택하지 않는다. `equipment_id=1`과 특정 서버 IP를 환경 독립적인 기본값으로 사용하지 않는다.

### 장비 검증

분석 실행 전에 다음을 검증한다.

```text
서버 URL 형식
서버 연결 가능 여부
장비 선택 여부
현재 서버에 선택 장비가 존재하는지
```

잘못된 장비를 다른 장비로 자동 fallback하지 않는다.

### Continue 연동 제외 정책

Extension은 Continue 설정 파일을 탐색·열기·수정하지 않으며 설정 스니펫을 생성하지 않는다.

제거할 사용자 명령과 설정:

```text
Continue 설정 문구 보기/복사
Continue 설정 파일 열기
Continue 요청 진행 표시
sourceTrace.continueProgress
sourceTrace.continueProgressDetail
```

기존 사용자의 Continue 설정 파일은 프로젝트가 자동으로 수정하거나 삭제하지 않는다. 문서에서 수동 제거 안내만 제공할 수 있다.

---

# 10. 함수 Git lifecycle 분석 정책 (현행)

함수 또는 Symbol 질문에서는 단일 Top Commit만 표시하지 않고 전체 변경 흐름을 구성한다.

## 10.1 기본 원칙

함수 또는 Symbol 질문에서는 단일 Top Commit만 표시하지 않고 시간순 변경 이력을 구성한다.

- 최초 추가는 parent commit에서 기존 정의 존재 여부를 확인하여 판정한다.
- 함수 최초 추가는 한 건만 허용한다.
- Merge commit과 실질 변경이 없는 후보가 이력을 왜곡하지 않도록 한다.
- 가능한 경우 commit별 exact Diff를 사용한다.
- DB Diff가 부족하면 live `git show` fallback을 사용할 수 있다.
- Diff를 확보하지 못한 항목은 직접 확인된 함수 변경처럼 표현하지 않는다.
- PPT가 없어도 Git 이력은 누락하지 않는다.

내부 구현은 `DIRECT_BODY_CHANGE / FUNCTION_CONTEXT_CHANGE / SYMBOL_ONLY / MESSAGE_ONLY`와 같은 근거 상태를 유지할 수 있다. 이는 **사용자에게 주요 개발/보조/유지보수 등급을 보여주기 위한 것이 아니라 잘못된 설명을 막기 위한 검증 정보**다.

## 10.2 사용자 결과 구성

사용자 Markdown은 다음 구조를 기본으로 한다.

```text
1. 한눈에 보기
2. 변경 이력
3. 변경 상세
4. 관련 문서
5. 전체 참조 근거
```

사용자 결과에서 다음 lifecycle 분류 섹션은 제거한다.

```text
초기 개발 및 주요 기능 변경
개발 및 보조 변경
후속 Git 유지보수
연관 Git 이력
```

모든 Git 이력은 기본적으로 하나의 시간순 `변경 이력`으로 보여준다.

각 행의 변경 내용은 근거 수준에 따라 보수적으로 작성한다.

```text
실제 함수 Diff 확인
→ 확인된 코드 변경을 간결하게 설명

함수 context만 확인
→ 함수 변경 구간에서 확인된 변경이라고 표시

Commit 메시지만 관련
→ `<Commit 메시지 요약> (대상 함수 Diff 미확인)` 형태

근거 부족
→ 의미를 추정하지 않고 확인 가능한 사실만 표시
```

`기능 변경`, `유지보수`, `보조 변경`, `연관 이력` 같은 의미 분류 열을 사용자 기본 표에 두지 않는다.

---

# 11. 관련 문서 모델 (v2.6 현행)

Git 변경 이력과 변경내역서는 별도 근거 축으로 관리한다.

내부 Evidence Link는 잘못된 문서 승격을 막기 위해 유지할 수 있다. 그러나 **사용자 결과에서는 문서 등급을 표시하지 않고 모두 `관련 문서`로 통합한다.**

## 11.1 내부 Evidence Link

내부적으로 다음 관계를 유지할 수 있다.

```text
commit_direct
stage
reference
```

이 값은 후보 필터링, 회귀 테스트, 연결 근거 검증용이다.

사용자 Markdown/Output에서는 다음 문구를 기본 표시하지 않는다.

```text
Commit 직접 근거
단계 연결 근거
관련 참고
문서 신뢰도
```

내부 Evidence Link가 강하지 않다는 이유만으로 실제 함수/파일/기능과 관련된 문서를 숨길 필요는 없다. 반대로 날짜·제목·score만으로 관련 없는 문서를 표시해서도 안 된다.

## 11.2 관련 문서 판정

관련 문서 후보는 다음 실제 근거를 사용한다.

```text
related_functions의 대상 Symbol exact match
related_sources의 대상 repo-relative path match
문서의 기능/변경 내용과 실제 Git 변경 주제의 명시적 일치
CSR/버전/명시적 Commit 정보가 있으면 보조 사용
```

고정 날짜 임계값으로 문서를 배제하거나 역할을 정하지 않는다.

문서와 특정 Commit의 인과관계가 확인되지 않으면 인과관계를 생성하지 않는다.

## 11.3 사용자 문서 표시

각 문서는 다음 실제 필드 중심으로 표시한다.

```text
문서 제목
파일명
작성일
적용 버전
CSR
Slide
업무 배경
주요 변경 내용
As-Is/To-Be가 있으면 해당 내용
관련 소스
관련 함수
```

특정 Commit과의 연결이 매우 명확해도 사용자 기본 결과에서는 별도 `연결 유형` 등급을 붙이지 않는다.

필요한 경우 변경 상세에 문서명을 단순 `관련 문서`로 보여줄 수 있다. 이때도 `이 문서 때문에 이 Commit이 변경되었다`는 식의 인과 표현은 근거가 있을 때만 허용한다.

## 11.4 문서 검색어 정규화

한글 기능 토큰은 단어 순서에만 의존하지 않는다.

```text
청소년 후불
후불 청소년
청소년후불
후불청소년
```

공통 토큰 후보를 찾되, 변경 행위를 구분한다.

```text
적용/추가/도입
수정/보완
삭제/제거
테스트/로그 정리
```

토큰 집합이 같다는 이유만으로 동일 변경으로 단정하지 않는다.

## 11.5 시간 및 행위 정보의 사용 범위

문서와 Git 이력의 관련성 검증에 다음 정보는 보조 근거로 사용할 수 있다.

```text
commit 날짜
문서 작성일
배포 예정일
적용 버전
함수/소스 일치
변경 행위 일치
```

금지:

```text
270일 등 고정 임계값으로 문서 역할 결정
가장 오래된 문서를 최초 적용 문서로 자동 승격
최초 Commit과 가까운 문서를 최초 추가 문서로 자동 승격
문서 작성일만으로 후속 유지보수 문서로 단정
```

특정 함수명·Commit hash·PPT 파일명을 조건문에 하드코딩하지 않는다.

## 11.6 PPT 소스 및 함수 파싱

PPT의 `소스/함수` 영역은 다음 필드로 분리한다.

```text
related_source_paths
related_symbols
```

### 소스 경로

- `.c`, `.h`, `.cpp` 등 파일 경로만 포함
- 경로 prefix 정규화
- 제어문자 제거
- 중복 제거

### 함수 및 Symbol

- 함수명, 구조체명, 상수명
- 경로 문자열 제외
- `()`는 표시 단계에서 일관되게 처리
- 제어문자와 불필요한 줄바꿈 제거
- 경로 토큰에서 잘못 생성된 함수명 제외

관련 소스·함수의 **판정은 전체 원본 목록**을 사용한다.

Markdown 표시 개수를 제한할 때는 현재 조회 대상 파일/함수가 원본 목록에 존재하면 우선 노출하고 나머지를 `외 N개`로 표시한다.

---


# 12. 결과 Markdown · Output · 사용자 문서 (v2.6 현행)

## 12.1 함수 변경 이력 — 한눈에 보기

최소 다음 정보만 표시한다.

```text
최초 확인
이후 Git 이력
관련 문서
조회 파일
```

예:

```markdown
# fare_is_xfer 변경 이력

## 한눈에 보기

| 항목 | 결과 |
|---|---|
| 최초 확인 | 2017-09-19 · `2af9a2f8` |
| 이후 Git 이력 | 10건 |
| 관련 문서 | 2건 |
| 조회 파일 | `src/fare_calc.c` |
```

조회 파일은 장비 Git Repository 기준 `repo_relative_path`로 통일한다.
함수 조회와 선택 코드 조회에서 같은 파일이 서로 다른 경로로 표시되지 않도록 한다.
Commit short hash는 사용자 결과에서 8자리로 통일한다.
사용자 기본 결과에서 제거:

```text
주요 개발 N건
보조 변경 N건
유지보수 N건
Commit 직접 연결 문서 N건
단계 연결 문서 N건
관련 참고 문서 N건
분석 신뢰도
```

## 12.2 함수 변경 이력 — 메인 표

기존 `핵심 변경 흐름`을 공식 메인 결과인 `변경 이력`으로 단순화한다.

기본 형식:

```markdown
## 변경 이력

| 날짜 | Commit | 변경 내용 |
|---|---|---|
| 2017-09-19 | `2af9a2f` | 함수 최초 확인 |
| 2018-11-05 | `92df02c` | 환승·재승차 판정 조건 변경 |
| 2023-07-03 | `8de644d` | 10분 재승차 관련 조건 변경 |
| 2023-11-14 | `5e7eb05` | 기후동행카드 적용 관련 Commit (대상 함수 Diff 미확인) |
```

제거할 열:

```text
구분
Git 근거
문서 연결
```

이 값은 내부 검증 데이터로 유지할 수 있지만 사용자가 한눈에 이력을 보는 기본 표에는 노출하지 않는다.

변경 내용 생성 규칙:

```text
DIRECT_BODY_CHANGE / FUNCTION_CONTEXT_CHANGE
→ 실제 Diff에서 확인된 변경을 간결하게 설명

SYMBOL_ONLY / MESSAGE_ONLY
→ 함수 변경으로 단정하지 않음
→ Commit 메시지 기반 사실 + `(대상 함수 Diff 미확인)` 같이 제한 명시
```

Commit 메시지가 충분히 명확하면 불필요하게 의미를 재분류하지 않는다.

## 12.3 변경 상세

변경 상세는 하나의 시간순 섹션 안에 `<details>`로 제공한다.

별도 `초기 개발/주요 기능/보조/유지보수/연관 이력` 하위 섹션을 만들지 않는다.

Commit 메시지와 실제 Diff 확인 결과를 분리한다.

```text
- Commit 메시지: …          ← Commit 작성자가 남긴 사실
- 코드에서 확인: …          ← 대상 함수 Diff에서 검증된 사실만
```

`코드에서 확인`에 Commit 메시지를 복사하거나 Diff 결과처럼 재표현하지 않는다.
근거 없는 `~했을 수 있습니다` / `~로 보입니다` 형태의 추측성 문장을 생성하지 않는다.

예:

```markdown
## 변경 상세

<details>
<summary>2023-07-03 · <code>8de644d3</code> · 10분 재승차 기능 추가 …</summary>

- Commit 메시지: `# 10분 재승차 기능 추가 및 5분 재개표 10분 재승차 이벤트 추가`
- 코드에서 확인:
  - 환승·재승차 판정 조건 변경
- 관련 문서: `프로그램변경내역서_….pptx`, Slide 3

</details>
```

사용자 기본 상세에서 제거:

```text
변경 성격
신뢰도
연결 유형
연결 근거 등급명
```

Diff를 확보하지 못한 경우:

```markdown
- Commit 메시지: `기후동행카드 적용 건.`
- 확인 상태: 대상 함수의 세부 Diff는 확인하지 못했습니다.
```

이 경우 `코드에서 확인` 섹션을 만들지 않는다.

사실보다 강한 설명을 만들지 않는다.

부모 Commit 검증이 완료되지 않은 최초 항목:

```text
이 Commit에서 함수 원형과 구현이 최초로 확인되었습니다.
```

부모 Commit에 함수가 없음을 실제로 확인한 경우에만:

```text
함수 원형과 구현이 새로 추가되었습니다.
```

Commit 상세의 관련 문서는 **Commit 직접(exact) 연결**만 간단히 표시하고,
stage/reference 문서는 하단 `## 관련 문서`에서만 보여 준다.

## 12.4 관련 문서

섹션 이름은 `관련 문서`로 통일한다.

```markdown
## 관련 문서
```

각 문서에 최소 다음을 표시한다.

```text
문서 제목
파일명
작성일
적용 버전
CSR
Slide
업무 배경 또는 주요 변경 내용
관련 소스
관련 함수
```

사용자에게 다음 등급은 표시하지 않는다.

```text
Commit 직접 근거
단계 연결 근거
관련 참고
분석/문서 신뢰도
```

관련 소스·함수 목록이 길면 현재 조회 대상 파일/함수를 우선 표시하고 `외 N개`로 축약한다.

접힘 영역 제목은 `관련 소스·함수 보기`이다.
사용자 Markdown에 `### 연결 Commit` 목록이나 `확정된 단일 Commit은 없습니다.`를 노출하지 않는다.
Commit↔문서 Evidence Link·score·후보 Commit은 내부 검증용으로만 유지한다.

문서가 없으면:

```text
관련 문서를 찾지 못했습니다.
```

## 12.5 집계 일관성

다음 값은 같은 최종 컬렉션을 기준으로 한다.

```text
한눈에 보기의 이후 Git 이력 N건
변경 이력 표의 최초 확인 이후 행 수
변경 상세의 Git 이력 항목 수

한눈에 보기의 관련 문서 N건
관련 문서 섹션의 unique 문서 수
Extension Output의 관련 문서 N건
```

내부 Evidence Link 유형별 개수는 사용자 집계로 사용하지 않는다.

## 12.6 Extension Output 정책

Output Channel은 진행 상태와 최소 결과만 보여준다.

### 함수 조회

```text
[시간] Source Trace 분석 시작
장비: ...
요청: 함수 변경 이력 조회
함수: ...
파일: ...

[시간] 서버 요청 전송
[시간] 분석 결과 수신
[시간] Git 이력: N건
[시간] 관련 문서: N건
[시간] 결과 문서 생성
[시간] 분석 완료 (소요 시간)
```

제거:

```text
주요 개발/보조/유지보수 집계
Commit 직접 연결 문서 수
단계 연결 문서 수
관련 참고 문서 수
분석 신뢰도
```

### 선택 코드 조회

Extension이 Repository를 자체 확정하지 못했다는 이유로 Backend 요청 전 실패시키지 않는다.

```text
[시간] Source Trace 분석 시작
장비: ...
요청: 선택 코드 변경 근거
함수: ...
파일: ...
범위: ...

[시간] 서버 요청 전송
[시간] Repository 확인
[시간] Git blame 조회
[시간] 현재 라인 Commit: ...
[시간] 변경 Diff 확인
[시간] 관련 문서: N건
[시간] 분석 완료
```

Repository ambiguity/error가 발생하면 Backend가 반환한 실제 이유를 출력한다.

기본 Output에서 제외:

```text
raw request body
전체 Diff
내부 score
remote credential
비밀번호·토큰
민감한 서버 절대경로
```

## 12.7 선택 코드 변경 근거 결과

선택 코드 조회는 다음 구조를 사용한다.

```markdown
# 선택 코드 변경 근거

## 선택 코드
```c
...
```
- 파일: `repo_relative_path`
- 범위: N행
- 포함 함수: `symbol()`

## 현재 라인의 Git 근거
| 행 범위 | Commit | 변경일 | 작성자 | 변경 유형 | Commit 메시지 |

## 실제 변경 내용

### 변경 전
```c
...
```

### 변경 후
```c
...
```

- Commit: `xxxxxxxx`
- Commit 메시지: `...`

(이전/현재 분리가 어려우면 선택 라인이 포함된 최소 Diff hunk만 표시)

## line history
## 관련 문서
## 함수 전체 이력
```

`git show`에서 선택 line/range와 겹치는 hunk만 추출한다. 전체 파일 Diff는 출력하지 않는다.

변경 유형(`추가`/`수정`/`삭제`)은 Diff로 확인할 수 있을 때만 표시하고, 확정하지 못하면 `변경 Commit 확인` 등 중립 표현을 사용한다.

`git log -L`이 실패하거나 0건이어도 blame 결과는 유지한다.

선택 코드 결과에서 금지:

```text
Extension의 remote URL/name 매칭 실패만으로 Backend 호출 전 종료
선택 코드와 직접 관계가 확인되지 않은 최고 점수 Commit을 대표 근거로 표시
함수 전체 문서를 선택 라인의 직접 원인 문서로 단정
Diff 확인 없이 업무 의미 단정
날짜·Slide·CSR 추정 생성
전체 파일 Diff 출력
```

## 12.7.1 Extension command 기여 일관성

공식 사용자 명령:

```text
sourceTrace.analyzeFunctionHistory
sourceTrace.analyzeSelectedCode
```

`sourceTrace.analyzeSelection`은 구버전 호환용으로만 `registerCommand`할 수 있으며,
`contributes.commands` / menus / commandPalette에 노출하지 않는다.
menus에서 참조하는 command는 반드시 `contributes.commands`에 존재해야 한다.
## 12.8 Repository resolver 공통화

함수 조회와 선택 코드 조회는 동일한 Backend resolver 함수를 호출해야 한다.

권장 입력:

```text
equipment_id
repo_relative_path
repo_id_hint(optional)
```

선택 코드 조회 추가 입력:

```text
start_line
end_line
selected_code
enclosing_symbol
revision
```

공통 resolver의 책임:

```text
장비에 등록된 ready Repo 목록 확인
repo_id_hint가 유효하면 우선 사용
repo-relative path가 존재하는 Repo 탐색
기존 함수 조회의 path alias/정규화 규칙 재사용
유일한 Repo 결정
Repo root 밖 경로 차단
```

여러 Repo에 동일 파일이 존재하여 유일하게 판단할 수 없으면 명시적 ambiguity 오류를 반환한다.

Extension의 remote URL canonicalization/name matching은 진단용 또는 optional hint 생성에만 사용할 수 있으며 공식 조회의 필수 gate가 아니다.

## 12.9 불확실성 및 할루시네이션 방지

사용자에게 의미 없는 일반 `분석 신뢰도` 등급은 출력하지 않는다.

대신 특정 항목의 근거가 부족할 때 그 항목 바로 옆에 사실적인 제한만 표시한다.

예:

```text
대상 함수의 세부 Diff 미확인
부모 Commit 확인 불가
관련 문서는 확인했지만 특정 Commit과의 직접 관계는 확인하지 않음
```

금지:

```text
근거 없는 기능명 생성
Commit 메시지보다 강한 원인 추정
문서 제목만으로 Git 변경 사유 단정
관련 문서를 특정 Commit의 원인으로 자동 승격
```

## 12.10 Continue 연동 제외 정책

Continue 결과는 본 프로젝트의 공식 결과가 아니다.

```text
공식 조회: Source Trace VS Code Extension 직접 결과
공식 근거: Git Commit / Diff / PPT / Slide / CSR
제외: Continue 모델 재작성 결과와 Agent/Skill/Tool 호출 결과
```

## 12.11 README 및 사용자 문서

README와 운영PC 사용자 매뉴얼은 새 단순 결과 구조를 기준으로 설명한다.

사용자에게 주요/보조/유지보수 분류 또는 direct/stage/reference 문서 등급을 학습하도록 요구하지 않는다.

## 12.12 v2.6 회귀 테스트

### 함수 결과

1. 한눈에 보기에 `최초 확인 / 이후 Git 이력 / 관련 문서 / 조회 파일`만 기본 표시
2. 주요 개발/보조/유지보수 집계 제거
3. direct/stage/reference 문서 집계 제거
4. 분석 신뢰도 제거
5. `변경 이력`이 날짜/Commit/변경 내용 3열로 표시
6. 시간순 정렬 유지
7. Diff 확인 항목은 실제 Diff + Commit 메시지 사실 기반 서술
8. Message-only 항목은 함수 변경으로 단정하지 않음 (`대상 함수 Diff 미확인`)
9. 변경 상세이 하나의 시간순 섹션으로 통합
10. stage/reference 문서는 Commit 상세에 반복하지 않고 하단 `관련 문서`에 표시
11. 관련 함수/소스 대상 우선 표시 및 `외 N개` 유지
12. 내부 Evidence Link 회귀로 잘못된 문서가 증가하지 않음
13. 부모 Commit 미검증 최초 항목은 `최초 확인` 표현(새로 추가 단정 금지)
14. short hash 8자리, 조회 파일 경로를 선택 조회와 동일 기준으로 표시
### Repository resolver

13. 함수 조회에서 성공한 동일 equipment/file이 선택 코드 조회에서도 동일 Backend resolver를 사용
14. Extension repo URL/name 매칭 실패가 Backend 호출을 차단하지 않음
15. Remote-SSH 절대경로와 Backend clone 절대경로가 달라도 성공
16. 다중 Repo에서 상대경로로 유일 Repo를 결정
17. repo_id_hint가 있으면 유효성 검증 후 사용
18. 동일 상대경로가 여러 Repo에 있으면 ambiguity 오류
19. `..`/symlink escape 차단
20. Backend resolver 성공 후 실제 `git blame` 실행
21. blame 성공 + line history 실패 시 blame 결과 유지
22. 선택 라인 direct 문서가 없어도 Git 결과 유지

### Output / 배포

23. 함수 Output에 Git 이력 N건/관련 문서 N건만 최소 집계
24. 선택 조회 Output이 Backend 요청 전 repo matching 오류로 종료되지 않음
25. Repo 오류와 서버 연결 오류 구분
26. Source Trace Output 유지
27. Continue 미재도입
28. Backend 전체 테스트 통과
29. Extension 전체 테스트 통과
30. 새 VSIX 패키징
31. 운영PC 산출물 갱신
32. 서버PC deploy 갱신
33. README/매뉴얼/체크리스트 현행화
34. STEP 10 미완료 유지

## 12.13 산출물 원칙

수정된 내용들을 산출물 폴더에 업데이트/반영한다.

```text
PROJECT_SPEC v2.6
vscode-extension README
운영PC 사용자 매뉴얼
00_읽어보세요.md
참고_README.md
테스트 체크리스트
서버PC 테스트 체크리스트
운영PC VSIX
서버PC deploy
```

사용자가 별도 버전 변경을 지시하기 전에는 임의로 `v2.6.1`, `v2.6.0.1` 등 새 PROJECT_SPEC 버전을 생성하지 않는다.

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

## 상태

**완료**

## 목표

Extension 연계와 별도로 Backend 단독으로 "변경 이유 추적 요청"을 받을 수 있는 핵심 Trace API를 구현한다.

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

Extension에서 현재 파일 또는 선택 코드 정보를 전달할 수 있을 때 사용한다.

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

## 상태

**완료**

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

## 상태

**완료**

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

## 상태

**완료** (lifecycle 단계 연결은 §11로 현행화)

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

## 상태

**완료**

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

# STEP 9. VS Code Extension 연계 (주 인터페이스)

## 상태

**완료 (현행 기준: Source Trace Extension 0.1.8 계열)**

## 목표

개발자가 VS Code에서 함수/Symbol 전체 Git lifecycle을 조회하거나, 선택한 라인·코드 블록의 실제 Git 변경 근거를 별도 모드로 조회할 수 있도록 한다.

주 경로:

```text
함수/Symbol 조회
Source Trace VS Code Extension
→ POST /api/trace/analyze
→ Git lifecycle + 관련 공식 문서 Markdown

선택 코드 조회
Source Trace VS Code Extension
→ POST /api/trace/selection
→ Git blame + line history + 직접 근거 Markdown
```

Continue 연동은 제외한다. Extension 단독으로 모든 공식 조회 기능을 제공한다.

## Extension 핵심 기능

```text
함수/Symbol 선택 후 `함수 변경 이력 조회`
선택한 라인·코드 블록에서 `선택 코드 변경 근거 조회`
서버 및 장비 설정 (장비명 Quick Pick)
서버 연결 확인 / 장비 변경 / 현재 설정 보기
분석 진행 Output Channel
결과 Markdown 문서 표시
```

설정 정책은 §9.3을 따른다. `equipment_id=1` 기본값·특정 서버 IP 기본값을 사용하지 않는다.

## Backend 핵심 API

Source Trace Extension은 조회 모드에 따라 다음 중립 Trace API를 호출한다.

```http
POST /api/trace/analyze
POST /api/trace/selection
```

기존 `/api/continue/trace`가 Extension에서 사용 중이면 마이그레이션 기간 동안 내부 호환 alias로만 유지할 수 있다. 신규 코드·문서·테스트는 `/api/trace/analyze`를 기준으로 한다.

요청 예:

```json
{
  "equipment_id": 3,
  "query": "card_mif_post_check_valid_birthday_usertype 함수의 변경이력을 찾아줘
현재 선택한 조건문은 언제 어떤 Commit에서 변경됐어?",
  "file_path": "Card/mif_post/src/card_mif_postpay.c",
  "selected_code": "card_mif_post_check_valid_birthday_usertype",
  "source_mode": "selection_symbol",
  "detected_symbol": "card_mif_post_check_valid_birthday_usertype",
  "use_ollama": false
}
```

응답은 사용자 Markdown(`content`)과 선택적 debug/lifecycle_summary를 포함한다. 함수 Symbol 질문의 본문은 §10~§12의 Git lifecycle·관련 공식 문서 독립 표시 계약을 따른다.

선택 코드 조회 요청 예:

```json
{
  "equipment_id": 1,
  "repo_id": 2,
  "repo_relative_path": "Fare/src/fare_calc.c",
  "start_line": 651,
  "end_line": 651,
  "selected_code": "if (trans_info_ptr->is_climate_init == CLIMATE_CLEAR_PENALTY)",
  "enclosing_symbol": "fare_is_xfer",
  "revision": "HEAD"
}
```


선택 코드 조회의 파일 식별은 다음 순서를 따른다.

```text
Extension: 현재 파일의 Git root 탐지
→ 장비 등록 Repo와 매칭
→ repo_id + repo_relative_path 생성
→ Backend: repo_id 검증
→ 서버측 Repo root + repo_relative_path 결합
→ resolve/정규화
→ Repository 내부 파일 검증
```

다중 Repo에서 같은 상대경로가 존재할 수 있으므로 `repo_relative_path` 단독으로 Repo를 추정하지 않는다.

선택 코드 조회 Backend는 다음 순서를 따른다.

```text
git blame -L start,end
→ blame Commit Diff 확인
→ git log -L 또는 동등한 line history
→ 직접 연결 문서 탐색
→ 선택 코드 전용 Markdown
```

Git/PPT 키워드 후보 검색은 보조 수단으로만 사용하며 blame·Diff 근거를 대체하지 않는다.


## 현재 코드 Context

가능한 경우 Extension에서 다음 정보를 전달한다.

```text
현재 Workspace
현재 파일 경로
선택 코드 / 감지 Symbol
선택 시작 행·종료 행
포함 함수/Symbol
사용자 질문
source_mode / detected_symbol (진단용, 기본 Output 비표시)
```

장비는 사용자가 선택한 설정을 사용한다. 자동 매칭 실패 시 장비를 임의 선택하지 않는다.

## Continue 연동 제거

- Continue Context Provider·Tool·Skill·MCP 연동을 제공하지 않는다.
- Extension은 Continue 설정 파일이나 모델 설정을 다루지 않는다.
- 기존 Continue 전용 코드와 문서는 제거한다.
- 사용자가 Continue를 일반 개발 도구로 별도 사용하는 것은 본 프로젝트 범위 밖이다.

## 답변 형식

§12 Markdown 계약을 따른다. 요약 예:

```text
# <함수명> 변경 이력

## 한눈에 보기
- 최초 확인 Commit
- Git 변경 흐름
- 관련 공식 문서: N건
- Commit 직접 연결 / 단계 연결 / 관련 참고 건수

## 변경 상세
- 최초 확인
- 핵심 기능 변경
- 개발 및 보조 변경
- 후속 Git 유지보수

## 관련 공식 문서
- 문서별 파일명·Slide·CSR·버전
- 연결 Commit
- 연결 유형
- 연결 근거
```

근거가 부족한 경우 Git lifecycle은 유지하고, 변경내역서 부재·Diff 미확보를 사용자 언어로 구분한다.

선택 코드 조회는 다음 별도 형식을 따른다.

```text
# 선택 코드 변경 근거
- 선택 위치와 포함 함수
- 현재 blame Commit
- 실제 Diff
- line history
- 직접 연결 공식 문서
- 추적 제한
```

함수 전체 이력은 선택 코드 결과에 자동 병합하지 않고 별도 조회 안내만 제공한다.


## 테스트 질문

```text
이 코드가 왜 변경됐어?
CHILD_FARE가 언제 추가됐어?
CalcFare 함수 변경 이유 찾아줘
card_mif_post_check_valid_birthday_usertype 함수의 변경이력을 찾아줘
```

## 완료 조건

- Extension에서 함수/Symbol 전체 이력 조회 가능
- Extension에서 선택 라인·코드 블록의 blame/line history 기반 직접 근거 조회 가능
- 서버·장비 설정 및 검증 가능
- Trace Backend 호출 및 lifecycle Markdown 표시
- Git lifecycle·관련 공식 문서 독립 표시 및 집계 일관성 (§11~§12)
- Extension 단독 사용
- 내부망에서 외부 연결 없음

---

# STEP 10. 운영환경 배포 및 단계별 검증

## 상태

**진행 중 — 미완료 항목: 실제 서버PC/운영PC 오프라인 배포, 실제 장비·Git·PPT 데이터 기반 함수/선택 코드 조회, 운영PC Extension UI 육안 검증.**

(2026-08-10 STEP 10 진행 승인됨. 개발 PC 로컬 기동·브랜드 자산·산출물/자동테스트는 부분 확인. 상세: `산출물/서버PC/STEP10_운영환경_최종배포_검증결과.md`)

## 목표

인터넷이 차단된 내부 서버와 운영 PC에서 실제 사용 가능하도록 배포한다.
(현재는 `산출물/` 및 `package-deploy`로 STEP 6 이후 운영 패키지를 유지하며, STEP 10 전체 검증은 승인 후 수행 중이다.)

## 배포 구조

```text
운영 PC
VSCode + Source Trace Extension
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

# 13. 운영환경 테스트 시점

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

Extension 실제 사용 시나리오 테스트:

```text
현재 코드 선택
질문
Backend 호출
Git 추적
PPT 탐색
Cache
Ollama
Evidence 확인
```

---

# 14. 테스트 결과 기록

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

# 15. Logging

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
Extension Trace Request
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

# 16. Error 처리 원칙

사용자 화면 또는 Extension 응답에 Python Exception을 그대로 표시하지 않는다.

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

# 17. 테스트 자동화

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
Extension Integration
```

Ollama는 일반 Unit Test에서 직접 호출하지 않는다.

Mock/Fake Response를 사용한다.

---

# 18. Cursor 작업 원칙

Cursor는 각 작업 시작 시 다음을 확인한다.

```text
PROJECT_SPEC v2.4 (본 문서)
현재 구현 상태
기존 테스트
DB Schema
TEST_PLAN.md / 산출물 가이드
```

이미 완료된 STEP 0~9 기능을 새 방향에 맞춘다는 이유로 임의 재작성하지 않는다.
현행 정책(§9~§12) 반영이 필요하면 최소 범위로 수정한다.

STEP 0~9는 현재 구현을 기반으로 유지한다. STEP 10은 승인 없이 시작하지 않는다.

변경이 필요한 경우:

```text
변경 이유
영향 범위
수정 파일
기존 테스트 영향
```

을 먼저 확인하고 최소 범위로 수정한다.

---

# 19. Cursor 단계별 완료 보고 형식

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

STEP별·현행 정책 핵심 설계도 보고한다.

산출물 관련 작업 시 추가로 보고한다.

```text
VSIX 버전 및 패키징 결과
서버PC/운영PC 산출물 반영 여부
PROJECT_SPEC v2.5.1 반영 여부
```

---

# 20. 금지 사항

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

외부 AI Plugin 구조를 Source Trace 필수 구조로 강제

equipment_id=1 또는 특정 서버 IP를 전역 기본값으로 강제

후속 유지보수 문서를 초기 개발 commit 전체에 일괄 복제

Diff 미확보 상태에서 Commit 직접 근거 표시

대표 기능명을 후속 삭제 문서 제목만으로 덮어쓰기

Extension README에 STEP/MVP/POC 데모·폐기된 연동 비교 이력 유지
```

---

# 21. 최종 완료 시나리오

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

Extension에서 코드를 선택하고 장비 변경 이력을 조회한다.

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

Extension에 lifecycle Markdown 결과를 표시한다.

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
Extension VSIX 설치 및 서버·장비 설정
변경 추적 질문 수행
```

---

# 22. 현재 개발 상태 및 다음 작업

현재 완료 (현행):

```text
STEP 0 ~ STEP 8 완료
STEP 9 완료 — Source Trace VS Code Extension (주 인터페이스)
함수 Git lifecycle + 관련 공식 문서 독립 연결·표시 (§10~§12)
Extension 서버·장비 설정 / Output / 사용자 README
산출물 서버PC deploy · 운영PC VSIX 동기화 체계
```

다음 작업:

```text
STEP 10 진행 중 — 실제 서버PC/운영PC + 장비·Git·PPT 데이터 smoke 잔여
필요 시 §9~§12 정책내의 최소 범위 개선
```

추가 IDE (승인된 POC 보완, Backend Freeze 유지):

```text
Eclipse Source Trace Plug-in — Adapter 추가 (서버 무수정)
산출물: eclipse-plugin/, 산출물/운영PC/Eclipse_Source_Trace_설치_사용_가이드.md
Microsoft Visual Studio Source Trace Extension — Adapter 추가 (서버 무수정)
  Visual Studio 2017 / 15.x 공식 VSIX 0.1.3
  Visual Studio 2010 / 10.x legacy VSIX 0.1.3 (VSIX schema 1.0)
  Visual Studio 2022 : 공식 지원·배포 대상에서 제외
산출물: visualstudio-extension/, visualstudio-extension/vs2017/, visualstudio-extension/vs2010/,
        산출물/운영PC/visualstudio/,
        VisualStudio_Source_Trace_설치_사용_가이드.md,
        VisualStudio2017_Source_Trace_설치_사용_가이드.md,
        VisualStudio2010_Source_Trace_설치_사용_가이드.md
```

아직 다음을 기본 범위로 확대하지 않는다.

```text
Vector DB
OCR (이미지 중심 PPT 비율 확인 후 재검토)
제거된 Continue 연동을 승인 없이 다시 도입하는 작업
```

참고: Eclipse 추가가 STEP 10 완료 판정을 대체하거나 변경하지 않는다. STEP 10은 기존 검증결과 문서를 따른다.

신규 작업 시 본 문서(PROJECT_SPEC v2.6)를 최우선으로 참고하고, 완료 보고 형식(§19)과 산출물 원칙(§12.10)을 따른다.
