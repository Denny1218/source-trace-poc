# Source Trace POC 전체 사용 매뉴얼

| 항목 | 내용 |
|------|------|
| 문서명 | AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC — 전체 사용 매뉴얼 |
| 대상 시스템 | Source Trace (Backend + Web UI + IDE Client) |
| 기준 명세 | PROJECT_SPEC **v2.6** |
| 문서 성격 | **제출용 통합 사용 매뉴얼** (설치·등록·조회·문제 해결) |
| 작성일 | 2026-08-27 |

---

## 1. 문서 안내

### 1.1 목적

본 매뉴얼은 Source Trace POC를 **처음 설치·운영하는 담당자**와 **일상적으로 변경 이력을 조회하는 개발자**가  
한 문서로 전체 사용 절차를 따라갈 수 있도록 작성한 **제출용 통합 안내서**입니다.

개별 IDE·서버 폴더의 `00_읽어보세요.md` 등은 세부·버전 참고용이며,  
**제출·인수인계·교육의 기준 문서는 본 매뉴얼**을 사용합니다.

### 1.2 적용 범위

| 포함 | 미포함(참고만) |
|------|----------------|
| 서버 설치·기동 요약 | 소스 빌드·개발 환경 구성 |
| 장비·Git·변경내역서 등록 | Backend API 상세 명세 |
| Web 조회 | Continue 등 비공식 AI 채팅 연동 |
| VS Code / Eclipse / VS2017 / VS2010 Client | Visual Studio **2022** (공식 미지원) |
| 결과 해석·문제 해결 | Ollama 모델 튜닝 |

### 1.3 역할 구분

| 역할 | 주요 작업 |
|------|-----------|
| 서버 관리자 | 서버 PC에 Deploy 설치, 기동/중지, Credential 설정 |
| 운영 담당자 | Web에서 장비·UNC·Git 등록, Git 동기화, 변경내역서 분석 |
| 개발자(사용자) | Web `Source Trace 조회` 또는 IDE Extension으로 함수/선택 코드 이력 조회 |

한 사람이 모든 역할을 수행해도 됩니다. 아래 장 순서를 따르면 됩니다.

---

## 2. 시스템 개요

### 2.1 Source Trace가 하는 일

장비 유지보수 중 “이 함수(또는 이 코드)가 **언제·어떻게** 바뀌었고, **관련 변경내역서는 무엇인지**”를  
Git Commit·Diff와 PPT 변경내역서를 근거로 추적하여 Markdown 결과로 제공합니다.

```text
[개발자 PC: Web 또는 IDE]
        │  함수명 / 선택 코드 / 파일 경로
        ▼
[Source Trace 서버]
  ├─ Git 이력·Diff 수집
  ├─ 변경내역서(PPTX) On-demand 분석·Cache
  └─ Git ↔ 문서 근거 연계
        │
        ▼
  Markdown 결과 (시간순 변경 + 관련 문서)
```

### 2.2 구성 요소

| 구성 | 설명 | 설치 위치 |
|------|------|-----------|
| Backend + Web UI | FastAPI + 정적 Web (포트 **8010**) | **서버 PC** |
| VS Code Extension | 공식 주요 Client (VSIX) | 개발자 PC |
| Eclipse Plug-in | CDT용 Update Site ZIP | 개발자 PC |
| Visual Studio 2017 / 2010 Extension | 세대별 VSIX | 개발자 PC |
| Web Source Trace 조회 | IDE 없는 환경용 fallback Client | 브라우저 |

모든 Client는 **동일 Backend API**를 사용합니다. IDE별로 API가 다르지 않습니다.

### 2.3 전체 사용 흐름 (한눈에)

```text
① 서버 설치·기동                          ← 서버 관리자
② 브라우저로 http://<서버IP>:8010 접속
③ [장비 관리] 장비·UNC·Git 등록            ← 운영 담당자
④ [Git 변경 이력] Git 동기화
⑤ [변경내역서 분석] PPT 분석(권장 1회+)
⑥ [Source Trace 조회] 또는 IDE로 이력 조회  ← 개발자
```

