# VS Code Extension — 장비 변경 이력 조회 (설치 가이드)

**현재 테스트 대상 버전**: `source-trace-vscode-0.5.5.vsix` (결과 Untitled Markdown · 자동 Preview 없음)

> 장비 등록부터 Extension 사용까지 **전체 사용자 절차**는  
> 상위 폴더 **`../사용자_사용_매뉴얼.md`** 를 먼저 보세요.

## 이 폴더 용도

VS Code에서 소스 코드 일부를 **선택한 채로** 바로 "장비 변경 이력 조회"를 실행하기 위한
Extension 설치 파일이다. **서버 소프트웨어가 아니다** — 운영 담당자/개발자의
**개인 PC의 VS Code**에 설치한다. Node.js/npm 설치가 필요 없다. `.vsix` 파일 하나만
있으면 설치할 수 있다.

> Source Trace VS Code Extension의 직접 조회 결과가 이 프로젝트의 **유일한 공식
> 조회 경로**다. 현재 선택한 코드와 파일 경로를 VS Code가 직접 읽어 Backend로
> 정확히 전달한다. 별도 AI 채팅 도구 연동은 지원하지 않는다.

## 폴더 구성

| 파일 | 용도 |
| --- | --- |
| `source-trace-vscode-0.5.5.vsix` | VS Code에 설치할 Extension 패키지 |
| `00_읽어보세요.md` | 이 문서 — 설치/설정/사용 가이드 |
| `테스트_체크리스트.md` | 설치 후 동작 확인 체크리스트 |
| `참고_README.md` | 상세 참고 (기능·설정·오류 해결) |

## 1. 설치 방법

**방법 A — VS Code 화면에서 설치**

1. VS Code 실행
2. Extensions(확장) → `...` → **VSIX에서 설치... (Install from VSIX...)**
3. `source-trace-vscode-0.5.5.vsix` 선택
4. 설치 완료 확인 (필요 시 VS Code 재시작)

**방법 B — 명령줄**

```bat
code --install-extension "source-trace-vscode-0.5.5.vsix"
```

> 이전 버전을 설치했다면 **0.5.5로 재설치**하세요.

## 2. 설정 (필수)

`F1` → `Source Trace: 서버 및 장비 설정`을 실행해 서버 주소 입력 → 연결 확인 →
장비 선택을 완료하는 방법을 권장합니다. 직접 입력하려면:

`F1` → `Preferences: Open User Settings (JSON)`:

```json
{
  "sourceTrace.serverUrl": "http://<서버IP>:8010",
  "sourceTrace.equipmentId": 1,
  "sourceTrace.useOllama": false,
  "sourceTrace.maxSelectedCodeChars": 4000,
  "sourceTrace.showDebug": false
}
```

| 설정 | 설명 |
| --- | --- |
| `sourceTrace.serverUrl` | 상위 폴더 `server_host.txt`와 동일한 서버 IP. `/api/...` 경로는 붙이지 않는다 |
| `sourceTrace.equipmentId` | Web UI **장비 관리**에서 확인한 장비 ID |
| `sourceTrace.useOllama` | 기본 `false` 권장 (§4 참고) |
| `sourceTrace.maxSelectedCodeChars` | 기본 `4000` 유지 |
| `sourceTrace.showDebug` | 기본 `false`. true일 때만 결과 Markdown 하단에 debug 표시. 로그는 항상 Output Channel `Source Trace`에 기록 |

## 3. 사용 방법

용도에 맞는 명령을 선택합니다.

```text
함수 전체 변경 흐름을 볼 때
→ Source Trace: 함수 변경 이력 조회

현재 선택한 한 줄·코드 블록의 실제 변경 Commit을 볼 때
→ Source Trace: 선택 코드 변경 근거 조회
```

### 3-1. 함수 변경 이력 조회

1. 소스 파일(`.c`, `.h` 등)을 연다
2. 함수명을 **더블클릭**하거나 코드 일부를 **드래그**로 선택한다
3. **우클릭 → `Source Trace: 함수 변경 이력 조회`** (또는 `F1` → 동일 명령)
4. 질문 입력 (기본: `선택한 코드가 왜 변경됐는지 알려줘`)
   - 예: `이 함수 언제 추가되었어?` → Extension이 `test_Alias 함수 언제 추가되었어?`로 보강 전송
