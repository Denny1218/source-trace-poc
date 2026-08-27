# POC Release Freeze (2026-08-23)

## 판정

**Source Trace POC Release Freeze: 가능**  
**Final Submission Package: READY**  
**Server Package: INCLUDED**

기능/API/지원범위 변경 없음. PROJECT_SPEC 새 버전 없음. v2.6은 이번 MIME 수정으로 수정하지 않음.

## MIME blocker (실제 HTTP)

로컬 Backend 기동 (`127.0.0.1:8010`) 후 `GET /` HTML이 참조하는 Vite JS를 요청했다.

수정 전:

- HTTP 200
- `Content-Type: text/plain; charset=utf-8`

원인: Windows/Python 3.14 `mimetypes`가 `.js`를 `text/plain`으로 매핑. TestClient만이 아니라 **실제 HTTP와 동일**.

최소 수정: `backend/app/core/frontend_static.py`에서 `.js`/`.mjs`를 `text/javascript`로 등록.

수정 후 실제 HTTP:

- HTTP 200
- `Content-Type: text/javascript; charset=utf-8`

API/DB/resolver/Markdown/Frontend 기능/IDE Client 변경 없음.

## Backend pytest (수정 후 재실행)

```
517 passed, 1 warning in 526.79s
```

Python 3.14. 경고: Starlette TestClient + httpx deprecation (실패 아님).

## 공식 Client 버전

| Client | 버전 | 파일 |
|---|---|---|
| VS Code | 0.5.4 | source-trace-vscode-0.5.4.vsix |
| Eclipse | 0.1.1 | source-trace-eclipse-update-site-0.1.1.zip |
| VS2010 | 0.1.3 | source-trace-visualstudio2010-0.1.3.vsix |
| VS2017 | 0.1.3 | source-trace-visualstudio2017-0.1.3.vsix |
| Web Manual Client | 현재 HEAD | 서버 Frontend |
| Backend | v2.6 API | MIME 등록만 추가 |

Continue / VS2022: 공식 범위 제외.

## 설치 파일 SHA256

제출본 복사본 기준으로 재계산. 기존 Freeze 값과 **일치**.

| 파일 | bytes | SHA256 |
|---|---|---|
| source-trace-visualstudio2010-0.1.3.vsix | 36335 | 20A6D4A81528C8A96538CB1FCE21035147CCCBF657B813387F0CECCF4DDA9851 |
| source-trace-visualstudio2017-0.1.3.vsix | 51588 | 80F89D389EA7B8A07D6E5C2C483FD7172E75CF6FC3DD5AE079B7D513AF6ACBCA |
| source-trace-vscode-0.5.4.vsix | 57444 | 41B729D56201DAE43FC43C86DA11B35966FE0923E0A8528288264051146AE350 |
| source-trace-eclipse-update-site-0.1.1.zip | 90442 | 5E881E56269507E6484E80242B877FF3E95550885860D173243B9387EB7D423A |

## 서버 실행본

포함. 기준: Release Freeze HEAD (`frontend_static.py` MIME 등록 포함).  
생성: 기존 `python scripts/package-deploy.py` 1회.

- `산출물/서버PC/deploy/backend/app/core/frontend_static.py`에 `text/javascript` 등록 확인
- 제출 파일: `02_설치및실행파일/Server/SourceTrace_Server_Deploy.zip` (압축 시 최상위 `deploy/`)

Deploy smoke (재생성 deploy 트리 + 이 PC Python으로 uvicorn, 운영 장비 데이터 없음):

| 항목 | 결과 |
|---|---|
| 서버 기동 | PASS |
| `GET /api/health` | PASS 200 `application/json` |
| `GET /` | PASS 200 `text/html` |
| Vite JS 200 | PASS |
| Vite JS Content-Type | PASS `text/javascript; charset=utf-8` |
| ATEC logo `/static/brand/logo_web_header.png` | PASS 200 `image/png` |
| favicon `/favicon.ico` | PASS 200 `image/x-icon` |
| 서버 중지 | PASS |
| 실제 장비/Git/PPT 조회 | 미실행(운영환경 필요) |

## 미검증

운영 장비/Git/PPT E2E, 원격 운영 서버 smoke. 과거 STEP 10 기록은 변경하지 않음.