---

## 3. 사전 준비

### 3.1 서버 PC

| 항목 | 요구 |
|------|------|
| OS | Windows (내부망) |
| Python | **3.12** |
| Git CLI | PATH에 `git` 사용 가능 |
| 네트워크 | 변경내역서 **UNC** 공유 접근, (Remote Git 시) Yona 등 접근 |
| Node.js | **불필요** |

### 3.2 운영·개발자 PC

| 항목 | 요구 |
|------|------|
| 서버 접근 | `http://<서버IP>:8010` (방화벽·망 구간 허용) |
| 브라우저 | 최신 Chromium/Edge 권장 |
| IDE (선택) | VS Code / Eclipse CDT / VS2017 / VS2010 |
| Git CLI (IDE 사용 시) | 권장 — 워크스페이스가 Git working tree 안에 있어야 함 |

### 3.3 데이터 준비

1. **변경내역서 폴더**는 반드시 **UNC** (`\\서버\공유\...`)  
   - 운영 PC의 `C:\...` 로컬 경로는 서버가 읽을 수 없음  
   - 대상: `.pptx` (`.ppt` 미지원)
2. **Git 주소** — Yona Remote URL 또는 서버에서 접근 가능한 Local Git 경로
3. 서버 관리자에게 **서버 IP**를 받는다.  
   - 브라우저에 `localhost:8010`을 치면 **본인 PC**를 가리킴 → 반드시 **서버 IP** 사용

---

## 4. 서버 설치 및 기동 (관리자)

제출 패키지 기준 폴더: **`02_서버용/`**

### 4.1 배포물

| 파일 | 용도 |
|------|------|
| `SourceTrace_Server_Deploy.zip` | `deploy/` 트리 (Backend + Web + 스크립트) |
| `00_읽어보세요.md` | 서버 폴더 안내 |
| `01_env_check.bat` ~ `05_stop_server.bat` | 점검·설치·기동·상태·중지 (한글명 bat 동일) |

### 4.2 설치 순서

1. ZIP을 서버 PC에 풀고 **`deploy\`** 를 원하는 위치에 둔다.
2. `deploy\.env.example` → **`.env`** 복사  
   - `DATABASE_PATH` 설정  
   - `YONA_DEFAULT_USERNAME=source_trace` (Remote Git 시 필수)
3. (최초 1회) Yona Credential  
   - `deploy\scripts\setup-yona-credential.bat <host:port> [username]`
4. 순서대로 실행  
   - `01_env_check.bat` (또는 `01_환경점검.bat`)  
   - `02_offline_install.bat` (또는 `02_오프라인설치.bat`)  
   - `03_start_server.bat` (또는 `03_서버시작.bat`)
5. 상태: `04_status_check.bat` / 중지: `05_stop_server.bat`  
   - 재시작은 **중지 후** 다시 `03_start_server.bat`

접속 확인: 서버 PC에서 `http://localhost:8010` → **시스템 상태** 정상

### 4.3 기존 서버에 덮어쓸 때 (중요)

아래는 **절대 덮어쓰지 마세요.** 운영 DB·설정이 날아갑니다.

- `.env`
- `data\*.db`, `data\*.db-wal`, `data\*.db-shm`
- `backend\data\` 아래 DB 관련 파일

제출 ZIP에는 DB를 넣지 않습니다. 코드·프론트만 갱신하고 DB는 서버에 있는 파일을 유지합니다.

---

## 5. Web — 장비·Git·변경내역서 준비 (운영)

제출 패키지: **`03_운영용/`**  
접속: `http://<서버IP>:8010` 또는 `open_browser.bat` (`server_host.txt`에 IP 기입)

### 5.1 화면 메뉴

| 메뉴 | 용도 |
|------|------|
| 시스템 상태 | Backend / DB / Git 연결 확인 |
| 장비 관리 | 장비 · 변경내역서 UNC · Git Repository 등록 |
| Git 변경 이력 | Commit 조회 · **Git 동기화** |
| 변경내역서 분석 | PPT 분석 · Cache |
| Source Trace 조회 | 함수 이력 · 선택 코드 변경 근거 (Web Client) |

