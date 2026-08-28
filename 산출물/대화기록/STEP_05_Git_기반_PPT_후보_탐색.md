# STEP 5. Git 기반 PPT 후보 탐색

> **범위**: Cursor 메인 개발 대화 turn **#6 ~ #7** （2턴）
> **이 STEP 요지**: Git 검색 컨텍스트 기반 PPT 후보 탐색

## 읽는 방법

| 구역 | 내용 |
|------|------|
| `◆ 사용자 Prompt` | 사용자 입력 **원문** |
| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |
| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |

---

## 이 Part turn 목록

1. 메인 #6 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트의 기준 명세 파일…
2. 메인 #7 — `AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트의 기준 명세 파일…

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [001]  STEP 5 — Git 기반 PPT 후보 탐색                                            ║
║  메인 turn #6  |  Monday, Jul 6, 2026, 3:00 PM (UTC+9)                         ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트의 기준 명세 파일로 사용해.

작업 시작 전 v2 명세 파일을 처음부터 끝까지 다시 검토하고, 현재 STEP 0~4 구현 상태와 기존 테스트를 확인해.

기존 `PROJECT_SPEC.md` 또는 이전 명세와 내용이 충돌하는 경우 반드시 v2 명세를 우선 적용해.

STEP 0~4의 기존 기능은 유지하고 불필요한 대규모 리팩터링을 하지 마.

이번에는 v2 명세의 STEP 5인 `Git 기반 PPT 후보 탐색`만 구현해.

이번 STEP에서는 PPT 내부 Text Parsing, PPT Cache, Git-PPT Slide 연계, Ollama, Continue 연계 기능을 구현하지 마.

---

1. PPT 후보 탐색 Service 구현

Git Trace Search Context를 입력받아 등록 장비의 document_path에서 관련 가능성이 높은 PPTX 파일 후보를 탐색하는 Service를 구현해.

권장 Service:

backend/app/services/ppt_candidate_service.py

입력 정보:

* equipment_id
* keywords
* date_from
* date_to

가능하면 STEP 4의 trace_service가 생성한 search_context 구조를 그대로 사용할 수 있게 해.

동일한 Keyword 또는 Date Context 생성 로직을 STEP 5에서 다시 구현하지 마.

---

2. PPT 파일 탐색

장비의 equipment.document_path 이하를 재귀 탐색해.

대상:

.pptx

제외:

.ppt
~$*.pptx

확장자 비교는 Windows 환경을 고려하여 대소문자 차이에 영향을 받지 않도록 처리해.

예:

.PPTX
.pptx

가능하면 pathlib.Path를 사용해.

하위 폴더까지 재귀 탐색해야 해.

예:

D:\ChangeDoc\AG
├── 2024
│   ├── 20240315_AG_변경내역.pptx
│   └── 20240501_AG_변경내역.pptx
├── 요금
│   └── 어린이카드_변경.PPTX
└── 기타
└── 화면문구변경.pptx

PPT 내부는 절대 열지 마.

python-pptx를 이번 STEP 후보 탐색에 사용하지 마.

파일명, 폴더명, 파일 메타정보만 사용해.

---

3. PPT Candidate 응답 구조

각 Candidate에는 최소 다음 정보를 포함해.

* file_path
* file_name
* modified_at
* file_size
* candidate_score
* match_reasons

예:

{
"file_path": "D:\ChangeDoc\AG\2024\20240315_AG_변경내역.pptx",
"file_name": "20240315_AG_변경내역.pptx",
"modified_at": "2026-06-20T11:30:00",
"file_size": 1428512,
"candidate_score": 82,
"match_reasons": [
"filename_date",
"filename_keyword"
]
}

match_reasons는 점수의 근거를 확인할 수 있도록 유지해.

단순 총점만 반환하지 마.

---

4. Candidate Score 구현

v2 명세를 기준으로 초기 점수를 구현해.

기본 방향:

파일명 날짜 근접도       35
파일 modified_at 근접도  10
파일명 Keyword          30
폴더명 Keyword          15
장비 Context             10

점수 기준은 코드 여러 곳에 분산시키지 마.

예:

PPT_CANDIDATE_SCORE_CONFIG

또는 동일 목적의 설정 객체를 한 곳에서 관리해.

중요:
modified_at은 실제 변경일이라고 가정하지 마.

우선순위는 다음과 같아.

1. 파일명 또는 폴더명에서 추출한 날짜
2. 파일명 Keyword
3. 폴더명 Keyword
4. modified_at
5. 장비 Context

modified_at은 약한 보조 근거로만 사용해.

---

5. 파일명 및 폴더명 날짜 추출

