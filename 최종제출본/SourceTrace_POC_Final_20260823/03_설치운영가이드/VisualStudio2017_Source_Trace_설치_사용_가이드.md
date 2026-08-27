# Visual Studio 2017 Source Trace Extension — 설치·사용 가이드 (v0.1.3)

## 지원 범위

| 항목 | 내용 |
|------|------|
| IDE | Microsoft Visual Studio **2017 (15.x)** |
| Edition | Community / Professional / Enterprise |
| 언어 | C/C++ Editor (`.c`, `.cpp`, `.h`, `.hpp` 등) |
| OS | Windows |
| Backend | Source Trace Backend v2.6 (Freeze, 무수정) |

제외: C#/JS/Python, Visual Studio for Mac, Marketplace/인터넷 필수 설치.

## 0.1.3 변경

- Tools 최상위 parent: `IDM_VS_MENU_TOOLS`
- Tools/Context 모두 **Menu → Group → Button** (공식 VSCT: Button Parent는 Group만 허용)
- 메뉴 리소스 버전 갱신 (VSCT Menu→Group→Button)

## 사전 조건

- Visual Studio 2017 (Community/Professional/Enterprise)
- C++ Desktop Development workload (C/C++ 편집기)
- Source Trace Backend 서버 접근 (사내 IP/포트)
- 조회 대상 소스가 **Git working tree** 안에 있을 것 (`.git` 존재)
- Git CLI (`git` in PATH) — **권장**. 없어도 `.git` 상위 탐색 fallback은 동작할 수 있으나, CLI가 더 안정적이다.

Visual Studio 2017 자체 Git 연동(Team Explorer)은 **필요 없다**.

## 오프라인 VSIX 설치

1. **Visual Studio 2017 완전 종료**
2. `source-trace-visualstudio2017-0.1.3.vsix` 실행
3. 설치 대상 Visual Studio **2017** 인스턴스 확인 → **Install**
4. Visual Studio 2017 시작 → **도구 → 확장 및 업데이트**에서 **ATEC Source Trace** 활성 확인
5. **도구 → ATEC Source Trace** 및 C/C++ 우클릭 메뉴 표시 확인

## 제거 / 업데이트

- **도구 → 확장 및 업데이트 → ATEC Source Trace → 사용 안 함/제거**
- 업데이트: 기존 버전 제거 후 새 VSIX 설치

VS2010용 VSIX와 Identity가 다르므로, 같은 PC에 VS2010/VS2017이 함께 있어도 충돌하지 않는다.

## Server URL / 장비 설정

1. **도구 → 옵션 → ATEC Source Trace → General**
2. **Server URL** — Backend origin만 입력 (예: `http://192.168.x.x:8010`)
3. **Equipment ID** — 숫자 ID
4. **Equipment Name** — 표시용 (선택)
5. 저장

또는 메뉴 **도구 → ATEC Source Trace → 서버 및 장비 설정...** 으로 장비 목록 조회·선택.

**Health 확인:** 메뉴 **서버 연결 확인** → `GET /api/health`

사내 IP는 코드에 하드코딩되어 있지 않다. 사용자 설정에만 저장된다.

## 함수 변경 이력 조회

1. Git Repository 안의 C/C++ 파일 열기 (저장된 파일)
2. 함수 내부에 커서 또는 심볼/코드 선택
3. 편집기 우클릭 → **ATEC Source Trace → 함수 변경 이력 조회**
4. **ATEC Source Trace** Tool Window에서 Backend Markdown 결과 확인

## 선택 코드 변경 근거 조회

1. 한 줄 또는 여러 줄 **드래그 선택**
2. 우클릭 → **ATEC Source Trace → 선택 코드 변경 근거 조회**
3. Tool Window에서 blame / diff / 관련 문서 등 Backend 결과 확인

선택이 없으면 서버를 호출하지 않는다.

## UI 정책

- **Toolbar 대형 ATEC 아이콘 없음**
- C/C++ 편집기 우클릭 상위 **ATEC Source Trace** 메뉴에만 **16×16** 아이콘
- 하위 명령은 텍스트 중심
- 상단 **도구 → ATEC Source Trace** 메뉴는 텍스트만

## 기존 업무 프로젝트

Extension 설치·설정만으로 **`.sln` / `.vcxproj` / 소스 파일 / Platform Toolset은 변경되지 않습니다.**
설정은 Visual Studio 사용자 옵션에만 저장됩니다.
프로젝트 conversion/upgrade를 요구하지 않습니다.

## 오류 처리

| 증상 | 확인 |
|------|------|
| Server URL 미설정 | 도구 → 옵션 → ATEC Source Trace |
| 서버 연결 실패 | URL, 네트워크, `GET /api/health` |
| 장비 미선택 | 서버 및 장비 설정에서 장비 선택 |
| C/C++ Editor 아님 | `.c/.cpp/.h` 등 저장된 파일 |
| HTTP 422 | POST UTF-8 JSON body — `type`/`loc`/`msg`를 짧게 표시 |
| Git root 실패 | 파일이 Git repo 안인지, `git` CLI PATH 또는 `.git` 존재 |
| Symbol 미확인 | 커서를 함수명/선언/호출부에 두기 — 추측 symbol 미전송 |
| 선택 없음 | 코드를 드래그한 뒤 선택 코드 조회 |
| Repo ambiguity | Repo 선택 대화상자 → `repo_id_hint` 재전송 |

## 3 IDE 교차검증

동일 equipment / `repo_relative_path` / symbol / 선택 범위로 VS Code, Eclipse, Visual Studio 2017, Visual Studio 2022 결과를 비교한다. Backend Git/PPT 핵심 사실은 동일해야 하고, UI 모양 차이는 허용한다.

## Backend

**수정 없음** — Source Trace Backend v2.6 API contract 그대로 사용.