### 5.2 장비 등록

1. **장비 관리** → **장비 추가**
2. **장비명** 입력 (예: `휴대용정산기`, `개집표기`)
3. **변경내역서 폴더**에 UNC 붙여넣기 → **경로 확인**  
   - 성공 시 PPTX 개수 등 표시
4. **Git Repository** 추가 (다음 절) → **장비 저장**

### 5.3 Git Repository 등록

1. **+ Repository 추가**
2. 표시용 이름 입력
3. 유형  
   - **Remote**: Yona 등 URL (개발자가 쓰는 주소를 그대로 붙여넣어도 됨)  
   - **Local**: 서버 PC에서 접근 가능한 Git 경로
4. **연결 확인**(Remote) / **경로 확인**(Local) → 목록에 추가 → 장비 **저장**
5. 상태가 **Ready**인지 확인 (`Pending`/`Error`면 URL·권한·Credential 재확인)

한 장비에 저장소가 여러 개면 Repository를 여러 건 등록할 수 있습니다.  
소스가 전혀 다른 장비는 **장비를 분리**하는 것이 안전합니다.

### 5.4 Git 동기화

등록만으로는 Commit이 DB에 쌓이지 않습니다.

1. **Git 변경 이력** 탭
2. 장비(및 필요 시 Repository) 선택
3. **Git 동기화** 실행 → 완료 메시지·Commit 목록 확인
4. 이후 신규 커밋이 생기면 동일하게 재동기화

### 5.5 변경내역서 분석 (권장)

Extension/Web 조회에서 문서 근거가 나오려면, 해당 장비 PPT를 **한 번 이상 분석**해 두는 것이 좋습니다.

1. **변경내역서 분석** 탭 → 장비 선택 → 분석 실행
2. 문서 수·네트워크에 따라 수십 초 이상 소요될 수 있음
3. Cache 목록이 보이면 준비 완료

> Git·UNC만 등록하고 분석을 생략하면, 조회 결과에 변경내역서가 비거나 적을 수 있습니다.

---

## 6. Web — Source Trace 조회 (개발자 / fallback)

IDE를 쓸 수 없는 환경에서는 브라우저 **Source Trace 조회** 탭을 사용합니다.  
결과는 Backend가 만든 Markdown을 그대로 표시합니다.

### 6.1 함수 변경 이력

1. **함수 변경 이력 조회** 선택
2. 장비 선택
3. (권장) Git 기준 **상대 경로**로 소스 파일 경로 입력
4. **함수명** 입력 → **변경 이력 조회**

### 6.2 선택 코드 변경 근거

1. **선택 코드 변경 근거 조회** 선택
2. 장비 · (다중 Repo면) Repository 선택
3. 소스 상대 경로, **시작/종료 Line**(1부터), 선택 코드 입력
4. (선택) 포함 함수명 → **변경 근거 조회**

주의:

- 경로는 절대경로가 아니라 **Repository 상대 경로**
- 선택 코드 조회는 라인 기반(`blame` / line history)이며, 이동·대규모 리팩터링·미커밋 코드에서는 이력이 제한될 수 있음

---

## 7. IDE Client 설치·사용 (개발자)

제출 패키지 설치 파일: **`03_운영용/설치파일/`**

| Client | 설치 파일 | 비고 |
|--------|-----------|------|
| VS Code | `VSCode/source-trace-vscode-0.5.5.vsix` | 공식 주요 Client |
| Eclipse | `Eclipse/source-trace-eclipse-update-site-0.1.1.zip` | **SOURCE.zip 금지** |
| VS 2017 | `VisualStudio/source-trace-visualstudio2017-0.1.3.vsix` | |
| VS 2010 | `VisualStudio/source-trace-visualstudio2010-0.1.3.vsix` | Legacy 호환 |

공통 전제:

- 서버가 기동 중이고 `http://<서버IP>:8010`에 접근 가능
- 조회 파일이 **Git working tree** 안 (`.git` 존재)
- 서버 URL에는 `/api/...`를 붙이지 않음 (예: `http://192.168.10.50:8010`)