최소 다음 날짜 형식을 인식해.

20240315
2024-03-15
2024_03_15
2024.03.15

예:

20240315_AG_변경내역.pptx
AG_2024-03-15_변경.pptx
2024_03_15\AG변경내역.pptx
2024.03.15 변경내역.pptx

파일명뿐 아니라 document_path 기준 상대 폴더명에서도 날짜를 찾을 수 있게 해.

예:

D:\ChangeDoc\AG\2024-03-15\변경내역.pptx

날짜 Parse 실패는 오류가 아니다.

잘못된 날짜 예:

20241345

이 경우 Skip하고 후보 탐색은 계속 진행해.

---

6. 날짜 점수 계산

Search Context의 date_from / date_to를 사용해.

파일명 또는 폴더명 날짜가 범위 안에 있는 경우 높은 점수를 부여해.

단순 범위 포함 여부만 볼지, Commit 기준 날짜와의 거리 점수를 사용할지는 현재 Search Context 구조를 확인하고 단순하고 테스트 가능한 방식을 선택해.

현재 Search Context에 정확한 기준 Commit Date가 없고 date_from/date_to만 있다면 범위 중앙 날짜를 기준으로 거리 점수를 계산해도 된다.

다만 이 방식은 근사임을 코드 주석과 STEP 결과 보고에 명시해.

점수 예:

기준 날짜와 가까울수록 35점에 근접
범위 경계에 가까울수록 낮은 점수

범위 밖이면 filename_date 점수 0

과도하게 복잡한 날짜 Ranking 알고리즘은 구현하지 마.

---

7. modified_at 처리

modified_at이 date_from/date_to 범위에 들어간 경우 보조 점수를 부여할 수 있어.

최대 10점을 초과하지 마.

파일명 또는 폴더명 날짜가 존재한다고 해서 modified_at 점수를 반드시 제외할 필요는 없지만, modified_at이 전체 점수를 지배하지 않도록 해.

실제 운영 문서는 복사 또는 정리 과정에서 수정 시간이 변경될 수 있음을 고려해.

---

8. Keyword Matching

Search Context keywords를 파일명과 상대 폴더 경로에 비교해.

예:

keywords:

CalcFare
FareCalc
CHILD_FARE
어린이
요금

파일:

요금\어린이카드_변경.pptx

예상:

filename_keyword 또는 folder_keyword 점수 발생

대소문자 차이는 검색 시 무시해.

예:

CalcFare
calcfare

검색 Match 가능

단, DB 또는 원본 Keyword 자체를 강제로 소문자로 변형하여 저장하는 별도 처리는 필요 없어.

비교 시 normalize해.

---

9. Keyword 부분 일치 정책

C/C++ Symbol과 일반 한글 Keyword의 특성이 다르므로 지나치게 단순한 한 글자 포함 Match를 사용하지 마.

예:

keyword = "A"

모든 PPT가 후보가 되는 문제를 방지해.

STEP 4 keyword_extractor에서 이미 최소 Keyword 기준을 적용하고 있으므로 해당 결과를 우선 신뢰해.

추가 방어가 필요하다면 너무 짧은 Keyword를 Score 대상에서 제외해.

한글:
2자 이상

영문:
2자 또는 3자 이상 정책을 검토

단 다음 Symbol은 보존해야 해.

IO
ID

실제 기존 Keyword Extractor 정책과 충돌하지 않도록 현재 구현을 먼저 확인해.

새로운 Keyword Extraction 로직을 중복 구현하지 마.

---

10. 장비 Context 점수

장비명 또는 장비 관련 식별자가 파일명 또는 상대 폴더 경로에 존재할 경우 장비 Context 점수를 부여해.

예:

equipment.name = AG

파일:

20240315_AG_변경내역.pptx

단, 장비명 `A`, `B`처럼 지나치게 짧은 이름은 단순 substring matching 시 오탐이 매우 많을 수 있다.

장비 Context Matching은 토큰 경계 또는 구분 문자 기준을 고려해.

예:

AG
*AG*
-AG-
\AG\

등을 인식할 수 있는 단순한 방식으로 구현해.

과도한 NLP는 사용하지 마.

---

11. Candidate 선정 정책

모든 PPT를 결과로 반환하지 마.

기본 Candidate 최대 개수:

30

v2 명세 및 환경 설정의 PPT_CANDIDATE_LIMIT를 사용해.

정렬:

candidate_score DESC
→ 파일명 또는 일관된 Secondary Sort

중요:
candidate_score가 0인 PPT는 기본적으로 후보에서 제외해.