5. 새 Untitled Markdown 문서에 결과가 열린다(자동 Preview 없음 · 필요 시 VS Code 기본 Preview 사용)
   (제목 예: `# test_Alias 변경 이력`). 연속 조회 시 **이전 Untitled 결과는 그대로 두고**
   새 문서를 추가한다. `.md` 자동 저장 없음(저장은 사용자 결정).
6. `보기 → Output → Source Trace`가 분석 시작 시 자동으로 열리며 진행 로그를 확인할 수 있다

### 3-2. 선택 코드 변경 근거 조회

1. 실제 변경 Commit을 확인하고 싶은 **한 줄 또는 여러 줄**을 드래그로 선택한다
2. **우클릭 → `Source Trace: 선택 코드 변경 근거 조회`** (또는 `F1` → 동일 명령)
3. 선택이 없으면 실행되지 않고 코드를 선택하라는 안내가 표시된다
4. 결과에는 `git blame` 기준 현재 라인 Commit, 실제 Diff 확인 내용, line history,
   직접 연결된 공식 문서(없으면 "확인하지 못했습니다")가 표시된다
5. 함수 전체 이력은 자동으로 포함되지 않으며, 필요하면 `함수 변경 이력 조회`를 별도 실행한다

### 0.5.5에서 개선된 동작 (결과 Untitled, 자동 Preview 제거)

- 조회 결과는 언어 모드 `markdown`의 **새 Untitled** 문서로 연다. 이전 조회 탭은 보존한다.
- **자동 Markdown Preview는 열지 않는다.** 필요 시 VS Code 기본 Preview를 사용자가 직접 연다.
- 디스크 자동 저장은 하지 않는다. 저장은 사용자가 Save As로 결정한다.


### 0.5.3에서 개선된 동작 (함수/선택 코드 조회 분리 · Output 복구)

- 기존 단일 조회 명령을 **`Source Trace: 함수 변경 이력 조회`**와
  **`Source Trace: 선택 코드 변경 근거 조회`**로 분리했다.
- 선택 코드 조회는 키워드 후보 검색 대신 `git blame -L`, blame Commit의 실제 Diff,
  `git log -L` line history를 1차 근거로 사용한다. 키워드 후보 점수로 대표 Commit이나
  PPT를 대체하지 않는다.
- **v0.5.3 / PROJECT_SPEC v2.6**: 선택 코드 파일 식별은 `repo_id + repo_relative_path`.
  Remote-SSH 절대경로와 서버 clone 경로가 달라도 blame 조회가 가능하다.
  remote URL은 `git@` / `ssh://` / `https` / `.git` 차이를 canonical match하고,
  함수 조회에서 확인된 Repo를 재사용한다. Repo 매칭 실패와 서버 연결 실패 Output 안내를 분리한다.
- 함수 Diff는 `DIRECT_BODY_CHANGE` / `FUNCTION_CONTEXT_CHANGE` / `SYMBOL_ONLY` /
  `MESSAGE_ONLY`로 구분한다. `@@` hunk header만으로 함수 범위가 확인되어도 주요 변경 가능하며,
  Symbol만 확인된 경우 `Diff상 … 기능 변경`으로 단정하지 않는다.
- 관련 공식 문서의 관련 함수·소스 목록은 표시 한도 안에서 조회 대상을 우선 포함하고
  초과분은 `외 N개`로 표시한다. Evidence Link 판정은 전체 원본 목록을 사용한다.
- 함수 이력에서 **관련 참고**는 Commit 상세에 반복 표시하지 않고 `## 관련 공식 문서`에만 둔다.
- 핵심 변경 흐름 표는 `Git 근거` / `문서 연결` 열을 분리한다.
- 선택 코드와 직접 연결되지 않은 PPT는 대표 문서로 표시하지 않으며, 없으면
  "이 선택 코드와 직접 연결되는 공식 문서는 확인하지 못했습니다."로 표시한다.
- Continue 연동 제거 과정에서 사라졌던 일반 `Source Trace` Output Channel의
  자동 표시(`show`)와 함수/선택 코드 조회 진행 로그(시작·blame·line history·완료)를 복구했다.
- 함수 변경 성격 분류를 보수화했다. 재승차·기관·시간·기후동행·패널티 관련 변경을
  카드 사용자 유형이나 생년월일 변경으로 오분류하지 않으며, 대상 함수 직접 Diff가 없는
  Commit은 핵심 변경이 아니라 `연관 Git 이력`으로 분리한다.
