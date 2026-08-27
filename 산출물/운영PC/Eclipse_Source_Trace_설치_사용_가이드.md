# Eclipse Source Trace 설치·사용 가이드 (폐쇄망)

대상: 운영PC Eclipse CDT  
Plug-in 버전: **0.1.1**  
Backend: **Source Trace v2.6 API** (서버 수정 없음)  
PROJECT_SPEC: **v2.6** (명세 버전과 Plug-in 버전은 별개)

---

## 0. 가장 중요 (설치 전 필독)

```text
운영PC Eclipse에 PDE는 필요하지 않습니다.
운영PC에 Maven / Tycho / 인터넷 Update Site도 필요하지 않습니다.

설치 시 SOURCE.zip 을 선택하면 안 됩니다.
반드시 바이너리 Update Site ZIP 을 선택하세요.

올바른 파일:
  source-trace-eclipse-update-site-0.1.1.zip

잘못된 파일 (개발/백업용):
  source-trace-eclipse-update-site-0.1.0-SOURCE.zip
  source-trace-eclipse-update-site-0.1.1-SOURCE.zip
```

`could not find jar` 오류가 나면 → **SOURCE.zip을 선택한 경우가 대부분**입니다. 바이너리 ZIP으로 다시 시도하세요.

---

## 1. 사전 조건

- Eclipse IDE for C/C++ Developers (또는 Eclipse + CDT) — **일반 설치면 충분, PDE 불필요**
- Java 17 이상 (Eclipse가 사용하는 JRE)
- 운영PC에서 Source Trace 서버에 HTTP 접근 가능 (`GET /api/health`)
- Git CLI가 PATH에 있으면 권장 (`git rev-parse --show-toplevel`)
- 기존 장비 C/C++ 프로젝트는 그대로 두고, **Plug-in만** 설치

이 Plug-in은 장비 프로젝트의 `.project` / `.cproject` / `.settings` / 소스를 변경하지 않습니다.

---

## 2. 배포 파일 (`산출물/운영PC/eclipse/`)

| 파일 | 설명 | 운영PC 설치 |
|------|------|-------------|
| **`source-trace-eclipse-update-site-0.1.1.zip`** | **바이너리 p2 Update Site** | **필수** |
| `source-trace-eclipse-update-site-0.1.0.zip` | 이전 버전 (대형 아이콘·HTTP 422 이슈) | 사용 비권장 |
| `*-SOURCE.zip` | 소스/백업 | 설치용 아님 |
| `README.md` | ZIP 구분 안내 | — |

---

## 3. 신규 설치 (Archive)

1. Eclipse → **Help → Install New Software…**
2. **Add… → Archive…**
3. **`source-trace-eclipse-update-site-0.1.1.zip`** 선택
4. **ATEC Source Trace** 체크 → Next → Finish → Restart

Unsigned content 경고는 내부 POC 산출물에서 흔합니다. 설치 자체는 가능합니다.

### 3-A. 0.1.0 → 0.1.1 업데이트

1. **Help → Install New Software… → Add → Archive…**  
   → `source-trace-eclipse-update-site-0.1.1.zip`
2. 업데이트가 보이면 설치 후 재시작

업데이트가 안 보이면:

1. **Help → About Eclipse IDE → Installation Details**
2. **ATEC Source Trace** 선택 → **Uninstall** → 재시작
3. 위 Archive 절차로 **0.1.1** 새로 설치

업무 C/C++ 프로젝트를 삭제하거나 다시 import하지 **않습니다**.

---

## 4. 초기 설정

메뉴 **ATEC Source Trace**(상단 텍스트 메뉴, 큰 아이콘 없음):

1. **서버 및 장비 설정**
2. Health 확인 후 장비 선택
3. 또는 **Window → Preferences → ATEC Source Trace**
4. **서버 연결 확인**

저장 위치: Eclipse PreferenceStore (장비 프로젝트 폴더 아님)

---

## 5. 사용

### 함수 변경 이력 조회

1. C/C++ 소스 열기 → 함수명 커서 또는 선택
2. 우클릭 → **ATEC Source Trace**(소형 16×16 아이콘) → **함수 변경 이력 조회**
3. **ATEC Source Trace** View에 Backend Markdown 표시

API: `POST /api/trace/report`

### 선택 코드 변경 근거 조회

1. 코드 선택 후 우클릭 → **선택 코드 변경 근거 조회**
2. blame / Diff / line history Markdown 표시

API: `POST /api/trace/selection`

---

## 6. VS Code 교차검증 (권장)

같은 equipment / `repo_relative_path` / 함수·선택 라인 → Commit·Diff·문서 사실 동일해야 함 (UI 차이는 허용).

---

## 7. Troubleshooting

| 증상 | 확인 |
|------|------|
| `could not find jar` | SOURCE.zip 선택 여부 → 바이너리 `0.1.1.zip` 사용 |
| 상단에 큰 ATEC 아이콘 | **0.1.0** 잔존 → 0.1.1로 업데이트/재설치 |
| HTTP 422 / body missing | **0.1.1** 적용 여부, Server URL, 장비 선택 |
| 서버 연결 실패 | Health, IP/포트 |
| Git root 못 찾음 | clone 안 여부, `git` PATH |
| 관련 문서 없음 | 오류 아님 |

---

## 8. ATEC Mobility 아이콘 정책 (0.1.1+)

- 상단 메뉴: **텍스트만** (아이콘 없음)
- Toolbar: Source Trace 버튼 **없음**
- Editor 우클릭 `ATEC Source Trace` 그룹: **16×16** 소형 아이콘만
- 하위 command: 텍스트만
- 원본 브랜드 대형은 Feature/브랜드 식별용으로만 보관 (`icons/brand/`)

---

## 9. Visual Studio

이번 패키지 범위가 아닙니다.