날짜와 Keyword 근거가 전혀 없는 PPT를 단순히 Candidate 개수를 채우기 위해 반환하지 마.

Candidate가 0개여도 정상 결과다.

예:

{
"ppt_candidates": []
}

잘못된 PPT를 근거 후보로 만드는 것보다 후보 없음이 더 안전하다.

---

12. Trace API 연계

STEP 4의 POST /api/trace/search 결과에 PPT Candidate를 바로 추가할지, 별도 Debug API를 구현할지는 기존 구조를 검토하여 결정해.

권장:

POST /api/trace/search의 기존 응답 계약을 불필요하게 크게 변경하지 마.

STEP 5 검증용 별도 API를 우선 구현해도 된다.

예:

POST /api/trace/ppt-candidates

요청:

{
"equipment_id": 1,
"keywords": [
"CalcFare",
"FareCalc",
"어린이",
"요금"
],
"date_from": "2023-12-16",
"date_to": "2024-06-13"
}

응답:

{
"equipment_id": 1,
"scanned_files": 120,
"ppt_candidates": [...]
}

단, Service는 이후 STEP 6 Trace 흐름에서 직접 재사용 가능하게 구현해.

API 전용 코드 안에 후보 Ranking 로직을 넣지 마.

---

13. File Metadata 오류 처리

개별 PPT 파일의 stat 정보 조회 실패 때문에 전체 Candidate Search를 실패시키지 마.

예:

권한 오류
파일 삭제 경쟁 상태
일시적 네트워크 경로 오류

해당 파일은 Skip하고 로그를 남겨.

장비 document_path 자체가 존재하지 않거나 접근할 수 없는 경우는 사용자 친화적인 API 오류를 반환해.

Python Stack Trace 전체는 반환하지 마.

---

14. 테스트 데이터

`tests/test-data/device-a/documents` 또는 기존 테스트 생성 구조를 확장해.

PPT 내부 내용은 필요 없어.

빈 .pptx 파일 또는 테스트 목적의 파일 생성 방식을 사용할 수 있으나, 실제 PowerPoint Parsing은 이번 STEP에서 하지 않기 때문에 파일명 및 경로 메타 테스트가 가능하면 된다.

단, 다음 파일 구조를 반드시 테스트해.

2024/
20240315_AG_변경내역.pptx
20240501_AG_변경내역.pptx
20241220_AG_변경내역.pptx

요금/
어린이카드_변경.pptx

기타/
화면문구변경.pptx

날짜형식/
AG_2024-03-15_변경.pptx
AG_2024_03_16_변경.pptx
AG_2024.03.17_변경.pptx

임시/
~$20240315_AG_변경내역.pptx

legacy/
구버전변경내역.ppt

잘못된날짜/
20241345_AG_변경내역.pptx

대문자확장자/
어린이요금변경.PPTX

---

15. Backend 테스트

다음 테스트를 반드시 구현해.

* document_path 하위 폴더 재귀 탐색
* .pptx 검색
* .PPTX 검색
* .ppt 제외
* ~$*.pptx 제외
* 20240315 날짜 추출
* 2024-03-15 날짜 추출
* 2024_03_15 날짜 추출
* 2024.03.15 날짜 추출
* 폴더명 날짜 추출
* 잘못된 날짜 Parse Skip
* 파일명 Keyword Match
* 폴더명 Keyword Match
* 대소문자 Keyword Match
* modified_at 보조 점수
* 장비 Context Match
* candidate_score DESC 정렬
* Candidate Limit
* candidate_score 0 제외
* 후보 없음 정상 응답
* 존재하지 않는 equipment 404
* document_path 없음 또는 접근 불가 오류
* 두 장비 document_path 데이터 분리
* 개별 File stat 실패 시 전체 탐색 계속

중요:
날짜와 Keyword 근거가 없는 무관 PPT가 Candidate Limit을 채우기 위해 결과에 포함되지 않는지 반드시 테스트해.

---

16. Logging

다음 로그를 추가해.

PPT candidate search started

* equipment_id
* keyword_count
* date range 존재 여부

PPT candidate search completed

* scanned_files
* candidate_count

PPT candidate file skipped

* file path
* exception type

전체 Keyword 목록을 반드시 로그에 저장할 필요는 없어.

파일명은 운영상 필요할 경우 로그에 기록 가능하지만 PPT 내부 Content는 아직 읽지 않는다.

---

17. 이번 STEP에서 구현하지 않을 기능

다음 기능은 구현하지 마.

* python-pptx를 이용한 PPT 내용 Parsing
* Slide Text 추출
* document_cache
* slide_cache
* SHA-256 Cache
* Git-PPT Slide 연계
* change_link
* Ollama
* AI 답변
* Continue 연계
* OCR
* Vector DB

