# STEP 6 운영환경 1차 테스트 가이드

변경내역서 분석 기능을 **내부 Windows 서버**에서 검증하기 위한 절차입니다.  
인터넷 연결을 전제로 하지 않습니다. (Ollama 테스트는 포함하지 않음)

---

## 1. 개발 PC에서 준비할 파일

다음 폴더/파일을 USB 또는 내부 공유로 복사합니다.

```text
equipment-change-trace/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── requirements-dev.txt          (선택)
├── frontend/
│   └── dist/                       (개발 PC에서 npm run build 후 생성)
├── scripts/
│   ├── check-environment.bat
│   ├── start-dev.bat               (또는 start-backend-only.bat)
│   └── setup-test-data.bat         (선택, 샘플 데이터)
├── data/                           (빈 폴더, DB 생성용)
├── logs/                           (빈 폴더)
├── .env.example
├── backend/requirements-lock.txt
├── offline_packages/python/          (scripts\prepare-offline-python.bat)
└── AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md
```

**운영 검증용 실제 PPT** (한글 파일명·공백 파일명 포함 권장):

```text
D:\ChangeDoc\<장비명>\
├── 2024\
│   └── 20240315_AG_변경내역.pptx
├── 요금\
│   └── 어린이카드_변경.pptx
└── AG 변경 내역 2024.pptx
```

**운영 검증용 Git Repository** — 서버에서 접근 가능한 로컬 또는 UNC 경로.

---

## 2. 내부 서버 PC로 복사할 폴더

권장 배치 경로 예:

```text
C:\apps\equipment-change-trace\
```

복사 후 `.env.example`을 `.env`로 복사하고 경로를 수정합니다.

```env
APP_HOST=0.0.0.0
APP_PORT=8010
DATABASE_PATH=C:\apps\equipment-change-trace\data\equipment_change_trace.db
PPT_CANDIDATE_LIMIT=30
PPT_PARSE_LIMIT=10
SLIDE_CANDIDATE_LIMIT=50
LOG_LEVEL=INFO
# Yona 서버 전용 Read 계정 (선택). Password는 Git Credential Helper로 처리.
YONA_GIT_USERNAME=source_trace
```

---

## 3. Python Offline Package 설치 방법

### 3-1. 개발 PC (인터넷 가능 시) — Wheel 다운로드

```powershell
cd C:\sourcechangeTrace
scripts\prepare-offline-python.bat
```

또는 수동:

```powershell
mkdir offline_packages\python -Force
pip download -r backend\requirements-lock.txt -d offline_packages\python
```

`requirements-lock.txt`는 **테스트 완료된 고정 버전**(Python 3.12, fastapi 0.139.0, python-pptx 1.0.2 등)입니다.  
`requirements.txt`(>= 범위)만 사용하면 uvicorn/starlette 등이 더 높은 버전으로 내려받아질 수 있으므로 운영 복사 시 lock 파일을 사용하세요.

### 3-2. 운영 서버 — Offline 설치

```powershell
cd C:\apps\equipment-change-trace\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --no-index --find-links=..\offline_packages\python -r requirements-lock.txt
```

설치 확인:

```powershell
python -c "import fastapi, pptx; print('ok')"
```

---

## 4. Backend 실행 방법

```powershell
cd C:\apps\equipment-change-trace\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
```

또는:

```bat
scripts\start-server.bat
```

> **주의:** `start-dev.bat`는 Node(Vite dev server, :5173)를 함께 띄웁니다. 운영 1차 테스트에서는 사용하지 마세요.

Health 확인:

```powershell
Invoke-RestMethod http://localhost:8010/api/health
```

---

## 5. 운영 PC Browser 접속 방법

FastAPI가 `frontend/dist`를 **동일 포트(8010)에서 정적 파일로 제공**합니다.

| 항목 | 주소 |
|---|---|
| **Web UI + API** | `http://<서버IP>:8010` |
| Health API | `http://<서버IP>:8010/api/health` |

Node / Vite Dev Server **불필요**. `scripts\start-server.bat`만 실행하면 됩니다.

### Browser에서 검증 가능한 Web UI

- 시스템 상태 (Dashboard)
- 장비 관리
- Git 변경 이력
- 변경내역서 분석 (PPTX Slide 분석 + Cache 관리)
- Source Trace 조회 (Web Manual Client)

