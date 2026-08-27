"""STEP 7: Rule-based, explainable Link Score between a Git Candidate and a
Change Item.

No ML / LLM / embedding / vector search is used. Every `MatchReason` traces
back to one explicit rule and the concrete values that triggered it (see
PROJECT_SPEC v2 STEP 7 and the completion report for weight rationale).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.link_score_config import (
    DIFF_KEYWORD_SCAN_LIMIT_CHARS,
    LINK_SCORE_CONFIG,
    MIN_WEAK_EVIDENCE_TYPES_WITHOUT_PRIMARY,
    PRIMARY_EVIDENCE_TYPES,
    WEAK_EVIDENCE_TYPES,
)
from app.services.csr_utils import csr_appears_in_text
from app.services.keyword_extractor import extract_keywords
from app.services.ppt_date_parser import parse_date_from_text, parse_iso_date
from app.services.source_path_utils import PathMatchLevel, best_match_level, source_path_match_level
from app.services.symbol_utils import normalize_symbol, symbol_appears_in_text

_STRUCTURED_FIELDS = ("business_background", "current_status", "as_is", "to_be")

_DATE_BUCKETS: tuple[tuple[int, str], ...] = (
    (7, "date_0_7_days"),
    (30, "date_8_30_days"),
    (90, "date_31_90_days"),
)


@dataclass
class MatchReason:
    type: str
    score: int
    git_value: str | None = None
    change_item_value: str | None = None
    distance_days: int | None = None
    match_level: str | None = None

    def to_dict(self) -> dict:
        data: dict = {"type": self.type, "score": self.score}
        if self.git_value is not None:
            data["git_value"] = self.git_value
        if self.change_item_value is not None:
            data["change_item_value"] = self.change_item_value
        if self.distance_days is not None:
            data["distance_days"] = self.distance_days
        if self.match_level is not None:
            data["match_level"] = self.match_level
        return data


@dataclass
class LinkScoreResult:
    score: int
    match_reasons: list[MatchReason] = field(default_factory=list)
    passes_gate: bool = False


@dataclass
class GitEvidenceInput:
    """Intrinsic Git-side fields used for Link Score (query-independent)."""

    file_path: str
    message: str
    diff: str | None
    commit_date: str | None


@dataclass
class ChangeItemEvidenceInput:
    """Intrinsic Change Item fields used for Link Score (query-independent).

    Deliberately excludes query-dependent fields (matched_keywords,
    candidate_score, from_cache_search, from_fallback) so the resulting score
    is stable regardless of which user query produced the candidate — this is
    what makes `change_link` caching valid (see change_link_service.py)."""

    change_title: str | None
    csr_no: str | None
    business_background: str | None
    current_status: str | None
    as_is: str | None
    to_be: str | None
    raw_text: str | None
    source_functions: list[dict]
    file_name: str | None


def evaluate_gate(reasons: list[MatchReason]) -> bool:
    """Primary Evidence Gate (STEP 7 section 14).

    A pair passes when it has >= 1 Primary evidence, or >= 2 *distinct* Weak
    evidence types. A single Weak type (e.g. date proximity alone, or a raw
    text keyword alone) never passes — this guarantees date-only and
    modified_at-only pairs are excluded (modified_at is never used as a Link
    Score input in the first place)."""
    present_types = {r.type for r in reasons}
    has_primary = bool(present_types & PRIMARY_EVIDENCE_TYPES)
    weak_type_count = len(present_types & WEAK_EVIDENCE_TYPES)
    return has_primary or weak_type_count >= MIN_WEAK_EVIDENCE_TYPES_WITHOUT_PRIMARY


def _keyword_hit(keywords: list[str], text: str | None) -> str | None:
    if not text:
        return None
    lower = text.lower()
    for kw in keywords:
        if kw.lower() in lower or kw in text:
            return kw
    return None


def _file_match_evidence(
    git_path: str, item: ChangeItemEvidenceInput
) -> MatchReason | None:
    if not git_path:
        return None

    levels: list[tuple[PathMatchLevel, str]] = []
    for entry in item.source_functions:
        ci_path = entry.get("file_path")
        if not ci_path:
            continue
        levels.append((source_path_match_level(git_path, ci_path), ci_path))

    if not levels:
        return None

    best = best_match_level([lvl for lvl, _ in levels])
    if best == PathMatchLevel.NONE:
        return None

    best_ci_path = next(path for lvl, path in levels if lvl == best)

    if best in (PathMatchLevel.EXACT, PathMatchLevel.SUFFIX):
        return MatchReason(
            type="same_file_path",
            score=LINK_SCORE_CONFIG["same_file_path"],
            git_value=git_path,
            change_item_value=best_ci_path,
            match_level=best.value,
        )
    return MatchReason(
        type="same_file_basename",
        score=LINK_SCORE_CONFIG["same_file_basename"],
        git_value=git_path,
        change_item_value=best_ci_path,
        match_level=best.value,
    )


def _function_match_evidence(
    git: GitEvidenceInput, item: ChangeItemEvidenceInput
) -> MatchReason | None:
    haystacks = [git.message or "", (git.diff or "")[:DIFF_KEYWORD_SCAN_LIMIT_CHARS]]
    for entry in item.source_functions:
        for fn in entry.get("functions") or []:
            symbol = normalize_symbol(fn)
            if not symbol:
                continue
            for haystack in haystacks:
                if symbol_appears_in_text(symbol, haystack):
                    return MatchReason(
                        type="same_function_exact",
                        score=LINK_SCORE_CONFIG["same_function_exact"],
                        git_value=symbol,
                        change_item_value=fn,
                    )
    return None


def _csr_match_evidence(
    git: GitEvidenceInput, item: ChangeItemEvidenceInput
) -> MatchReason | None:
    csr = (item.csr_no or "").strip()
    if not csr:
        return None
    haystack = f"{git.message or ''}\n{(git.diff or '')[:DIFF_KEYWORD_SCAN_LIMIT_CHARS]}"
    if csr_appears_in_text(csr, haystack):
        return MatchReason(
            type="csr_exact",
            score=LINK_SCORE_CONFIG["csr_exact"],
            git_value=csr,
            change_item_value=csr,
        )
    return None


def _keyword_evidence(
    git: GitEvidenceInput, item: ChangeItemEvidenceInput
) -> list[MatchReason]:
    reasons: list[MatchReason] = []
    message_keywords = extract_keywords(git.message or "")
    diff_text = (git.diff or "")[:DIFF_KEYWORD_SCAN_LIMIT_CHARS]
    diff_keywords = extract_keywords(diff_text) if diff_text else []

    any_structured_hit = False

    hit = _keyword_hit(message_keywords, item.change_title)
    if hit:
        reasons.append(
            MatchReason(
                type="commit_message_change_title",
                score=LINK_SCORE_CONFIG["commit_message_change_title"],
                git_value=hit,
                change_item_value=item.change_title,
            )
        )
        any_structured_hit = True

    for field_name in _STRUCTURED_FIELDS:
        value = getattr(item, field_name)
        hit = _keyword_hit(message_keywords, value)
        if hit:
            reasons.append(
                MatchReason(
                    type="message_other_field",
                    score=LINK_SCORE_CONFIG["message_other_field"],
                    git_value=hit,
                    change_item_value=value,
                )
            )
            any_structured_hit = True
            break

    if diff_keywords:
        hit = _keyword_hit(diff_keywords, item.change_title)
        if hit:
            reasons.append(
                MatchReason(
                    type="diff_change_title",
                    score=LINK_SCORE_CONFIG["diff_change_title"],
                    git_value=hit,
                    change_item_value=item.change_title,
                )
            )
            any_structured_hit = True

        for field_name in _STRUCTURED_FIELDS:
            value = getattr(item, field_name)
            hit = _keyword_hit(diff_keywords, value)
            if hit:
                reasons.append(
                    MatchReason(
                        type="diff_other_field",
                        score=LINK_SCORE_CONFIG["diff_other_field"],
                        git_value=hit,
                        change_item_value=value,
                    )
                )
                any_structured_hit = True
                break

        source_texts: list[str] = []
        for entry in item.source_functions:
            if entry.get("raw_text"):
                source_texts.append(str(entry["raw_text"]))
            if entry.get("file_path"):
                source_texts.append(str(entry["file_path"]))
        for text in source_texts:
            hit = _keyword_hit(diff_keywords, text)
            if hit:
                reasons.append(
                    MatchReason(
                        type="diff_source_function",
                        score=LINK_SCORE_CONFIG["diff_source_function"],
                        git_value=hit,
                        change_item_value=text,
                    )
                )
                any_structured_hit = True
                break

    if not any_structured_hit and item.raw_text:
        combined_keywords = message_keywords + diff_keywords
        hit = _keyword_hit(combined_keywords, item.raw_text)
        if hit:
            reasons.append(
                MatchReason(
                    type="raw_text_keyword",
                    score=LINK_SCORE_CONFIG["raw_text_keyword"],
                    git_value=hit,
                )
            )

    return reasons


def _date_evidence(
    git: GitEvidenceInput, item: ChangeItemEvidenceInput
) -> MatchReason | None:
    """Weak, auxiliary evidence only (STEP 5 policy: date is never Primary).

    Uses the Change Item's *document filename* date only — never
    `document_cache.modified_at` — consistent with the existing STEP 5 policy
    that filesystem modified-time is a weak helper, not a change-date proxy."""
    if not git.commit_date or not item.file_name:
        return None
    doc_date = parse_date_from_text(item.file_name)
    if doc_date is None:
        return None
    try:
        commit_date = parse_iso_date(git.commit_date)
    except ValueError:
        return None

    distance = abs((commit_date - doc_date).days)
    for max_days, evidence_type in _DATE_BUCKETS:
        if distance <= max_days:
            return MatchReason(
                type=evidence_type,
                score=LINK_SCORE_CONFIG[evidence_type],
                distance_days=distance,
            )
    return None


def compute_link_score(
    git: GitEvidenceInput, item: ChangeItemEvidenceInput
) -> LinkScoreResult:
    reasons: list[MatchReason] = []

    file_reason = _file_match_evidence(git.file_path, item)
    if file_reason:
        reasons.append(file_reason)

    function_reason = _function_match_evidence(git, item)
    if function_reason:
        reasons.append(function_reason)

    csr_reason = _csr_match_evidence(git, item)
    if csr_reason:
        reasons.append(csr_reason)

    reasons.extend(_keyword_evidence(git, item))

    date_reason = _date_evidence(git, item)
    if date_reason:
        reasons.append(date_reason)

    total_score = sum(r.score for r in reasons)
    passes_gate = evaluate_gate(reasons)

    return LinkScoreResult(score=total_score, match_reasons=reasons, passes_gate=passes_gate)
