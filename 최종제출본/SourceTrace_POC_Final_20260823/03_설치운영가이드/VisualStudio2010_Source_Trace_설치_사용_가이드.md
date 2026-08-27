# Visual Studio 2010 Source Trace Extension — 설치·사용·테스트 가이드 (v0.1.3)

## 지원 범위

| 항목 | 내용 |
|------|------|
| IDE | Microsoft Visual Studio **2010 (10.x)** |
| Edition | Professional / Premium / Ultimate |
| 언어 | C/C++ Editor (`.c`, `.cpp`, `.h`, `.hpp` 등) |
| OS | Windows |
| .NET | .NET Framework **4.0** (VS2010 런타임) |
| Backend | Source Trace Backend v2.6 (Freeze, 무수정) |
| VSIX | **스키마 1.0** (`Version="1.0.0"`) — VS2017 VSIX와 **호환되지 않음**. VS2022는 공식 배포 대상 아님 |

제외: C#/JS/Python Editor, Visual Studio for Mac, Marketplace/인터넷 필수 설치, Express Edition.

Visual Studio **2017**은 `source-trace-visualstudio2017-0.1.3.vsix`를 사용한다.

## 0.1.3 변경

- Tools 최상위 parent: `IDG_VS_MM_TOOLSADDINS` → `IDM_VS_MENU_TOOLS`
- Tools/Context 모두 **Menu → Group → Button** (Button → Menu 직접 parent 제거)
- `ProvideMenuResource("Menus.ctmenu", 2)` / pkgdef `, Menus.ctmenu, 2`

## 사전 조건

- Visual Studio 2010 (Pro/Premium/Ultimate)
- C++ native 개발 가능 환경 (C/C++ 편집기)
- Source Trace Backend 서버 접근 (사내 IP/포트)
- 조회 대상 소스가 **Git working tree** 안에 있을 것 (`.git` 존재)
- Git CLI (`git` in PATH) — **권장**. `git rev-parse`로 repo root를 안정적으로 찾는다. CLI가 없어도 `.git` 상위 탐색 fallback은 동작할 수 있다.

Visual Studio 2010 자체 Git/TFS 연동은 **필요 없다**. Extension은 파일 경로와 `.git`만 사용한다.

## 오프라인 VSIX 설치

1. **Visual Studio 2010 완전 종료** (모든 devenv.exe 종료)
2. `source-trace-visualstudio2010-0.1.3.vsix` 더블클릭
3. VSIX Installer에서 Visual Studio **2010** 대상 확인 → **Install**
4. Visual Studio 2010 시작
5. **도구 → Extension Manager** → **Installed Extensions**에서 **ATEC Source Trace**가 **Enabled**인지 확인

VS2010에는 VS2017+의 "확장 및 업데이트" 메뉴가 없다. **Extension Manager**를 사용한다.

### 수동 확인 (설치 실패 시)

확장 폴더:

```text
%LocalAppData%\Microsoft\VisualStudio\10.0\Extensions\
```

해당 폴더 아래에 `Atec.SourceTrace.VisualStudio2010.*` 항목이 있고, Extension Manager에서 **Enable** 되어 있어야 한다.

## 제거 / 업데이트

- **도구 → Extension Manager → ATEC Source Trace → Disable / Uninstall**
- 업데이트: 기존 버전 제거(또는 Disable) 후 새 VSIX 설치

Extension Identity는 VS2017(`e4b17c90`)와 다르므로 (`d0c19e45`), 같은 PC에 여러 Visual Studio 세대가 있어도 충돌하지 않는다.

## Server URL / 장비 설정

1. **도구 → 옵션 → ATEC Source Trace → General**
2. **Server URL** — Backend origin만 (예: `http://192.168.x.x:8010`)
3. **장비** — 읽기 전용 표시 (`(선택 안 됨)` 또는 `장비명 (ID: n)`)
4. **확인**으로 저장

장비 선택은 Options가 아니라 **도구 → ATEC Source Trace → 서버 및 장비 설정...** 에서 목록으로 선택한다.
(Server URL을 먼저 입력해야 한다.)

**Health 확인:** **도구 → ATEC Source Trace → 서버 연결 확인** → `GET /api/health`

사내 IP는 코드에 하드코딩되어 있지 않다. Visual Studio 사용자 설정에만 저장된다.

## 함수 변경 이력 조회

1. Git Repository 안의 C/C++ **저장된** 파일 열기
2. 함수 내부에 커서를 두거나, 함수명/호출부/선언부를 선택
3. 편집기 우클릭 → **ATEC Source Trace → 함수 변경 이력 조회**
4. **ATEC Source Trace** Tool Window에서 Backend Markdown 결과 확인

## 선택 코드 변경 근거 조회

1. 한 줄 또는 여러 줄 **드래그 선택**
2. 우클릭 → **ATEC Source Trace → 선택 코드 변경 근거 조회**
3. Tool Window에서 blame / diff / 관련 문서 등 Backend 결과 확인

선택이 없으면 서버를 호출하지 않는다.

## UI 정책

- **Toolbar 대형 ATEC 아이콘 없음**
- C/C++ 편집기 우클릭 **ATEC Source Trace** 메뉴에만 **16×16** 아이콘
- 하위 명령은 텍스트 중심
- 상단 **도구 → ATEC Source Trace** 메뉴는 텍스트만

## 기존 업무 프로젝트

Extension 설치·설정만으로 **`.sln` / `.vcxproj` / 소스 / Platform Toolset은 변경되지 않습니다.**
설정은 Visual Studio 사용자 옵션에만 저장됩니다.
프로젝트 conversion/upgrade를 요구하지 않습니다.