Trace Search / PPT Candidate 전용 화면은 없음 — **PowerShell API** (8~10절) 사용.

### dist 없을 때

`frontend/dist`가 없으면 Backend/API는 정상 기동하고, Root(`/`)는 JSON 상태 메시지를 반환합니다.  
운영 배포 전 개발 PC에서 `scripts\build-frontend.bat` 또는 `cd frontend && npm run build`로 dist를 생성하세요.

동일 PC 테스트:

```text
http://localhost:8010
http://localhost:8010/api/health
```

---

## 6. 실제 장비 등록 방법

### 6-1. 장비 등록 (장비명 + 변경내역서 경로)

**경로 정책 (POC 운영):** `document_path`는 **UNC 네트워크 공유 경로만** 허용합니다.  
Local Drive (`D:\...`) 및 운영 PC Browser 로컬 폴더는 사용하지 않습니다.

- 허용: `\\192.168.155.90\ChangeDocuments\HHD200`
- 비허용: `D:\ChangeDoc\HHD200`, `C:\Users\...`

접근 권한은 **Backend 실행 계정** 기준입니다.

Web UI **장비 관리** 탭:

1. Windows 탐색기에서 UNC 경로를 복사하여 **직접 입력/붙여넣기**
2. **[경로 확인]** — UNC 형식·존재·Directory·Read 접근·재귀 PPTX Count 검증 (10초 이상 소요 시 Loading Panel + 경과 시간 표시)

이번 POC에서는 Web Folder Browser / Windows Native Folder Picker를 제공하지 않습니다.

API 예:

```powershell
$body = @{
  name = "HHD200"
  document_path = "\\192.168.155.90\ChangeDocuments\HHD200"
} | ConvertTo-Json
```

응답 예: `유효한 네트워크 폴더입니다. PPTX N개 (하위 폴더 포함)`

### 6-2. Git Repository 추가 (장비당 1개 이상)

**장비 추가** 화면에서도 Repository를 함께 등록할 수 있습니다 (0개 허용).  
일부 Repository 등록 실패 시 장비는 유지되며 실패 항목만 안내됩니다.

장비 **수정** 화면에서 Repository 추가/수정/삭제하거나 API 사용:

**Remote 예 (Yona URL 그대로 입력):**

```powershell
$body = @{
  name = "hhd200_card"
  source_type = "remote"
  repository_url = "http://ds_yoo@192.168.155.89:9000/13.hhd200/hhd200_card"
} | ConvertTo-Json
```

> URL에 포함된 Username(예: `ds_yoo`)은 편의용 입력 정보입니다. 실제 Git Access(ls-remote/clone/fetch)에는 **항상** `YONA_DEFAULT_USERNAME`을 사용합니다. Repository Identity는 Username을 제거한 `canonical_repository_url` 기준입니다. DB·화면 표시 URL에도 userinfo(개인 ID)를 포함하지 않습니다.

**장비 수정 저장:** 기존 `ready` Repository는 변경 없을 때 Git 명령(ls-remote/clone/fetch)을 실행하지 않습니다. 신규 Repository만 Metadata Create → Prepare(clone) 합니다. `[목록에 추가]`는 Temporary 목록 등록만 수행하며 Git 명령을 실행하지 않습니다.

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/equipment/1/repositories" `
  -ContentType "application/json" -Body $body
```

Remote Repository는 생성 시 **설정 정보만 저장**하고 `status=pending` 으로 응답할 수 있습니다.  
실제 Clone 준비는 별도 prepare 단계에서 수행합니다.

Remote URL 연결 확인 (응답에 `canonical_repository_url` 포함):

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/repositories/validate/remote" `
  -ContentType "application/json" -Body '{"repository_url":"http://ds_yoo@192.168.155.89:9000/13.hhd200/hhd200_card"}'
