# -*- coding: utf-8 -*-
"""Export Cursor agent transcripts as STEP-based conversation archives.

포함 범위 (중요):
- Cursor IDE에서 수행한 **Source Trace POC 메인 개발 대화**만 STEP 0~10에 저장
- 아카이브 정리·AICA 신청서·제출 패키지 메타 논의 등 **별도 채팅은 제외**

규칙:
- 사용자 Prompt / 어시스턴트 응답을 시각적으로 확실히 구분
- 어시스턴트 응답·완료보고: 요약하지 않음 (원문)
- 진행 과정(도구 호출이 긴 경우)만 요약
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TRANSCRIPT_ROOT = Path(
    r"C:\Users\denny\.cursor\projects\c-sourcechangeTrace\agent-transcripts"
)
OUT_DIR = Path(r"c:\sourcechangeTrace\산출물\대화기록")

# POC 메인 개발 대화 (Cursor) — STEP 0~10 유일 소스
MAIN_CHAT_ID = "ae5ad5ce-4518-486d-966a-bbcfeee7ba50"
MAIN_CHAT_TITLE = "Cursor 메인 개발 대화 (Source Trace POC)"

# STEP 본문에는 넣지 않는 채팅 (메타·신청서·아카이브 정리 등)
EXCLUDED_CHAT_IDS: dict[str, str] = {
    "05b29092-d53b-45c6-a774-97743fa4ac7e": (
        "대화기록 아카이브/제출·AICA 신청서 등 메타 대화 (본 아카이브 제외)"
    ),
    "adbdeb12-bf57-4f69-90d6-72c9143a0374": (
        "프로젝트 본 개발과 무관한 단건 문의 (package.json 등) — 제외"
    ),
}

# STEP 외 단건·비관련 채팅은 아카이브에 넣지 않음 (이 프로젝트 메인 개발 대화만).
MISC_CHATS: dict[str, str] = {}

STEP_TITLES = {
    0: "프로젝트 기본 실행 환경 구축",
    1: "장비 관리",
    2: "Git 변경 이력 수집",
    3: "Git 변경 이력 조회",
    4: "변경 추적 요청 API 및 Trace 흐름 구축",
    5: "Git 기반 PPT 후보 탐색",
    6: "PPT On-demand 분석 및 Cache",
    7: "Git-PPT 근거 연계",
    8: "Ollama 근거 기반 변경 사유 분석",
    9: "VSCode Continue 연계 및 Extension",
    10: "운영환경 배포 및 단계별 검증",
}

STEP_BLURBS = {
    0: "프로젝트 스펙 이해 및 실행 환경(Backend/Frontend) 기본 구축",
    1: "장비 등록·조회 등 장비 관리 API/화면",
    2: "장비별 Git Repository 연동 및 Commit 이력 수집",
    3: "수집된 Git 변경 이력 Web 조회",
    4: "Trace 검색·후보 랭킹 등 변경 추적 요청 흐름",
    5: "Git 검색 컨텍스트 기반 PPT 후보 탐색",
    6: "PPT On-demand 분석 및 Change Item Cache",
    7: "Git Candidate ↔ Change Item Evidence Link",
    8: "Ollama(선택) 근거 기반 변경 사유 문장 생성",
    9: "Continue/VS Code Extension 및 함수 이력 조회",
    10: "운영 배포·검증, 선택 코드 조회, Eclipse/VS Adapter, 제출 패키지",
}

# 메인 대화 user turn(1-based) → STEP
STEP_RANGES: list[tuple[int, int, int]] = [
    (0, 1, 1),
    (1, 2, 2),
    (2, 3, 3),
    (3, 4, 4),
    (4, 5, 5),
    (5, 6, 7),
    (6, 8, 47),
    (7, 48, 65),
    (8, 66, 71),
    (9, 72, 119),
    (10, 120, 10_000),
]

# STEP 10을 주제별로 나누어 읽기 쉽게 (메인 turn 번호)
STEP10_PART_RANGES: list[tuple[int, int, str]] = [
    (120, 150, "운영 배포·선택 코드 조회·명세 보완"),
    (151, 203, "v2.5.1 보완·Eclipse/Visual Studio Adapter"),
    (204, 10_000, "VS 진단·Release Freeze·산출물 정리"),
]

SKIP_PROMPT_MARKERS = (
    "You have access to tools through dynamic namespaces",
    "<dynamic_tools>",
    "Start multitasking",
    "Perform any necessary follow-up actions in response to the subagent",
    "Briefly inform the user about the task result and perform any follow-up",
)

USER_QUERY_RE = re.compile(
    r"<timestamp>(.*?)</timestamp>\s*<user_query>\s*(.*?)\s*</user_query>",
    re.DOTALL,
)

PROCESS_WITH_TOOLS_MAX = 400


@dataclass
class AssistantChunk:
    text: str
    with_tools: bool
    tools: list[str] = field(default_factory=list)


@dataclass
class Turn:
    chat_id: str
    chat_title: str
    index: int
    timestamp: str
    user_prompt: str
    chunks: list[AssistantChunk] = field(default_factory=list)
    all_tools: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    step: int | None = None


def clean_text(text: str) -> str:
    text = text.replace("[REDACTED]", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_parts(content) -> tuple[list[str], list[str]]:
    texts: list[str] = []
    tools: list[str] = []
    if content is None:
        return texts, tools
    if isinstance(content, str):
        cleaned = clean_text(content)
        if cleaned:
            texts.append(cleaned)
        return texts, tools
    if not isinstance(content, list):
        return texts, tools
    for item in content:
        if not isinstance(item, dict):
            continue
        t = item.get("type")
        if t == "text":
            cleaned = clean_text(item.get("text") or "")
            if cleaned:
                texts.append(cleaned)
        elif t == "tool_use":
            tools.append(item.get("name") or "tool")
    return texts, tools


def parse_user_message(text: str) -> tuple[str, str]:
    m = USER_QUERY_RE.search(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    cleaned = re.sub(r"</?timestamp>.*?</timestamp>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"</?user_query>", "", cleaned)
    return "", cleaned.strip()


def load_turns_from_jsonl(path: Path, chat_id: str, chat_title: str) -> list[Turn]:
    turns: list[Turn] = []
    current: Turn | None = None

    def close_current() -> None:
        nonlocal current
        if current is not None:
            turns.append(current)
            current = None

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = obj.get("role")
            if role == "turn_ended":
                status = obj.get("status")
                err = obj.get("error")
                if current is not None and (status or err):
                    current.errors.append(f"{status or ''}: {err or ''}".strip(": "))
                continue

            msg = obj.get("message") or {}
            texts, tools = extract_text_parts(msg.get("content"))

            if role == "user":
                close_current()
                raw = "\n".join(texts)
                ts, prompt = parse_user_message(raw)
                current = Turn(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    index=len(turns) + 1,
                    timestamp=ts or "(시각 없음)",
                    user_prompt=prompt or raw.strip(),
                )
                continue

            if role == "assistant" and current is not None:
                current.all_tools.extend(tools)
                joined = "\n\n".join(texts).strip()
                if joined:
                    current.chunks.append(
                        AssistantChunk(
                            text=joined,
                            with_tools=bool(tools),
                            tools=list(tools),
                        )
                    )

    close_current()
    return turns


def split_response_and_process(
    turn: Turn,
) -> tuple[list[str], list[str], str]:
    responses: list[str] = []
    process_notes: list[str] = []

    for chunk in turn.chunks:
        if chunk.with_tools and len(chunk.text) <= PROCESS_WITH_TOOLS_MAX:
            one = re.sub(r"\s+", " ", chunk.text.replace("\n", " ")).strip()
            if one and one not in process_notes:
                process_notes.append(one)
            continue
        responses.append(chunk.text)

    tool_summary = ""
    if turn.all_tools:
        seen: set[str] = set()
        uniq: list[str] = []
        for n in turn.all_tools:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        counts = {n: turn.all_tools.count(n) for n in uniq}
        desc = ", ".join(
            f"{n}×{counts[n]}" if counts[n] > 1 else n for n in uniq[:30]
        )
        if len(uniq) > 30:
            desc += f" 외 {len(uniq) - 30}개"
        tool_summary = f"사용 도구: {desc} (총 {len(turn.all_tools)}회)"

    return responses, process_notes[:8], tool_summary


def should_skip_prompt(prompt: str) -> bool:
    return any(marker in prompt for marker in SKIP_PROMPT_MARKERS)


def assign_main_steps(turns: list[Turn]) -> tuple[list[Turn], int]:
    saved: list[Turn] = []
    excluded = 0
    for turn in turns:
        if should_skip_prompt(turn.user_prompt) or not turn.user_prompt.strip():
            excluded += 1
            continue
        step = None
        for s, start, end in STEP_RANGES:
            if start <= turn.index <= end:
                step = s
                break
        if step is None:
            excluded += 1
            continue
        turn.step = step
        saved.append(turn)
    return saved, excluded


def _prompt_preview(text: str, limit: int = 72) -> str:
    one = re.sub(r"\s+", " ", (text or "").strip())
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def render_turn(seq_in_step: int, turn: Turn) -> str:
    responses, process_notes, tool_summary = split_response_and_process(turn)
    step_label = (
        f"STEP {turn.step} — {STEP_TITLES.get(turn.step, '')}"
        if turn.step is not None
        else "기타 (STEP 외)"
    )

    lines: list[str] = []
    lines.append("")
    lines.append("╔" + "═" * 78 + "╗")
    lines.append(
        f"║  [{seq_in_step:03d}]  {step_label}".ljust(79) + "║"
    )
    lines.append(
        f"║  메인 turn #{turn.index}  |  {turn.timestamp}".ljust(79) + "║"
    )
    lines.append(
        f"║  출처: {turn.chat_title}".ljust(79) + "║"
    )
    lines.append("╚" + "═" * 78 + "╝")
    lines.append("")

    lines.append("### ◆ 사용자 Prompt（원문）")
    lines.append("")
    lines.append("```text")
    lines.append(turn.user_prompt)
    lines.append("```")
    lines.append("")

    lines.append("### ◆ 어시스턴트 응답（원문 · 요약 없음）")
    lines.append("")
    if responses:
        for i, text in enumerate(responses, 1):
            if len(responses) > 1:
                lines.append(f"#### 응답 {i}/{len(responses)}")
                lines.append("")
            lines.append(text)
            lines.append("")
    else:
        lines.append("_이 턴에서 도구 없는 최종 응답 텍스트가 transcript에 없음_")
        lines.append("")

    lines.append("### ◇ 진행 과정 요약（도구·짧은 안내만）")
    lines.append("")
    if process_notes:
        for note in process_notes:
            lines.append(f"- {note}")
        lines.append("")
    if tool_summary:
        lines.append(f"- {tool_summary}")
        lines.append("")
    if not process_notes and not tool_summary:
        lines.append("- _(도구 호출 없음)_")
        lines.append("")
    if turn.errors:
        lines.append(f"- 턴 종료 상태: {'; '.join(turn.errors)}")
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def _safe_name(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", title)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:60]


def _split_step10_parts(turns: list[Turn]) -> list[tuple[str, list[Turn]]]:
    parts: list[tuple[str, list[Turn]]] = []
    for start, end, subtitle in STEP10_PART_RANGES:
        chunk = [t for t in turns if start <= t.index <= end]
        if chunk:
            parts.append((subtitle, chunk))
    # 혹시 범위 밖 잔여
    covered = {t.index for _, chunk in parts for t in chunk}
    rest = [t for t in turns if t.index not in covered]
    if rest:
        parts.append(("기타 STEP 10 잔여", rest))
    return parts


def _split_by_size(turns: list[Turn], max_chars: int = 380_000) -> list[list[Turn]]:
    parts: list[list[Turn]] = []
    current: list[Turn] = []
    size = 0
    for turn in turns:
        est = len(turn.user_prompt) + sum(len(c.text) for c in turn.chunks) + 1200
        if current and size + est > max_chars:
            parts.append(current)
            current = []
            size = 0
        current.append(turn)
        size += est
    if current:
        parts.append(current)
    return parts


def write_step_file(
    step: int, turns: list[Turn], global_start: int
) -> tuple[list[tuple[str, Path, int, int]], int]:
    title = STEP_TITLES[step]
    if step == 10:
        named_parts = _split_step10_parts(turns)
    else:
        sized = _split_by_size(turns)
        named_parts = [("", chunk) for chunk in sized]

    written: list[tuple[str, Path, int, int]] = []
    idx = global_start
    total_parts = len(named_parts)

    for part_i, (subtitle, part_turns) in enumerate(named_parts, 1):
        suffix = f"_Part{part_i:02d}" if total_parts > 1 else ""
        fname = f"STEP_{step:02d}_{_safe_name(title)}{suffix}.md"
        out = OUT_DIR / fname
        start_t = part_turns[0].index
        end_t = part_turns[-1].index
        heading = f"# STEP {step}. {title}"
        if total_parts > 1:
            heading += f" (Part {part_i}/{total_parts})"
            if subtitle:
                heading += f" — {subtitle}"

        toc_lines = ["## 이 Part turn 목록", ""]
        for i, t in enumerate(part_turns, 1):
            toc_lines.append(
                f"{i}. 메인 #{t.index} — {_prompt_preview(t.user_prompt)}"
            )
        toc_lines.append("")

        body: list[str] = [
            heading,
            "",
            f"> **범위**: Cursor 메인 개발 대화 turn **#{start_t} ~ #{end_t}** "
            f"（{len(part_turns)}턴）",
            f"> **이 STEP 요지**: {STEP_BLURBS.get(step, '')}",
            "",
            "## 읽는 방법",
            "",
            "| 구역 | 내용 |",
            "|------|------|",
            "| `◆ 사용자 Prompt` | 사용자 입력 **원문** |",
            "| `◆ 어시스턴트 응답` | 답변·완료보고 **원문** (요약 없음) |",
            "| `◇ 진행 과정 요약` | 도구 호출·짧은 중간 안내만 요약 |",
            "",
            "---",
            "",
            *toc_lines,
            "---",
            "",
        ]
        seq = 1
        for turn in part_turns:
            body.append(render_turn(seq, turn))
            seq += 1
            idx += 1
        out.write_text("\n".join(body), encoding="utf-8")
        written.append((f"STEP {step}", out, start_t, end_t))
    return written, idx


def write_misc_file(turns: list[Turn], global_start: int) -> tuple[Path | None, int]:
    if not turns:
        return None, global_start
    out = OUT_DIR / "기타_STEP외_대화.md"
    body: list[str] = [
        "# 기타 — STEP 번호 밖 Cursor 단건 대화",
        "",
        "> POC STEP 0~10 **본문에는 포함하지 않음**. 개발 중 발생한 짧은은 단건 문의만 참고용으로 보관.",
        "",
        "## 읽는 방법",
        "",
        "- `◆ 사용자 Prompt` / `◆ 어시스턴트 응답` / `◇ 진행 과정 요약`",
        "",
        "---",
        "",
    ]
    idx = global_start
    seq = 1
    for turn in turns:
        turn.step = None
        body.append(render_turn(seq, turn))
        seq += 1
        idx += 1
    out.write_text("\n".join(body), encoding="utf-8")
    return out, idx


def clear_old_archives() -> list[str]:
    removed: list[str] = []
    if not OUT_DIR.exists():
        return removed
    for p in OUT_DIR.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if (
            name.startswith("대화기록_Part")
            or name.startswith("STEP_")
            or name.startswith("기타_")
            or name == "00_인덱스.md"
        ):
            p.unlink()
            removed.append(name)
    return removed


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    removed = clear_old_archives()

    main_path = TRANSCRIPT_ROOT / MAIN_CHAT_ID / f"{MAIN_CHAT_ID}.jsonl"
    main_turns = load_turns_from_jsonl(main_path, MAIN_CHAT_ID, MAIN_CHAT_TITLE)
    saved_main, excluded = assign_main_steps(main_turns)

    by_step: dict[int, list[Turn]] = {s: [] for s, _, _ in STEP_RANGES}
    for t in saved_main:
        assert t.step is not None
        by_step[t.step].append(t)

    written: list[tuple[str, Path, int, int]] = []
    global_idx = 1
    for step, _, _ in STEP_RANGES:
        turns = by_step[step]
        if not turns:
            continue
        extra, global_idx = write_step_file(step, turns, global_idx)
        written.extend(extra)

    misc_turns: list[Turn] = []
    for chat_id, title in MISC_CHATS.items():
        path = TRANSCRIPT_ROOT / chat_id / f"{chat_id}.jsonl"
        if not path.exists():
            continue
        for turn in load_turns_from_jsonl(path, chat_id, title):
            if should_skip_prompt(turn.user_prompt) or not turn.user_prompt.strip():
                continue
            misc_turns.append(turn)
    misc_path, global_idx = write_misc_file(misc_turns, global_idx)
    if misc_path:
        written.append(("기타", misc_path, 0, 0))

    step0 = by_step[0][0] if by_step[0] else None
    if step0:
        responses, _, _ = split_response_and_process(step0)
        joined = "\n".join(responses)
        assert "STEP 0 완료 보고" in joined, "STEP 0 완료보고 누락"
        assert len(joined) > 1500, f"STEP 0 응답이 너무 짧음: {len(joined)}"

    last_by_step: dict[int, int] = {}
    first_by_step: dict[int, int] = {}
    for t in saved_main:
        if t.step is None:
            continue
        last_by_step[t.step] = t.index
        first_by_step.setdefault(t.step, t.index)

    index_lines = [
        "# Source Trace POC — Cursor 대화 Prompt 아카이브",
        "",
        "Cursor IDE에서 진행한 **메인 개발 대화**만 STEP 단위로 정리한 기록입니다.",
        "",
        "## 1. 포함 / 제외（반드시 확인）",
        "",
        "### 포함",
        "",
        f"- Cursor 채팅: `{MAIN_CHAT_ID}` — **{MAIN_CHAT_TITLE}**",
        "- STEP 0 ~ STEP 10（프로젝트 스펙 단계와 동일 축）",
        "",
        "### 제외",
        "",
        "- 대화기록 아카이브 재정리·제출 패키지 메타·AICA 신청서 작성 등 **별도 Cursor 채팅**",
    ]
    for cid, reason in EXCLUDED_CHAT_IDS.items():
        index_lines.append(f"  - `{cid}` — {reason}")
    index_lines.extend(
        [
            "- transcript 시스템 주입 / multitask follow-up 등 비사용자 Prompt",
            "",
            "## 2. 읽는 방법",
            "",
            "| 구역 | 의미 | 요약 |",
            "|------|------|------|",
            "| `◆ 사용자 Prompt` | 사용자 입력 | **원문** |",
            "| `◆ 어시스턴트 응답` | 답변·완료보고 | **원문** |",
            "| `◇ 진행 과정 요약` | 도구·짧은 안내 | 요약 |",
            "",
            "각 STEP 파일 상단에 **turn 목록(목차)** 이 있어 Prompt만 훑어보기 쉽습니다.",
            "",
            "## 3. STEP 경계（메인 대화 turn）",
            "",
            "| STEP | 제목 | turn 범위 | 요지 |",
            "|------|------|-----------|------|",
        ]
    )
    for step, start, _end in STEP_RANGES:
        a = first_by_step.get(step, start)
        b = last_by_step.get(step, start)
        index_lines.append(
            f"| {step} | {STEP_TITLES[step]} | #{a} ~ #{b} | {STEP_BLURBS[step]} |"
        )

    index_lines.extend(
        [
            "",
            "## 4. 통계",
            "",
            f"- 메인 대화 user turn 전체: **{len(main_turns)}**",
            f"- STEP 0~10 저장: **{len(saved_main)}**",
            f"- 메인에서 제외(시스템 주입 등): **{excluded}**",
            f"- 제외된 기타/메타 채팅 수: **{len(EXCLUDED_CHAT_IDS)}**",
            "",
            "## 5. 파일 목록",
            "",
        ]
    )
    for label, path, start, end in written:
        size = path.stat().st_size
        if label == "기타":
            index_lines.append(f"- [{path.name}]({path.name}) — {size:,} bytes")
        else:
            index_lines.append(
                f"- [{path.name}]({path.name}) — 메인 turn #{start}~#{end}, "
                f"{size:,} bytes"
            )

    index_lines.extend(
        [
            "",
            "## 6. 재생성",
            "",
            "```bat",
            "python scripts/export_conversation_archive.py",
            "```",
            "",
            "이 스크립트는 **메인 개발 채팅만** STEP에 넣습니다. "
            "기타·메타·비관련 Cursor 채팅은 `EXCLUDED_CHAT_IDS`로 제외하며 "
            "`기타_STEP외_대화.md`는 생성하지 않습니다.",
            "",
        ]
    )
    if removed:
        index_lines.append("## 이번 재생성에서 교체한 이전 파일")
        index_lines.append("")
        for name in removed:
            index_lines.append(f"- `{name}`")
        index_lines.append("")

    (OUT_DIR / "00_인덱스.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"OUT_DIR={OUT_DIR}")
    print(f"saved_main={len(saved_main)} excluded={excluded}")
    print(f"excluded_meta_chats={list(EXCLUDED_CHAT_IDS)}")
    for label, path, start, end in written:
        text = path.read_text(encoding="utf-8")
        print(
            f"  {path.name}: {path.stat().st_size:,} bytes "
            f"user={text.count('◆ 사용자 Prompt')} "
            f"asst={text.count('◆ 어시스턴트 응답')} "
            f"turns=#{start}-{end}"
        )


if __name__ == "__main__":
    main()
