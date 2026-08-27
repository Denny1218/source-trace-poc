"""STEP 7 Evidence Link scoring configuration.

All weights are internal rule-based ranking scores, not percentages. No 0-100
cap is applied (Option A — see STEP 7 completion report for rationale): the
Change Item Search Score (STEP 6, `ppt_fallback_config.CHANGE_ITEM_SCORE_CONFIG`)
already exceeds 100 for multi-field matches and is used purely for internal
ranking, so Link Score follows the same convention for consistency.

Weight rationale (see completion report item 5/6):
- Primary evidence (exact/structural identity signals) starts at 25 and caps
  at 40, mirroring the top end of STEP 6's `CHANGE_ITEM_SCORE_CONFIG`
  (title=40, source_function=35) and STEP 4's `TRACE_SCORE_CONFIG`
  (file_path=30) scales, so STEP 7 scores stay in a comparable numeric range.
- Weak evidence (10-15) mirrors STEP 4's `context`/`diff_keyword` and STEP 6's
  `raw_text` weights — deliberately low so no single weak signal can reach
  Primary-equivalent weight on its own.
"""

import os

LINKER_VERSION = "rule-v1"

LINK_SCORE_CONFIG = {
    # --- Primary evidence: at least one of these opens the Evidence Gate ---
    "same_function_exact": 40,
    "csr_exact": 35,
    "same_file_path": 35,  # EXACT or SUFFIX path match level (see source_path_utils)
    "same_file_basename": 25,
    "commit_message_change_title": 25,
    # --- Weak evidence: need >= 2 distinct types (without a Primary) to pass gate ---
    "diff_change_title": 15,
    "diff_source_function": 15,
    "date_0_7_days": 15,
    "message_other_field": 12,
    "date_8_30_days": 10,
    "diff_other_field": 10,
    "date_31_90_days": 5,
    "raw_text_keyword": 5,
}

PRIMARY_EVIDENCE_TYPES = frozenset(
    {
        "same_function_exact",
        "csr_exact",
        "same_file_path",
        "same_file_basename",
        "commit_message_change_title",
    }
)

WEAK_EVIDENCE_TYPES = frozenset(LINK_SCORE_CONFIG) - PRIMARY_EVIDENCE_TYPES

# Primary Evidence Gate (STEP 7 section 14): a Git<->Change Item pair is kept
# only if it has >= 1 Primary evidence, OR >= this many *distinct* Weak
# evidence types. This guarantees a lone date-proximity or raw-text match can
# never create an Evidence Link by itself (both are single Weak types).
MIN_WEAK_EVIDENCE_TYPES_WITHOUT_PRIMARY = 2

# Diff text can be very long; bound keyword/CSR/symbol scanning to the first
# N characters of a Top-5 Git Candidate's diff (already a small, pre-filtered
# set — this is not a full-repository scan).
DIFF_KEYWORD_SCAN_LIMIT_CHARS = int(os.getenv("TRACE_DIFF_KEYWORD_SCAN_LIMIT_CHARS", "4000"))

# On-demand Link scope: only Git Top 5 (TOP_CANDIDATE_LIMIT) x Change Item
# Top N are paired — never a full Cartesian product over the whole DB.
TRACE_CHANGE_ITEM_LINK_LIMIT = int(os.getenv("TRACE_CHANGE_ITEM_LINK_LIMIT", "30"))

# Final Evidence Link result size returned to the caller.
TRACE_EVIDENCE_LINK_LIMIT = int(os.getenv("TRACE_EVIDENCE_LINK_LIMIT", "10"))

# Minimum total Link Score to keep a pair. Set at the smallest score reachable
# via 2 combined Weak types (5 + 5 = 10) so it never contradicts the Gate —
# the Gate is the real filter; this is a defensive floor for future weight
# changes.
TRACE_LINK_MIN_SCORE = int(os.getenv("TRACE_LINK_MIN_SCORE", "10"))

# Diff excerpt window for future STEP 8 Evidence Context (±N lines around a
# matched keyword/symbol/CSR occurrence in the diff).
DIFF_EXCERPT_CONTEXT_LINES = int(os.getenv("TRACE_DIFF_EXCERPT_CONTEXT_LINES", "5"))