이번 STEP은 파일 메타데이터 기반 PPT 후보 탐색까지만 구현해.

---

18. 완료 후 보고

`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`의 Cursor 단계별 완료 보고 형식에 따라 결과를 보고해.

1. 구현한 기능
2. 생성 또는 수정한 파일
3. 핵심 구현 방식
4. 실행 방법
5. 테스트 방법
6. 테스트 결과
7. 현재 제한 사항
8. 다음 STEP 진행 전 확인 사항

추가로 STEP 5에서는 다음 내용을 반드시 보고해.

* PPT 재귀 탐색 방식
* 확장자 및 임시 파일 제외 정책
* 실제 구현한 Candidate Score
* 날짜 형식별 Parse 방식
* 날짜 점수 계산 방식
* modified_at 점수 정책
* Keyword Matching 방식
* 장비 Context Matching 방식
* candidate_score 0 제외 여부
* 후보가 없을 때 처리
* Candidate Limit
* 개별 File 오류 처리
* 테스트 실패 이력과 수정 내용

테스트 실패가 발생했다면 실패 내용을 숨기지 말고 원인, 수정 내용, 재테스트 결과를 함께 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_

### ◇ 진행 과정 요약（도구·짧은 안내만）

- v2 명세 STEP 5와 기존 STEP 0~4 구현을 확인한 뒤 PPT 후보 탐색만 구현합니다.

- 사용 도구: Read×6, Grep, Write×5, StrReplace×18, Shell×3 (총 33회)

---


╔══════════════════════════════════════════════════════════════════════════════╗
║  [002]  STEP 5 — Git 기반 PPT 후보 탐색                                            ║
║  메인 turn #7  |  Monday, Jul 6, 2026, 3:00 PM (UTC+9)                         ║
║  출처: Cursor 메인 개발 대화 (Source Trace POC)                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

### ◆ 사용자 Prompt（원문）

