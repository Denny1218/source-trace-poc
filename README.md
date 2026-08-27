# AI 기반 장비 소스 변경 이력 추적 및 유지보수 지원 POC

장비 Git 소스 변경 이력과 PPT 변경내역서를 연계하여 유지보수 시 변경 배경을 빠르게 확인하는 시스템입니다.

## 현재 구현 단계

**STEP 0** — 프로젝트 기본 실행 환경 구축 (완료)  
**STEP 1** — 장비 관리 기능 (완료)  
**STEP 2** — Git 변경 이력 수집 (완료)  
**STEP 3** — Git 이력 조회 화면 (완료)  
**STEP 4** — 변경 추적 요청 API 및 Trace 흐름 (완료)  
**STEP 5** — Git 기반 PPT 후보 탐색 (완료)  
**STEP 6** — PPT On-demand 분석 및 Cache (완료)

## 요구 사항

- Python 3.10+
- Node.js 18+ (개발 시 Frontend만)
- Git CLI
- Ollama (선택, AI 기능용 — 없어도 시스템 실행 가능)

## 빠른 시작

### 1. 환경 점검

```bat
scripts\check-environment.bat
```

### 2. Backend 의존성 설치

```bat
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Frontend 의존성 설치

```bat
cd frontend
npm install
```

### 4. 개발 서버 실행

```bat
scripts\start-dev.bat
```

- Backend: http://localhost:8010
- Frontend: http://localhost:5173
- Health API: http://localhost:8010/api/health

### 5. 테스트

```bat
scripts\test-backend.bat
```

## 환경 설정

`.env.example`을 `.env`로 복사하여 사용합니다.

```env
APP_HOST=0.0.0.0
APP_PORT=8010
DATABASE_PATH=./data/equipment_change_trace.db
OLLAMA_BASE_URL=http://127.0.0.1:11434
LOG_LEVEL=INFO
```

## 프로젝트 구조

```
equipment-change-trace/
├── backend/          # FastAPI
├── frontend/         # React + TypeScript + Vite
├── scripts/          # 실행/점검 스크립트
├── data/             # SQLite DB
├── logs/             # 애플리케이션 로그
└── tests/            # 테스트 데이터 (STEP 1 이후)
```

## 장비 경로 정책

장비 경로는 Backend 서버에서 접근 가능한 경로를 기준으로 한다.  
서버 로컬 경로를 기본 지원한다.  
UNC 네트워크 경로는 서버 실행 계정의 접근 권한 및 Git 동작 여부에 따라 사용할 수 있으며, 실제 운영 환경에서 별도 검증이 필요하다.

## Git 동기화 (STEP 2)

```http
POST /api/equipment/{id}/sync/git
```

## Git 이력 조회 (STEP 3)

```http
GET /api/equipment/{id}/git/commits?q=CHILD_FARE&page=1&page_size=50
GET /api/git/commits/{commit_id}
```

Commit 상세는 DB `commit_id` 기준 (commit_hash 전역 UNIQUE 아님).

## Trace 검색 (STEP 4)

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

PPT/Ollama/Continue 없이 Git Candidate + Search Context 생성.

## PPT 후보 탐색 (STEP 5)

```http
POST /api/trace/ppt-candidates
```

```json
{
  "equipment_id": 1,
  "keywords": ["어린이", "요금"],
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

파일 메타데이터 기반 후보 탐색 (PPT 내용 Parsing 없음). STEP 4 `search_context` 재사용.

운영 서버는 `scripts\start-server.bat`로 Backend + `frontend/dist` UI를 포트 8010에서 제공합니다.

## PPT On-demand 분석 (STEP 6)

```http
POST /api/trace/ppt-analysis
GET /api/equipment/{id}/ppt-cache
GET /api/ppt-cache/{document_cache_id}
DELETE /api/ppt-cache/{document_cache_id}
```

상위 `PPT_PARSE_LIMIT`(기본 10)개만 Parsing. SHA-256 Hash 기반 Cache.

운영 1차 테스트: `OPERATING_TEST_STEP6.md`  
배포 산출물: `산출물\` (서버PC / 운영PC)

테스트 Repository 준비:

```bat
scripts\setup-test-data.bat
python tests\test-data\setup_ppt_documents.py
```

## 상세 명세

`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.6.md` 참조
