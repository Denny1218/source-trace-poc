# ATEC Source Trace — Eclipse Plug-in

Backend **v2.6 API Freeze** Adapter. Does **not** modify `backend/`, `frontend/`, VS Code Extension, or equipment projects.

## Ops install package (no PDE on ops PC)

| Artifact | Purpose |
|----------|---------|
| `산출물/운영PC/eclipse/source-trace-eclipse-update-site-0.1.1.zip` | **Binary p2 Update Site** — install with Help → Install New Software → Archive |
| `…-0.1.1-SOURCE.zip` | Source backup only — **not** installable |

Rebuild binary ZIP on a **dev PC** (needs JDK 17 + Maven + network for Tycho/Eclipse p2 resolve):

```text
eclipse-plugin/build-update-site.ps1
```

Headless stack: **Maven 3.9.x + Tycho 4.0.8**, target `https://download.eclipse.org/releases/2023-12`.

Ops PC needs **neither** PDE nor Maven/Tycho nor internet for install.

## Requirements (runtime on ops Eclipse)

- Eclipse IDE for C/C++ Developers (or Eclipse + CDT)
- Java 17+ (Eclipse runtime)
- Git CLI on PATH (repo-relative path; `.git` walk fallback)
- Reachable Source Trace Backend (`GET /api/health`)

## Dev: import in PDE (optional)

1. File → Import → Existing Projects → `com.atec.sourcetrace.eclipse`
2. Or `mvn -f eclipse-plugin/pom.xml clean verify`

## Official commands

| Menu | Backend |
|------|---------|
| 함수 변경 이력 조회 | `POST /api/trace/report` |
| 선택 코드 변경 근거 조회 | `POST /api/trace/selection` |

Identity key: `equipment_id` + `repo_relative_path` (never IDE absolute path as primary key).

## Unit tests (core, no Eclipse UI)

```text
eclipse-plugin/unit-tests/run-tests.ps1
```

## Non-interference

Preferences only (`PreferenceStore`). Must not write `.project`, `.cproject`, `.settings`, or equipment sources.
