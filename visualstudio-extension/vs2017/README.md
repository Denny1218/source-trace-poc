# ATEC Source Trace — Microsoft Visual Studio 2017 Extension (Adapter)



Visual Studio **2017 (15.x)** C/C++ Editor용 Source Trace Backend v2.6 Adapter입니다.



## 기능



- 함수 변경 이력 조회 → `POST /api/trace/report`

- 선택 코드 변경 근거 조회 → `POST /api/trace/selection`

- Server URL / 장비 설정 (Visual Studio 사용자 설정)

- 결과: `ATEC Source Trace` Tool Window (Backend `content` Markdown)



## 빌드 (개발 PC)



```powershell

cd visualstudio-extension\vs2017

.\build-vsix.ps1

```



요구: .NET SDK(로컬 `.tools/dotnet` 사용 가능) + NuGet restore (`Microsoft.VisualStudio.SDK` 15.0.1).



빌드 시 `VSPackage.resx` + `MergeWithCTO=true`로 command table이 managed resource에 병합되는지 자동 검증한다.



## 산출물



- `vs2017/out/source-trace-visualstudio2017-0.1.3.vsix`

- `산출물/운영PC/visualstudio/source-trace-visualstudio2017-0.1.3.vsix`



## 설치 (운영 PC)



Visual Studio 2017 종료 → VSIX 더블클릭 → 2017 인스턴스 선택 → Install → **도구 → ATEC Source Trace** 및 C/C++ 우클릭 메뉴 확인.



상세: `산출물/운영PC/VisualStudio2017_Source_Trace_설치_사용_가이드.md`



## Backend



**수정 없음** — 기존 Source Trace Backend v2.6 API contract 그대로 사용.