```text
`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`를 프로젝트의 기준 명세 파일로 사용해.

작업 시작 전 v2 명세 파일을 처음부터 끝까지 다시 검토하고, 현재 STEP 0~4 구현 상태와 기존 테스트를 확인해.

기존 `PROJECT_SPEC.md` 또는 이전 명세와 내용이 충돌하는 경우 반드시 v2 명세를 우선 적용해.

STEP 0~4의 기존 기능은 유지하고 불필요한 대규모 리팩터링을 하지 마.

이번에는 v2 명세의 STEP 5인 `Git 기반 PPT 후보 탐색`만 구현해.

이번 STEP에서는 PPT 내부 Text Parsing, PPT Cache, Git-PPT Slide 연계, Ollama, Continue 연계 기능을 구현하지 마.

---

1. PPT 후보 탐색 Service 구현

Git Trace Search Context를 입력받아 등록 장비의 document_path에서 관련 가능성이 높은 PPTX 파일 후보를 탐색하는 Service를 구현해.

권장 Service:

backend/app/services/ppt_candidate_service.py

입력 정보:

* equipment_id
* keywords
* date_from
* date_to

가능하면 STEP 4의 trace_service가 생성한 search_context 구조를 그대로 사용할 수 있게 해.

동일한 Keyword 또는 Date Context 생성 로직을 STEP 5에서 다시 구현하지 마.

---

2. PPT 파일 탐색

장비의 equipment.document_path 이하를 재귀 탐색해.

대상:

.pptx

제외:

.ppt
~$*.pptx

확장자 비교는 Windows 환경을 고려하여 대소문자 차이에 영향을 받지 않도록 처리해.

예:

.PPTX
.pptx

가능하면 pathlib.Path를 사용해.

하위 폴더까지 재귀 탐색해야 해.

예:

D:\ChangeDoc\AG
├── 2024
│   ├── 20240315_AG_변경내역.pptx
│   └── 20240501_AG_변경내역.pptx
├── 요금
│   └── 어린이카드_변경.PPTX
└── 기타
└── 화면문구변경.pptx

PPT 내부는 절대 열지 마.

python-pptx를 이번 STEP 후보 탐색에 사용하지 마.

파일명, 폴더명, 파일 메타정보만 사용해.

---

3. PPT Candidate 응답 구조

각 Candidate에는 최소 다음 정보를 포함해.

* file_path
* file_name
* modified_at
* file_size
* candidate_score
* match_reasons

예:

{
"file_path": "D:\ChangeDoc\AG\2024\20240315_AG_변경내역.pptx",
"file_name": "20240315_AG_변경내역.pptx",
"modified_at": "2026-06-20T11:30:00",
"file_size": 1428512,
"candidate_score": 82,
"match_reasons": [
"filename_date",
"filename_keyword"
]
}

match_reasons는 점수의 근거를 확인할 수 있도록 유지해.

단순 총점만 반환하지 마.

---

4. Candidate Score 구현

v2 명세를 기준으로 초기 점수를 구현해.

기본 방향:

파일명 날짜 근접도       35
파일 modified_at 근접도  10
파일명 Keyword          30
폴더명 Keyword          15
장비 Context             10

점수 기준은 코드 여러 곳에 분산시키지 마.

예:

PPT_CANDIDATE_SCORE_CONFIG

또는 동일 목적의 설정 객체를 한 곳에서 관리해.

중요:
modified_at은 실제 변경일이라고 가정하지 마.

우선순위는 다음과 같아.

1. 파일명 또는 폴더명에서 추출한 날짜
2. 파일명 Keyword
3. 폴더명 Keyword
4. modified_at
5. 장비 Context

modified_at은 약한 보조 근거로만 사용해.

---

5. 파일명 및 폴더명 날짜 추출

최소 다음 날짜 형식을 인식해.

20240315
2024-03-15
2024_03_15
2024.03.15

예:

20240315_AG_변경내역.pptx
AG_2024-03-15_변경.pptx
2024_03_15\AG변경내역.pptx
2024.03.15 변경내역.pptx

파일명뿐 아니라 document_path 기준 상대 폴더명에서도 날짜를 찾을 수 있게 해.

예:

D:\ChangeDoc\AG\2024-03-15\변경내역.pptx

날짜 Parse 실패는 오류가 아니다.

잘못된 날짜 예:

20241345

이 경우 Skip하고 후보 탐색은 계속 진행해.

---

6. 날짜 점수 계산

Search Context의 date_from / date_to를 사용해.

파일명 또는 폴더명 날짜가 범위 안에 있는 경우 높은 점수를 부여해.

단순 범위 포함 여부만 볼지, Commit 기준 날짜와의 거리 점수를 사용할지는 현재 Search Context 구조를 확인하고 단순하고 테스트 가능한 방식을 선택해.

현재 Search Context에 정확한 기준 Commit Date가 없고 date_from/date_to만 있다면 범위 중앙 날짜를 기준으로 거리 점수를 계산해도 된다.

다만 이 방식은 근사임을 코드 주석과 STEP 결과 보고에 명시해.

점수 예:

기준 날짜와 가까울수록 35점에 근접
범위 경계에 가까울수록 낮은 점수

범위 밖이면 filename_date 점수 0

과도하게 복잡한 날짜 Ranking 알고리즘은 구현하지 마.

---

7. modified_at 처리

modified_at이 date_from/date_to 범위에 들어간 경우 보조 점수를 부여할 수 있어.

최대 10점을 초과하지 마.

파일명 또는 폴더명 날짜가 존재한다고 해서 modified_at 점수를 반드시 제외할 필요는 없지만, modified_at이 전체 점수를 지배하지 않도록 해.

실제 운영 문서는 복사 또는 정리 과정에서 수정 시간이 변경될 수 있음을 고려해.

---

8. Keyword Matching

Search Context keywords를 파일명과 상대 폴더 경로에 비교해.

예:

keywords:

CalcFare
FareCalc
CHILD_FARE
어린이
요금

파일:

요금\어린이카드_변경.pptx

예상:

filename_keyword 또는 folder_keyword 점수 발생

대소문자 차이는 검색 시 무시해.

예:

CalcFare
calcfare

검색 Match 가능

단, DB 또는 원본 Keyword 자체를 강제로 소문자로 변형하여 저장하는 별도 처리는 필요 없어.

비교 시 normalize해.

---

9. Keyword 부분 일치 정책

C/C++ Symbol과 일반 한글 Keyword의 특성이 다르므로 지나치게 단순한 한 글자 포함 Match를 사용하지 마.

예:

keyword = "A"

모든 PPT가 후보가 되는 문제를 방지해.

STEP 4 keyword_extractor에서 이미 최소 Keyword 기준을 적용하고 있으므로 해당 결과를 우선 신뢰해.

추가 방어가 필요하다면 너무 짧은 Keyword를 Score 대상에서 제외해.

한글:
2자 이상

영문:
2자 또는 3자 이상 정책을 검토

단 다음 Symbol은 보존해야 해.

IO
ID

실제 기존 Keyword Extractor 정책과 충돌하지 않도록 현재 구현을 먼저 확인해.

새로운 Keyword Extraction 로직을 중복 구현하지 마.

---

10. 장비 Context 점수

장비명 또는 장비 관련 식별자가 파일명 또는 상대 폴더 경로에 존재할 경우 장비 Context 점수를 부여해.

예:

equipment.name = AG

파일:

20240315_AG_변경내역.pptx

단, 장비명 `A`, `B`처럼 지나치게 짧은 이름은 단순 substring matching 시 오탐이 매우 많을 수 있다.

장비 Context Matching은 토큰 경계 또는 구분 문자 기준을 고려해.

예:

AG
*AG*
-AG-
\AG\

등을 인식할 수 있는 단순한 방식으로 구현해.

과도한 NLP는 사용하지 마.

---

11. Candidate 선정 정책

모든 PPT를 결과로 반환하지 마.

기본 Candidate 최대 개수:

30

v2 명세 및 환경 설정의 PPT_CANDIDATE_LIMIT를 사용해.

정렬:

candidate_score DESC
→ 파일명 또는 일관된 Secondary Sort

중요:
candidate_score가 0인 PPT는 기본적으로 후보에서 제외해.

날짜와 Keyword 근거가 전혀 없는 PPT를 단순히 Candidate 개수를 채우기 위해 반환하지 마.

Candidate가 0개여도 정상 결과다.

예:

{
"ppt_candidates": []
}

잘못된 PPT를 근거 후보로 만드는 것보다 후보 없음이 더 안전하다.

---

12. Trace API 연계

STEP 4의 POST /api/trace/search 결과에 PPT Candidate를 바로 추가할지, 별도 Debug API를 구현할지는 기존 구조를 검토하여 결정해.

권장:

POST /api/trace/search의 기존 응답 계약을 불필요하게 크게 변경하지 마.

STEP 5 검증용 별도 API를 우선 구현해도 된다.

예:

POST /api/trace/ppt-candidates

요청:

{
"equipment_id": 1,
"keywords": [
"CalcFare",
"FareCalc",
"어린이",
"요금"
],
"date_from": "2023-12-16",
"date_to": "2024-06-13"
}

응답:

{
"equipment_id": 1,
"scanned_files": 120,
"ppt_candidates": [...]
}

단, Service는 이후 STEP 6 Trace 흐름에서 직접 재사용 가능하게 구현해.

API 전용 코드 안에 후보 Ranking 로직을 넣지 마.

---

13. File Metadata 오류 처리

개별 PPT 파일의 stat 정보 조회 실패 때문에 전체 Candidate Search를 실패시키지 마.

예:

권한 오류
파일 삭제 경쟁 상태
일시적 네트워크 경로 오류

해당 파일은 Skip하고 로그를 남겨.

장비 document_path 자체가 존재하지 않거나 접근할 수 없는 경우는 사용자 친화적인 API 오류를 반환해.

Python Stack Trace 전체는 반환하지 마.

---

14. 테스트 데이터

`tests/test-data/device-a/documents` 또는 기존 테스트 생성 구조를 확장해.

PPT 내부 내용은 필요 없어.

빈 .pptx 파일 또는 테스트 목적의 파일 생성 방식을 사용할 수 있으나, 실제 PowerPoint Parsing은 이번 STEP에서 하지 않기 때문에 파일명 및 경로 메타 테스트가 가능하면 된다.

단, 다음 파일 구조를 반드시 테스트해.

2024/
20240315_AG_변경내역.pptx
20240501_AG_변경내역.pptx
20241220_AG_변경내역.pptx

요금/
어린이카드_변경.pptx

기타/
화면문구변경.pptx

날짜형식/
AG_2024-03-15_변경.pptx
AG_2024_03_16_변경.pptx
AG_2024.03.17_변경.pptx

임시/
~$20240315_AG_변경내역.pptx

legacy/
구버전변경내역.ppt

잘못된날짜/
20241345_AG_변경내역.pptx

대문자확장자/
어린이요금변경.PPTX

---

15. Backend 테스트

다음 테스트를 반드시 구현해.

* document_path 하위 폴더 재귀 탐색
* .pptx 검색
* .PPTX 검색
* .ppt 제외
* ~$*.pptx 제외
* 20240315 날짜 추출
* 2024-03-15 날짜 추출
* 2024_03_15 날짜 추출
* 2024.03.15 날짜 추출
* 폴더명 날짜 추출
* 잘못된 날짜 Parse Skip
* 파일명 Keyword Match
* 폴더명 Keyword Match
* 대소문자 Keyword Match
* modified_at 보조 점수
* 장비 Context Match
* candidate_score DESC 정렬
* Candidate Limit
* candidate_score 0 제외
* 후보 없음 정상 응답
* 존재하지 않는 equipment 404
* document_path 없음 또는 접근 불가 오류
* 두 장비 document_path 데이터 분리
* 개별 File stat 실패 시 전체 탐색 계속

중요:
날짜와 Keyword 근거가 없는 무관 PPT가 Candidate Limit을 채우기 위해 결과에 포함되지 않는지 반드시 테스트해.

---

16. Logging

다음 로그를 추가해.

PPT candidate search started

* equipment_id
* keyword_count
* date range 존재 여부

PPT candidate search completed

* scanned_files
* candidate_count

PPT candidate file skipped

* file path
* exception type

전체 Keyword 목록을 반드시 로그에 저장할 필요는 없어.

파일명은 운영상 필요할 경우 로그에 기록 가능하지만 PPT 내부 Content는 아직 읽지 않는다.

---

17. 이번 STEP에서 구현하지 않을 기능

다음 기능은 구현하지 마.

* python-pptx를 이용한 PPT 내용 Parsing
* Slide Text 추출
* document_cache
* slide_cache
* SHA-256 Cache
* Git-PPT Slide 연계
* change_link
* Ollama
* AI 답변
* Continue 연계
* OCR
* Vector DB

이번 STEP은 파일 메타데이터 기반 PPT 후보 탐색까지만 구현해.

---

18. 완료 후 보고

`AI_기반_장비_소스_변경_이력_추적_및_유지보수_지원_POC_PROJECT_SPEC_v2.md`의 Cursor 단계별 완료 보고 형식에 따라 결과를 보고해.

1. 구현한 기능
2. 생성 또는 수정한 파일
3. 핵심 구현 방식
4. 실행 방법
5. 테스트 방법
6. 테스트 결과
7. 현재 제한 사항
8. 다음 STEP 진행 전 확인 사항

추가로 STEP 5에서는 다음 내용을 반드시 보고해.

* PPT 재귀 탐색 방식
* 확장자 및 임시 파일 제외 정책
* 실제 구현한 Candidate Score
* 날짜 형식별 Parse 방식
* 날짜 점수 계산 방식
* modified_at 점수 정책
* Keyword Matching 방식
* 장비 Context Matching 방식
* candidate_score 0 제외 여부
* 후보가 없을 때 처리
* Candidate Limit
* 개별 File 오류 처리
* 테스트 실패 이력과 수정 내용

테스트 실패가 발생했다면 실패 내용을 숨기지 말고 원인, 수정 내용, 재테스트 결과를 함께 보고해.
```

