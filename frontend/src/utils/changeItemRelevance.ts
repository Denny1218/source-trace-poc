/**
 * Change Item candidate_score → user-facing relevance level.
 *
 * Thresholds derive from CHANGE_ITEM_SCORE_CONFIG (backend, unchanged):
 *   change_title 40 | source_function 35 | to_be 30 | csr_no 25
 *   business_background/current_status/as_is 20 | raw_text 10
 *
 * Observed distributions (synthetic fixture + rule combos):
 *   85  — title + source + secondary field (multi-keyword)
 *   70  — title + to_be (strong single-doc match)
 *   45  — source + raw_text, or title + raw_text
 *   35  — csr/source-only match
 *   10  — raw_text-only weak match
 *
 * Ops-style examples: 140, 105, 75 → high; 35 → medium.
 */
export type RelevanceLevel = "high" | "medium" | "low";

/** Scores ≥ 70: title+to_be, title+source, or multi-field strong match. */
export const RELEVANCE_HIGH_MIN = 70;

/** Scores ≥ 30: to_be/source/title-alone (40) or csr+secondary; below = raw-only weak. */
export const RELEVANCE_MEDIUM_MIN = 30;

const LABELS: Record<RelevanceLevel, string> = {
  high: "관련도 높음",
  medium: "관련도 보통",
  low: "관련도 낮음",
};

export function getRelevanceLevel(score: number): RelevanceLevel {
  if (score >= RELEVANCE_HIGH_MIN) return "high";
  if (score >= RELEVANCE_MEDIUM_MIN) return "medium";
  return "low";
}

export function getRelevanceLabel(score: number): string {
  return LABELS[getRelevanceLevel(score)];
}