공통 조회 명령(이름만 IDE마다 메뉴 위치가 다름):

| 명령 | 용도 |
|------|------|
| 함수 변경 이력 조회 | 함수 전체 변경 흐름 + 관련 문서 |
| 선택 코드 변경 근거 조회 | 선택 줄/블록의 blame·Diff·직접 연결 문서 |

---

### 7.1 VS Code

**설치**

1. Extensions → `...` → **VSIX에서 설치** → `source-trace-vscode-0.5.5.vsix`
2. 또는: `code --install-extension "source-trace-vscode-0.5.5.vsix"`

**설정**

1. `F1` → **`Source Trace: 서버 및 장비 설정`**
2. 서버 주소 입력 → 연결 확인 → **장비명** 선택

| 명령 | 용도 |
|------|------|
| 서버 및 장비 설정 | 최초·서버 변경 |
| 장비 변경 | 같은 서버에서 장비만 변경 |
| 서버 연결 확인 | Health 테스트 |
| 현재 설정 보기 | 서버·장비 확인 |

**조회**

1. 소스 파일 열기 → 함수명/코드 선택  
2. 우클릭 또는 `F1` → **함수 변경 이력 조회** / **선택 코드 변경 근거 조회**  
3. 결과 Markdown 확인 (Output: **보기 → 출력 → Source Trace**)

선택 코드 조회는 **드래그 선택이 필수**입니다. 선택이 없으면 실행되지 않습니다.

---

### 7.2 Eclipse (CDT)

**설치**

1. **Help → Install New Software… → Add… → Archive…**
2. **`source-trace-eclipse-update-site-0.1.1.zip`** 선택  
   - `*-SOURCE.zip`을 고르면 `could not find jar` 오류가 납니다.
3. **ATEC Source Trace** 설치 → Restart

**설정·조회**

- 서버 URL·장비 설정 후, 편집기 컨텍스트 메뉴에서  
  **함수 변경 이력 조회** / **선택 코드 변경 근거 조회** 실행  
- 상세: `03_운영용/Eclipse_Source_Trace_설치_사용_가이드.md`

---

### 7.3 Visual Studio 2017

**설치**

1. VS2017 **완전 종료**
2. `source-trace-visualstudio2017-0.1.3.vsix` 실행 → Install
3. **도구 → 확장 및 업데이트**에서 **ATEC Source Trace** 활성 확인

**설정**

- **도구 → 옵션 → ATEC Source Trace → General** 또는  
  **도구 → ATEC Source Trace → 서버 및 장비 설정...**

**조회**

- C/C++ 편집기 우클릭 → **ATEC Source Trace → …**  
- 결과는 Tool Window에 표시

---

### 7.4 Visual Studio 2010

**설치**

1. VS2010 **완전 종료**
2. `source-trace-visualstudio2010-0.1.3.vsix` 실행
3. **도구 → Extension Manager**에서 **ATEC Source Trace** Enabled 확인

VS2010용과 VS2017용 VSIX는 **서로 호환되지 않습니다.** 세대에 맞는 파일을 사용하세요.  
같은 PC에 둘 다 설치해도 Identity가 달라 충돌하지 않습니다.

**설정·조회**는 VS2017과 유사하며, 메뉴는 **도구 → ATEC Source Trace** / 편집기 우클릭을 사용합니다.  
상세: `03_운영용/VisualStudio2010_Source_Trace_설치_사용_가이드.md`

---

## 8. 조회 결과 읽는 법

사용자 결과의 초점은 다음 세 가지입니다.

1. **언제** 변경되었는지 (시간순 Git 이력)
2. **무엇이** 변경되었는지 (Diff·blame 등)
3. **관련 문서**가 무엇인지 (변경내역서 연결)

대표 구성(버전·Client에 따라 표현은 소폭 다를 수 있음):

