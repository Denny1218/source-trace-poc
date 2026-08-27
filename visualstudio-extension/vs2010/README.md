# ATEC Source Trace — Microsoft Visual Studio 2010 Extension (Adapter)



Visual Studio **2010 (10.x)** C/C++ Editor용 Source Trace Backend v2.6 Adapter입니다.



VS2017(`vs2017/`)와 **별도 VSIX·Identity**입니다.



## 기술 요약



| 항목 | VS2010 |

|------|--------|

| VSIX 스키마 | **1.0** (`Version="1.0.0"`) |

| Package | classic `Package` (AsyncPackage 아님) |

| Target framework | net40 |

| Command table | VSSDK `VSCTCompile` + `VSPackage.resx` `MergeWithCTO=true` |

| Installation target | Visual Studio **10.0** |

| Identity | `Atec.SourceTrace.VisualStudio2010.d0c19e45` |

| 패키징 | `scripts/pack_vsix.py` (VSIX 1.0 zip, CTO Win32 embed 없음) |



## 기능



- 함수 변경 이력 조회 → `POST /api/trace/report`

- 선택 코드 변경 근거 조회 → `POST /api/trace/selection`

- Server URL / 장비 설정 (Visual Studio 사용자 설정)

- 결과: `ATEC Source Trace` Tool Window (Backend `content` Markdown)



## 빌드 (개발 PC)



```powershell

cd visualstudio-extension\vs2010

.\build-vsix.ps1

```



요구: .NET SDK (`dotnet msbuild`), NuGet VSSDK 10 packages, Python 3 (VSIX pack + CTMENU 검증).



## 산출물



- `out/source-trace-visualstudio2010-0.1.3.vsix`

- `산출물/운영PC/visualstudio/source-trace-visualstudio2010-0.1.3.vsix`



## 설치 (운영 PC)



Visual Studio 2010 종료 → VSIX 더블클릭 → Install → **도구 → Extension Manager**에서 Enable → **도구 → ATEC Source Trace** 및 C/C++ 우클릭 메뉴 확인.



상세·테스트: `산출물/운영PC/VisualStudio2010_Source_Trace_설치_사용_가이드.md`



## Backend



**수정 없음** — 기존 Source Trace Backend v2.6 API contract 그대로 사용.