### ◆ 어시스턴트 응답（원문 · 요약 없음）

# STEP 5 완료 보고 — Git 기반 PPT 후보 탐색

## 1. 구현한 기능

- `equipment.document_path` 하위 **재귀 탐색**으로 `.pptx` 후보 수집 (PPT 내용 미파싱)
- STEP 4 `search_context`와 동일한 입력(`keywords`, `date_from`, `date_to`) 기반 **점수·순위**
- `POST /api/trace/ppt-candidates` 검증용 API
- `search_ppt_candidates_from_context()` — STEP 6 Trace 연계용 Service 진입점
- 파일 메타데이터(`stat`) 기반 `modified_at`, `file_size` 수집
- `match_reasons`로 점수 근거 노출
- 로깅: search started / completed / file skipped

## 2. 생성 또는 수정한 파일

| 파일 | 역할 |
|---|---|
| `backend/app/core/ppt_candidate_config.py` | 점수·Limit 설정 |
| `backend/app/services/ppt_date_parser.py` | 경로 날짜 추출 |
| `backend/app/services/ppt_candidate_service.py` | 탐색·점수·선정 |
| `backend/app/schemas/trace.py` | `PptCandidateRequest/Response/Item` |
| `backend/app/api/trace.py` | `POST /api/trace/ppt-candidates` |
| `tests/test-data/setup_ppt_documents.py` | PPT 테스트 문서 트리 |
| `backend/tests/test_ppt_candidate.py` | 22개 테스트 |
| `backend/tests/conftest.py` | `ppt_documents_ready` fixture |
| `scripts/setup-test-data.bat` | PPT 테스트 데이터 생성 추가 |
| `README.md`, `TEST_PLAN.md` | STEP 5 문서 반영 |