| 구역 | 내용 |
|------|------|
| 한눈에 보기 / 요약 | 최초 확인 시점, Git 흐름, 관련 문서 건수 |
| 핵심 변경 흐름 | Commit과 문서 연결 요약 |
| 변경 상세 (Git) | Commit·메시지·Diff 근거 |
| 관련 공식 문서 | Commit과 연결된 PPT 근거 |

선택 코드 조회는 함수 전체 이력이 아니라 **선택 구간의 실제 변경 Commit**에 초점을 둡니다.  
함수 단위 전체 흐름이 필요하면 **함수 변경 이력 조회**를 따로 실행합니다.

AI(Ollama) 보조 설명은 기본 **꺼짐**입니다. 근거 검색은 Git·문서 연결로 동작합니다.

---

## 9. 문제 해결

### 9.1 서버·Web

| 증상 | 확인 |
|------|------|
| 페이지가 안 열림 | 서버 기동, `http://서버IP:8010`, 방화벽 |
| 변경내역서 경로 실패 | UNC 여부, 공유 권한, **서버 PC**에서 경로 접근 |
| Git 연결 실패 | URL/경로, Yona Credential, Repository Ready |
| Commit 목록 비어 있음 | **Git 동기화** 실행 여부 |
| 변경내역서가 조회에 없음 | UNC 등록 + **변경내역서 분석** |

### 9.2 IDE

| 증상 | 확인 |
|------|------|
| 서버 연결 실패 | 서버 URL(포트 포함), 망 접근, Health |
| 장비 목록 없음 | Web **장비 관리**에 장비 등록 여부 |
| 이력 없음 | 해당 장비 Git 등록·동기화 |
| 선택 코드 조회 불가 | 코드를 **드래그 선택**했는지 |
| Eclipse jar 오류 | **SOURCE.zip**이 아닌 **0.1.1 바이너리 ZIP**인지 |
| 경로/Repo 불일치 | 파일이 Git 트리 안인지, 상대 경로가 Repo 기준인지 |

---

## 10. 신규 장비 1대 — 권장 체크리스트

- [ ] 서버 기동, `http://<서버IP>:8010` 접속
- [ ] 시스템 상태 정상
- [ ] 장비 추가(장비명)
- [ ] 변경내역서 UNC → **경로 확인** 성공
- [ ] Git Repository 추가 → 연결/경로 확인 → 저장 → **Ready**
- [ ] Git 변경 이력 → **Git 동기화** → Commit 확인
- [ ] 변경내역서 분석 1회 이상
- [ ] Web Source Trace 조회(함수) 결과 확인
- [ ] (선택) IDE Client 설치 · 서버/장비 설정
- [ ] 함수 변경 이력 조회 결과 확인
- [ ] 선택 코드 변경 근거 조회 결과 확인

---

## 11. 제출 패키지에서 관련 파일 위치

본 매뉴얼이 포함된 제출본 기준 (`SourceTrace_POC_Final_YYYYMMDD`):

| 위치 | 내용 |
|------|------|
| `03_운영용/SourceTrace_POC_전체_사용_매뉴얼.md` | **본 문서 (제출용 통합 매뉴얼)** |
| `02_서버용/` | 서버 Deploy ZIP, 설치 bat, 서버 안내 |
| `03_운영용/` | 운영 스크립트, IDE별 상세 가이드, `설치파일/` |
| `01_소스코드/` | PROJECT_SPEC v2.6, 소스 ZIP |
| `04_대화기록/` | STEP별 개발 대화 아카이브 |

세부 참고(동일 주제의 짧은 안내):

- `02_서버용/00_읽어보세요.md`
- `03_운영용/00_읽어보세요.md`
- `03_운영용/사용자_사용_매뉴얼.md` (Web·VS Code 절차 중심 요약본)
- `03_운영용/*_설치_사용_가이드.md` (IDE별)

---

## 12. 문의·인수 시 전달할 최소 정보

운영 인수인계 시 다음만 전달해도 사용자가 바로 시작할 수 있습니다.

1. 서버 주소: `http://<서버IP>:8010`
2. 본 매뉴얼 파일
3. (개발자용) 해당 IDE 설치 파일 + 장비명

---

**끝.**
)
