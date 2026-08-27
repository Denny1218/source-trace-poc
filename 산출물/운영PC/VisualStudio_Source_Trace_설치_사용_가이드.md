# Visual Studio Source Trace — 공식 설치 안내

현재 POC **공식 운영 대상**은 다음뿐입니다.

| IDE | 정책 | 설치 파일 |
|---|---|---|
| Visual Studio **2017** | 공식 지원 | `visualstudio/source-trace-visualstudio2017-0.1.3.vsix` |
| Visual Studio **2010** | legacy compatibility | `visualstudio/source-trace-visualstudio2010-0.1.3.vsix` |

- Visual Studio **2022**는 공식 지원·배포 대상이 **아닙니다.**
- MenuProbe 등 진단 VSIX는 운영 설치 대상이 **아닙니다.**

설치·사용:

- VS2017 → `VisualStudio2017_Source_Trace_설치_사용_가이드.md`
- VS2010 → `VisualStudio2010_Source_Trace_설치_사용_가이드.md`

조회 결과의 공식 근거는 IDE와 무관하게 동일 Backend API입니다 (`POST /api/trace/report`, `POST /api/trace/selection`). repository identity는 `equipment_id` + `repo_relative_path`입니다.
