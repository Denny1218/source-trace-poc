# Source Trace VS Code Extension

함수/Symbol 전체 Git 변경 이력과, 선택한 라인·코드 블록의 실제 변경 근거를
각각 별도 명령으로 조회하는 VS Code Extension입니다.

## 기능

- **함수 변경 이력 조회** — 최초 확인·이후 Git 이력·관련 문서를 시간순으로 단순 표시
- **선택 코드 변경 근거 조회** — 선택한 한 줄·코드 블록의 실제 `git blame`/Diff hunk/
  line history 기반 변경 Commit 조회 (키워드 후보 검색으로 대체하지 않음).
  Extension은 repo-relative path만 보내고, Backend가 함수 조회와 **동일한
  Repository resolver**로 Repo를 결정합니다. Remote-SSH 절대경로와 서버 clone
  경로가 달라도 됩니다.
- 관련 문서를 별도 영역으로 표시 (사용자 화면에 문서 등급/신뢰도 미표시)
- Source Trace Output에서 분석 진행 상태 확인 (조회 시작 시 자동으로 표시됨)
- Extension 목록/상세에 ATEC Mobility 워드마크형 아이콘 표시

Source Trace VS Code Extension의 직접 조회 결과가 이 프로젝트의 **유일한 공식
조회 경로**입니다. PROJECT_SPEC v2.3 이후 Continue 연동은 지원하지 않습니다.
별도 AI 어시스턴트 연동은 지원하지 않습니다.

## 설치

1. `산출물/운영PC/VSCode-Extension/`의 `.vsix` 파일을 준비합니다.
2. VS Code에서 **Extensions → … → Install from VSIX…** 로 설치합니다.
3. 필요하면 **Developer: Reload Window**로 창을 새로고침합니다.

CLI 예:

```bash
code --install-extension source-trace-vscode-0.5.5.vsix
```

## 결과 표시 (v0.5.5)

조회 결과는 **Untitled Markdown 문서**(언어 모드 `markdown`)로 열리고, 자동 Markdown Preview는 열리지 않습니다. 필요하면 VS Code 기본 Preview를 직접 엽니다. 연속 조회마다 새 Untitled를 추가하고 이전 결과는 보존합니다.

## 최초 설정

명령 팔레트(`F1`)에서 다음을 실행합니다.

**Source Trace: 서버 및 장비 설정**

1. Source Trace 서버 주소 입력 (예: `http://<서버IP>:8010`)
2. 서버 연결 확인
3. 서버에 등록된 장비 목록에서 **장비명** 선택

장비 숫자 ID를 미리 알 필요는 없습니다. 설정 명령이 장비 목록을 조회해 선택합니다.

설정 완료 후 VS Code 재시작 없이 바로 분석에 사용됩니다.

## 사용 방법

용도에 맞는 명령을 선택하세요.

```text
함수 전체 변경 흐름을 볼 때
→ Source Trace: 함수 변경 이력 조회

현재 선택한 한 줄·코드 블록의 실제 변경 Commit을 볼 때
→ Source Trace: 선택 코드 변경 근거 조회
```

### 함수 변경 이력 조회

1. 소스 파일을 엽니다.
2. 함수명 또는 코드 일부를 선택합니다 (선택하지 않으면 커서 위치의 Symbol 사용).
3. 우클릭 → **Source Trace: 함수 변경 이력 조회** (또는 `F1` → 동일 명령)
4. 질문을 입력합니다. (기본: `선택한 코드가 왜 변경됐는지 알려줘`)
5. 새 Untitled Markdown 문서에 결과가 열리고, Untitled로 표시됩니다(자동 Preview 없음).
   이전 조회 Untitled는 보존됩니다.
   (디스크에 `.md`로 자동 저장하지 않으며, 저장 여부는 사용자가 결정합니다.)
6. Output에는 `Git 이력: N건`, `관련 문서: N건`만 최소 집계로 표시됩니다.

### 선택 코드 변경 근거 조회