---

## 상세 테스트 절차 (운영 PC)

아래는 VS2010 PC에서 Extension을 검증할 때 권장하는 순서이다. Backend가 이미 기동 중이어야 한다.

### 0. 준비

| 확인 항목 | 방법 |
|-----------|------|
| Backend 기동 | 브라우저 또는 `api_test.ps1`로 `GET /api/health` |
| Git repo | 테스트용 C/C++ 파일이 `.git` 아래에 있음 |
| Git CLI | 명령 프롬프트에서 `git --version` (권장) |
| VS2010 | Pro/Premium/Ultimate, C++ 파일 편집 가능 |

### 1. 설치 스모크

1. VS2010 종료
2. `source-trace-visualstudio2010-0.1.3.vsix` 설치
3. VS2010 시작 → Extension Manager에서 **Enabled**
4. **도구** 메뉴에 **ATEC Source Trace** 하위 항목이 보이는지 확인

### 2. 설정·Health

1. **도구 → 옵션 → ATEC Source Trace** 열기
2. Server URL 입력 → Equipment ID/Name 설정 → 확인
3. **도구 → ATEC Source Trace → 서버 연결 확인**
4. 성공 메시지 또는 Tool Window/대화상자에 health OK 표시 확인

실패 시: URL, 방화벽, Backend 로그, `GET /api/health` 직접 호출.

### 3. 장비·Repo

1. **도구 → ATEC Source Trace → 서버 및 장비 설정...**
2. 장비 목록이 로드되는지 확인
3. 장비 선택 후 저장

### 4. 함수 변경 이력 (Report)

1. Git repo의 `.cpp` 또는 `.h` 파일 열기 (**저장** 상태)
2. 알려진 함수 내부에 커서
3. 우클릭 → **ATEC Source Trace → 함수 변경 이력 조회**
4. **ATEC Source Trace** Tool Window에 Markdown/HTML 형태 Backend `content` 표시 확인
5. VS Code 또는 Eclipse에서 **동일 symbol / repo_relative_path / equipment**로 조회해 핵심 사실(날짜, commit, slide 등)이 일치하는지 비교

### 5. 선택 코드 (Selection)

1. 동일 파일에서 2~10줄 드래그 선택
2. 우클릭 → **ATEC Source Trace → 선택 코드 변경 근거 조회**
3. Tool Window에 selection 결과 표시 확인
4. 선택 없이 메뉴 실행 시 — 서버 호출 없음(또는 안내) 확인

### 6. Tool Window

1. **보기 → 기타 창** (또는 메뉴에서 Tool Window 표시) → **ATEC Source Trace**
2. 창이 열리고 이전 조회 결과가 유지/갱신되는지 확인

### 7. 컨텍스트 메뉴·아이콘

1. C/C++ 편집기에서만 **ATEC Source Trace** 우클릭 메뉴 노출 확인
2. `.txt` 등 비 C/C++ 또는 솔루션 탐색기에서는 메뉴 없음(또는 비활성) 확인
3. 메뉴 옆 **16×16** 아이콘만 — 툴바 대형 아이콘 없음

### 8. Git edge case

| 시나리오 | 기대 |
|----------|------|
| `.git` 밖 파일 | repo root 오류 또는 조회 실패 안내 |
| `git` CLI 없음 | `.git` 탐색 fallback으로 동작 가능(환경별 확인) |
| 동일 equipment에 repo 여러 개 | Repo 선택 대화상자 → 재전송 |

### 9. 오류 표시

HTTP 422 등 Backend 오류 시 Extension이 `type`/`loc`/`msg`를 **짧게** 표시하는지 확인 (전체 JSON 덤프 금지).

---

## 오류 처리

| 증상 | 확인 |
|------|------|
| VSIX 설치 거부 | VS2010 Pro/Premium/Ultimate인지, VS2017/2022 VSIX를 잘못 쓰지 않았는지 |
| Extension Disabled | Extension Manager에서 Enable |
| Server URL 미설정 | 도구 → 옵션 → ATEC Source Trace |
| 서버 연결 실패 | URL, 네트워크, `GET /api/health` |
| 장비 미선택 | 서버 및 장비 설정 |
| C/C++ Editor 아님 | `.c/.cpp/.h` 등 **저장된** 파일 |
| HTTP 422 | POST UTF-8 JSON body — Extension은 ContentLength 고정 |
| Git root 실패 | `.git` 존재, `git` PATH |
| Symbol 미확인 | 함수명/선언/호출부에 커서 — 추측 symbol 미전송 |
| 선택 없음 | 코드 드래그 후 selection 조회 |
| Repo ambiguity | Repo 선택 대화상자 |

## 3 IDE 교차검증

동일 equipment / `repo_relative_path` / symbol / 선택 범위로 **VS Code**, **Eclipse**, **Visual Studio 2010**, (가능하면 2017) 결과를 비교한다. Backend Git/PPT 핵심 사실은 동일해야 하고, UI 모양 차이는 허용한다.

## 개발 PC 빌드 (참고)

```powershell
cd visualstudio-extension\vs2010
.\build-vsix.ps1
```

- 21개 VS2010 단위 테스트 → Release net40 빌드 → VSIX 1.0 패키징 (VSSDK MergeWithCTO managed resource)
- 산출물: `산출물/운영PC/visualstudio/source-trace-visualstudio2010-0.1.3.vsix`

## Backend

**수정 없음** — Source Trace Backend v2.6 API contract 그대로 사용.
