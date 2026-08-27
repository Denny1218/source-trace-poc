# ATEC Source Trace — Visual Studio Extension (공식)

Source Trace Backend v2.6 Adapter입니다. **공식 운영 설치 파일은 아래 두 개뿐입니다.**

| Visual Studio | 정책 | 설치 파일 | 버전 |
|---|---|---|---|
| **2017** | 공식 지원 | `source-trace-visualstudio2017-0.1.3.vsix` | 0.1.3 |
| **2010** | legacy compatibility | `source-trace-visualstudio2010-0.1.3.vsix` | 0.1.3 |

Visual Studio 2022는 현재 POC **공식 지원·배포 대상이 아닙니다.**

이전 공식 빌드(0.1.0~0.1.2)는 `이전버전/`에만 있습니다. MenuProbe 등 진단용 VSIX는 `산출물/개발진단/visualstudio/`에 있으며 **운영 설치 대상이 아닙니다.**

## Visual Studio 2017

1. Visual Studio 2017 종료
2. `source-trace-visualstudio2017-0.1.3.vsix` 더블클릭
3. 대상 Visual Studio **2017** 인스턴스 선택 → Install
4. Visual Studio 재시작
5. **도구 → ATEC Source Trace** 및 C/C++ 우클릭 메뉴 표시 확인

상세: `../VisualStudio2017_Source_Trace_설치_사용_가이드.md`

## Visual Studio 2010

1. Visual Studio 2010 종료
2. `source-trace-visualstudio2010-0.1.3.vsix` 더블클릭
3. 대상 Visual Studio **2010** 확인 → Install
4. Visual Studio 재시작 → **도구 → Extension Manager**에서 Enable
5. **도구 → ATEC Source Trace** 및 C/C++ 우클릭 메뉴 표시 확인

상세: `../VisualStudio2010_Source_Trace_설치_사용_가이드.md`