- 문서 단계 연결 조건을 강화했다. 문서 관련 함수 목록에 대상 함수가 없으면
  "대상 함수가 관련 함수로 확인됩니다" 문구를 생성하지 않고, 대상 파일만 관련되면
  파일 수준 관계로만 표시한다.

### 0.2.0에서 개선된 동작 (Continue 연동 제거)

- Continue Context Provider 연동, 설정 스니펫 생성·복사·설정 파일 열기 기능을 완전히 제거했다.
- Continue 요청 상태 polling, 진행 Output, 관련 설정(`continueProgress`,
  `continueProgressDetail`)을 제거했다.
- Backend 호출 API를 중립 API(`POST /api/trace/report`)로 이전했다. `/api/continue/trace`는
  더 이상 존재하지 않는다.
- Extension 직접 조회 기능(Git/PPT 분석 결과 표시)은 이전과 동일하게 동작한다.
- 한눈에 보기·Output 통계 문구를 `Commit 직접 연결 문서` / `단계 연결 문서` / `관련 참고 문서`로
  명확히 했다(문서 건수 기준임을 표시).
- 이전 버전에서 Continue `config.yaml`에 추가한 Source Trace 항목은 더 이상 사용되지 않으며,
  사용자가 직접 제거할 수 있다. Extension은 해당 파일을 자동으로 읽거나 수정하지 않는다.

### 0.1.16에서 개선된 동작 (Git/문서 독립 축 유지)

- 관련 공식 문서에 **Commit별 연결 유형**을 함께 표시한다 (대표 유형만으로 오해하지 않도록).
- 단계 연결·관련 참고 연결 근거 문구를 보수적·객관적으로 수정했다.

### 0.1.15에서 개선된 동작 (Git/문서 독립 · 연결 유형)

- Git lifecycle과 관련 공식 문서를 별도 축으로 표시한다.
- 문서 연결 유형은 Commit 직접 근거 / 단계 연결 근거 / 관련 참고만 사용한다.
- `공식 적용`·`후속 공식 기능 변경` 등 문서 역할 추정과 270일 휴리스틱을 제거했다.
- Output 통계도 동일 집계를 사용한다.

### 0.1.14에서 개선된 동작 (공식 문서 분류 · footer)

- 최초 확인과 후속 공식 기능 변경 문서 시점이 다르면 `공식 적용`으로 혼동하지 않도록 분리 표시한다.
- 결과 Markdown footer는 `조회:` 한 줄만 유지한다 (`조회 시각:` 중복 제거).

### 0.1.6에서 개선된 동작 (서버 설정 UI + 장비 Quick Pick)

- **명령 팔레트에 4개 명령 추가**
  - `Source Trace: 서버 및 장비 설정` — 서버 주소 입력 → 연결 테스트 → 장비 Quick Pick → 저장
  - `Source Trace: 장비 변경` — 저장된 서버 유지, 장비만 재선택 (서버 URL 입력 없음)
  - `Source Trace: 서버 연결 확인` — 현재 설정 서버로 연결 테스트
  - `Source Trace: 현재 설정 보기` — 서버·장비명·저장소 수 출력
- **`sourceTrace.serverUrl` 신규 설정** (예: `http://서버IP:8010`) — `/api/...` 경로 불필요
- 기존 `sourceTrace.backendUrl`은 자동 인식(하위 호환)
- 서버 주소 입력 시 끝 slash·경로·자격증명 자동 정규화
- 장비명 Quick Pick에 `ID N · Git 저장소 N개 · 변경내역서 등록됨` 표시
- 분석 시 장비 미설정이면 "설정 시작" 버튼으로 바로 설정 마법사 진행
- Output에 `서버: http://...` · `장비: 개집표기 (ID 2)` 표시

### 0.1.5에서 개선된 동작

- **장비 검증**: 분석 전 `GET /api/equipment/{id}`로 장비 존재 여부 확인
- Output에 장비명·장비 ID 표시
- `sourceTrace.equipmentId` **기본값 제거** (null — 미설정 시 분석 차단)
- 장비 미설정 → "Source Trace 장비가 선택되지 않았습니다..." 오류
- 장비 ID 미존재 → "장비 ID N을 서버에서 찾을 수 없습니다..." 오류