1. 소스 파일에서 근거를 확인하고 싶은 **한 줄 또는 여러 줄**을 실제로 드래그하여 선택합니다.
2. 우클릭 → **Source Trace: 선택 코드 변경 근거 조회** (또는 `F1` → 동일 명령)
3. 선택이 없으면 명령이 실행되지 않고 코드를 선택하라는 안내가 표시됩니다.
4. Extension은 Git root 기준 상대경로만 준비해 서버로 보냅니다. remote URL 매칭
   실패로 Backend 호출 전에 중단하지 않습니다.
5. 결과에는 `git blame` 기준 현재 라인 Commit, 선택 라인과 겹치는 실제 Diff hunk
   (가능하면 변경 전/후 코드), line history, 관련 문서(없으면 "관련 문서를 찾지
   못했습니다")가 표시됩니다. 전체 파일 Diff는 표시하지 않습니다.
6. 함수 전체 이력은 이 결과에 자동으로 포함되지 않으며, 필요하면 **함수 변경 이력 조회**를
   별도로 실행하세요.

라인 조회는 다음 경우 완전한 이력을 추적하지 못할 수 있습니다 (결과에 제한 사유가 표시됩니다).

- 코드 이동/이름 변경
- Git line tracking 제한

## 결과 구조 (v0.5.3 / PROJECT_SPEC v2.6)

함수 결과 기본 구성:

```text
한눈에 보기 (최초 확인 / 이후 Git 이력 / 관련 문서 / 조회 파일)
변경 이력 (날짜 · Commit · 변경 내용)
변경 상세 (시간순 details — Commit 메시지와 코드에서 확인 분리)
관련 문서 (관련 소스·함수 보기, 연결 Commit 미표시)
전체 참조 근거 (접힘)
```

사용자 화면에 표시하지 않는 항목:

```text
주요 개발 / 보조 변경 / 유지보수 집계
Commit 직접·단계·관련 참고 문서 등급
분석 신뢰도
```

변경 내용 문장은 대상 함수 Diff를 우선하고, 이어서 Commit 메시지의 명시적 사실을
사용합니다. Diff가 없으면 Commit 메시지 수준으로 표시하고
`(대상 함수 Diff 미확인)`을 명시합니다.

조회 파일 경로는 함수 조회·선택 조회 모두 장비 Git Repository 기준
`repo_relative_path`로 통일합니다. Commit short hash는 8자리입니다.

## 설정 항목

| 설정 | 설명 | 기본값 |
|---|---|---|
| `sourceTrace.serverUrl` | Source Trace 서버 주소 | (설정 마법사) |
| `sourceTrace.equipmentId` | 장비 ID | (설정 마법사) |
| `sourceTrace.backendUrl` | (레거시) 전체 API URL. `serverUrl`이 있으면 무시 | (호환용) |
| `sourceTrace.useOllama` | AI 보조 설명 (근거 대체 아님) | `false` |
| `sourceTrace.maxSelectedCodeChars` | 선택 코드 전송 상한 | `4000` |
| `sourceTrace.showDebug` | 결과 하단 debug 접기 표시 | `false` |
| `sourceTrace.diagnosticLogging` | Output 진단 로그 | `false` |

## 문제 해결

- **서버 연결 실패**: 서버 실행·IP·포트·방화벽 확인
- **장비 미설정**: `Source Trace: 서버 및 장비 설정` 재실행
- **선택 코드 조회가 실패**: 현재 파일이 Git Repository 안인지 확인. 함수 조회가
  같은 파일에서 성공한다면 선택 조회도 동일 Backend resolver를 사용합니다
- **선택 코드 조회를 방금 설치/갱신**: `0.5.3` 이상으로 재설치.
  remote URL 매칭은 더 이상 필수 gate가 아닙니다
- **Extension에 `1 message` 경고**: `sourceTrace.analyzeSelection` stale menu
  참조가 없어야 합니다. `0.5.1` 이상이면 해당 경고는 제거되었습니다

Continue 연동은 지원하지 않습니다.