## 3. 핵심 구현 방식

**Service 계층 분리** — API는 `search_ppt_candidates()`만 호출, Ranking 로직은 Service에 집중.

**STEP 4 재사용** — Keyword/Date Context를 STEP 5에서 재생성하지 않음. `search_ppt_candidates_from_context(SearchContext)` 제공.

---

### STEP 5 설계 정책 상세

| 항목 | 정책 |
|---|---|
| **PPT 재귀 탐색** | `pathlib.Path.rglob("*")` + `is_file()` |
| **확장자/임시 파일 제외** | 포함: `.pptx`(대소문자 무시). 제외: `.ppt`, `~$` 접두사 |
| **Candidate Score** | filename_date 35, modified_at 10, filename_keyword 30, folder_keyword 15, equipment_context 10 (`PPT_CANDIDATE_SCORE_CONFIG`) |
| **날짜 Parse** | `20240315`, `2024-03-15`, `2024_03_15`, `2024.03.15` — 파일명·폴더명. `20241345` 등 무효 날짜는 Skip |
| **날짜 점수** | `date_from`~`date_to` **범위 중앙일** 기준 거리 비율 (근사). 범위 밖이면 0 |
| **modified_at** | 범위 내일 때 최대 10점 보조. 파일명/폴더명 날짜보다 우선순위 낮음 |
| **Keyword** | 비교 시 소문자 normalize. 한글 2자+, 영문 3자+(대문자 Symbol 2자+, `IO`/`ID`/`AG` 보존) |
| **장비 Context** | 2자 미만 장비명 제외. 구분자(`\`, `_`, `-`, `.`) 경계 또는 이름 포함 |
| **score 0 제외** | `candidate_score == 0` 제외 |
| **Primary gate** | `filename_date`/`folder_date`/`filename_keyword`/`folder_keyword` 중 **하나 이상** 필수 — equipment_context·modified_at만으로는 후보 불가 |
| **후보 없음** | `{"ppt_candidates": []}` 정상 |
| **Candidate Limit** | 기본 30 (`PPT_CANDIDATE_LIMIT` 환경변수) |
| **개별 파일 오류** | `is_file()`/`stat()` 실패 시 Skip + warning 로그, 전체 탐색 계속 |
| **document_path 오류** | 없음/비폴더/읽기불가 → 400 (스택트레이스 미노출) |

## 4. 실행 방법

```bat
scripts\start-dev.bat
```

```http
POST http://localhost:8010/api/trace/ppt-candidates
Content-Type: application/json

{
  "equipment_id": 1,
  "keywords": ["어린이", "요금", "AG"],
  "date_from": "2024-03-01",
  "date_to": "2024-04-30"
}
```

테스트 데이터 준비:

```bat
scripts\setup-test-data.bat
```

## 5. 테스트 방법

```bat
cd backend
python -m pytest tests/test_ppt_candidate.py -v
python -m pytest tests/ -q
```

## 6. 테스트 결과

| 구분 | 결과 |
|---|---|
| `test_ppt_candidate.py` | **22 passed** |
| 전체 `pytest tests/` | **89 passed** |

## 7. 현재 제한 사항

- PPT **내부 텍스트** 미분석 (python-pptx 미사용)
- 날짜 점수는 정확한 Commit Date가 아닌 **검색 범위 중앙일 근사**
- Keyword는 **부분 문자열** 매칭 (STEP 4 extractor 결과 신뢰 + 최소 길이 방어)
- `POST /api/trace/search` 응답에는 PPT 후보 **미포함** (별도 API)
- Cache, Slide 연계, Ollama, Continue **미구현**

## 8. 다음 STEP 진행 전 확인 사항

- STEP 6: STEP 5 상위 후보만 **On-demand PPT Parsing** + `document_cache`/`slide_cache`
- Trace 전체 흐름에서 `search_ppt_candidates_from_context()` 연계 여부 결정
- 운영 환경 `document_path`(로컬/UNC) 접근 권한 검증

---

## 테스트 실패 이력

| # | 실패 | 원인 | 수정 | 재테스트 |
|---|---|---|---|---|
| 1 | `test_ppt_candidate_empty_ok` | `equipment_context`만으로 무관 PPT 후보 포함 | primary_reasons 게이트 추가 | PASS |
| 2 | `test_individual_stat_failure_continues` | `is_file()` OSError 시 탐색 중단 | `is_file()` try/except | PASS |

---

STEP 0~4 기능은 유지되었고, 이번 STEP 범위(PPT 메타데이터 기반 후보 탐색) 구현이 완료되었습니다. STEP 6(PPT On-demand 분석 및 Cache) 진행할까요?

### ◇ 진행 과정 요약（도구·짧은 안내만）

- TEST_PLAN.md에 STEP 5 섹션이 중복되어 있어 정리 중입니다.

- 사용 도구: Shell, StrReplace×7, Read×11, Grep×3, Write (총 23회)

---