### 0.1.4에서 개선된 동작

- `보기 → Output → Source Trace`에 분석 단계별 진행 로그 출력 (요청 준비·전송·응답·결과 생성)
- 백엔드 `lifecycle_summary` 통계를 사용자용 문구로 Output에 표시
- lifecycle Markdown이 이미 `# 함수명 변경 이력` 제목을 포함하면 중복 제목 미추가

### 0.1.3에서 개선된 동작

- selected_symbol 질의 시 **함수 Git lifecycle** 전체 출력 (`## 한눈에 보기` / `## 핵심 변경 흐름` / `## 변경 상세` / `## 공식 근거 문서`)
- `함수 최초 추가`는 부모 커밋 검증 후 **1건만** 인정, 본문 수정은 별도 분류
- Commit별 Diff 기반 설명 (동일 요약 복제 없음), PPT는 **전체 hash** 일치 시 직접 연결
- 로그/주석 Commit은 무관 PPT에 직접 연결하지 않음
- 사용자 Markdown에 `키워드 일치` 등 내부 라벨 미노출
- `sourceTrace.showDebug` 기본 false — 결과 본문에 Extension debug 미표시
- debug는 Output Channel `Source Trace`에만 기록 (showDebug=true면 Markdown 하단 접힌 섹션)

### Evidence Link 요약 (symbol 질의 외)

- 최종 Markdown(요약/시점/이유/소스/근거)이 **symbol-matched Top Evidence Link**와 동일 기준
- `test_Alias` 선택 시 `Alias 확장 적용 건` 등 직접 관련 변경항목 우선 (file_path만 같은 기후동행카드 항목 배제)
- Top Evidence Link에 Commit이 있으면 `### 추가/변경 시점`에도 같은 Commit 표시 (`### 참조 근거`와 일치)

### 0.1.2에서 개선된 동작

- Extension → Backend에 `source_mode`, `detected_symbol` optional 전송
- Backend가 `selected_code="test_Alias"` 단일 식별자를 symbol로 인식
- `final_query_used`가 `card_sc_tm.c test_Alias`가 아니라 **`test_Alias 변경 이력`** 중심
- `file_path`는 scope만 사용 (`file_path_used_as_scope_only=true`)
- `언제 추가` 질문 시 Commit 날짜/메시지/변경내역서 섹션 추가

## 4. Ollama(AI 보조 설명)

- `useOllama` 기본값 **false**
- Ollama는 근거 검색이 아니라 서버 Evidence 요약을 **문장 다듬기**용 보조 기능
- 검색 정확도는 Git/PPT Evidence Link가 결정
- 결과 Markdown에는 `### AI 보조 설명` 문구를 별도로 표시하지 않는다
  (서버 근거 요약이 항상 1차 결과이며, `ai_used`/`ai_answer` API 필드 자체는 유지된다)

## 5. 문제 해결

| 증상 | 조치 |
| --- | --- |
| `분석할 소스 파일을 먼저 열어주세요.` | 소스 파일을 연다 |
| `분석할 함수명 위에 커서를 두거나...` | 함수명 선택 또는 커서를 식별자 위에 둔다 |
| `Backend 서버에 연결할 수 없습니다.` | `sourceTrace.serverUrl` / `server_host.txt` IP 확인 |
| 결과가 파일명만 검색된 것 같음 | Web Evidence Link Top과 비교, 서버 deploy 최신 여부 확인 |
| 서버 로그 `parsed_code_chars=0` | Extension 미설치/구버전 가능 — 최신 `.vsix` 재설치 |
| `선택 코드 변경 근거 조회` 실행 시 안내만 뜨고 끝남 | 코드를 실제로 드래그 선택한 뒤 다시 실행 (공백만 선택하면 동일 안내) |
| line history 확인 제한 문구가 표시됨 | 정상 동작 — 코드 이동/리팩터링/history 단절 가능성. blame Commit 결과는 유효함 |
| 선택 코드 결과에 문서가 없다고 나옴 | 정상 동작 — 직접 연결된 공식 문서가 없으면 있는 그대로 표시함 (무관 문서를 대신 보여주지 않음) |

## 6. 참고

- 상세: `참고_README.md`
- 서버/브라우저 운영: `..\00_읽어보세요.md`