```

**Yona Default Account (필수):** `.env`에 `YONA_DEFAULT_USERNAME=source_trace` 설정. 미설정 시 Remote 검증/등록이 즉시 실패합니다.

**Credential 설정 (최초 1회):** `scripts\setup-yona-credential.bat <host:port> [username]`  
→ Git Credential Manager (`credential.helper=manager`) → Windows Credential Manager. `credential.helper=store`(평문) 미사용.

**비대화형 Git:** 모든 Git subprocess에 `GIT_TERMINAL_PROMPT=0` 적용. Credential 없으면 즉시 실패 (서버 Console Password Prompt 금지).

**Local 예:**

```powershell
$body = @{
  name = "hhd200_comm"
  source_type = "local"
  local_path = "D:\Source\HHD200\hhd200_comm"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/equipment/1/repositories" `
  -ContentType "application/json" -Body $body
```

Local 경로 확인:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/repositories/validate/local" `
  -ContentType "application/json" -Body '{"local_path":"D:\\Source\\..."}'
```

Remote Repository는 서버 관리 경로 `data/repositories/{equipment_id}/{repository_id}`에 Clone됩니다.  
예시:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/repositories/1/prepare"
```

상태 흐름: `pending -> preparing -> ready | error`

장비 추가 화면에서는:

1. 장비 정보 저장
2. Repository 설정 Row 저장
3. Repository 준비(prepare/clone) 진행 상태 표시

즉 장비 기본 저장과 Remote Clone 완료는 동일 단계가 아닙니다.

---

## 7. Git 동기화 방법

장비 전체 Repository 동기화:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/equipment/1/sync/git"
```

특정 Repository만 동기화:

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/repositories/3/sync"
```

Remote Repository: 최초 Clone 후 `git fetch --all --prune` → `git log`  
Local Repository: 로컬 Working Tree 분석 (자동 `git pull` 없음)

변경 이력 화면에서 **장비 선택 → Repository 선택(전체 또는 개별)** 후 Commit 목록 확인.  
Tab 이동 후 복귀 시 기존 검색 조건/목록/선택 Commit은 유지되며 자동 재조회하지 않습니다.

---

## 8. Trace Search 확인 방법

Web UI 없음 — PowerShell 또는 REST 클라이언트 사용.

```powershell
$body = @{
  equipment_id = 1
  query = "CalcFare 함수가 왜 변경됐어?"
  file_path = "FareCalc.c"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/trace/search" `
  -ContentType "application/json" -Body $body
```

응답의 `search_context.keywords`, `date_from`, `date_to`를 STEP 6 분석에 재사용합니다.

---

## 9. PPT Candidate 확인 방법

Web UI 없음 — PowerShell 또는 REST 클라이언트 사용.

```powershell
$body = @{
  equipment_id = 1
  keywords = @("CalcFare","CHILD_FARE","어린이","요금")
  date_from = "2023-12-16"
  date_to = "2024-06-13"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/trace/ppt-candidates" `
  -ContentType "application/json" -Body $body
```

---

## 10. 변경내역서 분석 확인 방법

```powershell
$body = @{
  equipment_id = 1
  keywords = @("CalcFare","CHILD_FARE","어린이","요금")
  date_from = "2023-12-16"
  date_to = "2024-06-13"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8010/api/trace/ppt-analysis" `
  -ContentType "application/json" -Body $body
```

확인 항목:

- `ppt_candidate_count` ≤ 30
- `processed_documents` ≤ 10 (`PPT_PARSE_LIMIT`)
- `change_item_total` / `change_item_candidates` — 구조화된 변경 항목(변경사항 정의·CSR·As-Is/To-Be·소스/함수명) 포함 여부
- `slide_candidates` — 디버그용 Slide 단위 후보(변경 항목 미인식 시 fallback 확인)
- `fallback_documents_parsed` — 초기 후보에서 결과 부족 시 추가 파싱된 문서 수 (0이면 미발동)

응답 구조(요약):

```jsonc
{
  "change_item_total": 3,
  "change_item_candidates": [
    {
      "change_title": "...",        // 변경사항 정의
      "csr_no": "...",              // 관련 CSR 번호
      "as_is": "...", "to_be": "...",
      "source_functions": [{ "file_path": "X.c", "functions": ["f1", "f2"] }],
      "matched_keywords": ["..."],
      "candidate_score": 75,
      "from_cache_search": false,    // 장비 전체 캐시 검색으로 발견
      "from_fallback": false         // Progressive Fallback으로 발견
    }
  ],
  "slide_candidates": [ /* 디버그용 */ ],
  "fallback_documents_parsed": 0
}
```

Progressive Fallback: 초기(메타데이터 후보 + 캐시) 변경 항목이 `PPT_FALLBACK_RESULT_LIMIT`
미만이면, 메타데이터 점수 순으로 미분석 PPT를 `PPT_FALLBACK_BATCH_SIZE`씩,
최대 `PPT_FALLBACK_MAX_DOCUMENTS`개까지 추가 파싱한다(전량 사전 파싱 회피).

변경 항목 구조는 `change_item_cache`에 `parser_version`과 함께 저장되며,
문서 Hash가 바뀌면 재파싱, 파서 버전이 올라가면 지연(lazy) 재생성된다.

Web UI **변경내역서 분석** 탭은 변경 항목 중심으로 결과를 요약·강조 표시하고,
Slide 후보·Cache·통계는 **디버그 / Cache 보기** 토글 안으로 접힌다.

---

## 11. Cache Hit 확인 방법

동일 PPT를 **내용 변경 없이** 두 번 분석:

```powershell
# 1차 — cache_misses 증가 예상
# 2차 — cache_hits 증가, cache_misses 0 또는 감소 예상
```

로그 (`logs\app.log`)에서:

```text
PPT cache hit
PPT cache miss
```

`modified_at`만 바뀌고 파일 내용이 같으면 **Cache Hit**이어야 합니다 (Hash 기준).

---

## 12. Cache 상세 Slide Text 확인 방법

```powershell
Invoke-RestMethod -Uri "http://localhost:8010/api/equipment/1/ppt-cache"

Invoke-RestMethod -Uri "http://localhost:8010/api/ppt-cache/<document_cache_id>"
```

Web UI에서 Cache 목록 → **상세** 버튼으로 Slide `title` / `content` 확인.

---

## 13. 로그 확인 위치

```text
C:\apps\equipment-change-trace\logs\app.log
```

주요 로그:

- `PPT parse requested`
- `PPT cache hit` / `PPT cache miss`
- `PPT parse started` / `PPT parse completed` / `PPT parse failed`
- `PPT cache updated`
- `Slide candidate search completed`
- `Change item cache stored` / `Change item candidate search`
- `PPT analysis change item merge` / `PPT fallback started` / `PPT fallback completed`

---

## 14. 문제 발생 시 수집할 정보

| 항목 | 예시 |
|---|---|
| OS / Python 버전 | `python --version` |
| `.env` (비밀 제외) | PORT, DATABASE_PATH, PPT_PARSE_LIMIT |
| 장비 등록 정보 | name, document_path, repositories (name, source_type, url/path) |
| API 요청/응답 | ppt-analysis JSON |
| 문제 PPT 경로 | 한글/공백 파일명 포함 |
| `app.log` 해당 시간대 | parse failed, cache hit/miss |
| DB 파일 크기 | `data\equipment_change_trace.db` |
| 손상 PPT 여부 | 다른 PPT는 정상 처리되는지 |

Cache 삭제 후 재분석 테스트:

```powershell
Invoke-RestMethod -Method DELETE -Uri "http://localhost:8010/api/ppt-cache/<document_cache_id>"
```

원본 PPT 파일은 삭제되지 않아야 합니다.

---

## 운영 1차 테스트 체크리스트

- [ ] Python 3.12 + offline_packages/python 오프라인 설치
- [ ] Windows 서버 경로 (로컬/UNC)에서 `document_path` 접근
- [ ] API: 장비 등록 / Git 동기화 / Trace Search
- [ ] API: PPT Candidate / PPT Analysis
- [ ] API: `change_item_candidates` 구조화 필드 반환 (변경사항 정의·CSR·As-Is/To-Be·소스/함수명)
- [ ] 배포계획/별첨 등 비(非)변경 항목 Slide는 변경 항목에서 제외
- [ ] 초기 결과 부족 시 Progressive Fallback 동작 (`fallback_documents_parsed` > 0) 및 상한 준수
- [ ] Web UI: 변경 항목 중심 요약·키워드 강조, Slide/Cache는 디버그 토글 안
- [ ] API: Cache 목록·상세·삭제
- [ ] 동일 ppt-analysis 2회 → Cache Hit
- [ ] 한글 파일명 PPT Parsing
- [ ] 공백 포함 파일명 PPT Parsing
- [ ] PPT 내용 변경 후 Hash 변경 → 재Parsing
- [ ] `processed_documents` ≤ `PPT_PARSE_LIMIT`
- [ ] 이미지 전용 Slide — 빈 content (OCR 미지원)
- [ ] Cache 삭제 후 재생성
- [ ] Browser: `http://<서버IP>:8010` Web UI (장비/Git/변경내역 분석 탭)
