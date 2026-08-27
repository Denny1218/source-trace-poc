# ATEC Source Trace — Microsoft Visual Studio Extension (Adapter)



Visual Studio 세대별 **별도 VSIX** Adapter입니다.



## 운영 배포 대상 (산출물)



| 대상 | 경로 | 산출물 |

|---|---|---|

| Visual Studio **2010 (10.x)** | [`vs2010/`](vs2010/) | `source-trace-visualstudio2010-0.1.3.vsix` |

| Visual Studio **2017 (15.x)** | [`vs2017/`](vs2017/) | `source-trace-visualstudio2017-0.1.3.vsix` |



상세: `산출물/운영PC/visualstudio/README.md`



## 소스만 유지 (운영 배포 제외)



| 대상 | 경로 | 비고 |

|---|---|---|

| Visual Studio **2022 (17.x)** | 이 폴더 (`src/`) | 소스·빌드 스크립트 유지, **산출물/문서 배포 대상 아님** |



## VS2010 / VS2017 공통 — Command table 빌드



```

.vsct → VSCTCompile → .cto → MergeWithCTO → VSPackage.resources (Menus.ctmenu byte[])

```



- `VSPackage.resx` + `<MergeWithCTO>true</MergeWithCTO>`

- `[ProvideMenuResource("Menus.ctmenu", 1)]`

- `[PackageRegistration(UseManagedResourcesOnly = true)]`

- 빌드 후 `scripts/verify_ctmenu_resource.py`로 DLL/VSIX 검증



## Backend



**수정 없음** — 기존 Source Trace Backend v2.6 API contract 그대로 사용.

