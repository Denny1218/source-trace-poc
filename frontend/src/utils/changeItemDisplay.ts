import type { ChangeItemCandidate } from "../api/pptCache";

const META_SEP = " · ";
const SCOPE_SEP = " · ";

/** Primary meta: Slide · 항목 · CSR — omit empty segments. */
export function formatMetaPrimaryLine(item: Pick<
  ChangeItemCandidate,
  "slide_no" | "item_no" | "csr_no"
>): string | null {
  const parts: string[] = [`Slide ${item.slide_no}`];
  if (item.item_no?.trim()) parts.push(`항목 ${item.item_no.trim()}`);
  if (item.csr_no?.trim()) parts.push(`CSR ${item.csr_no.trim()}`);
  return parts.length > 0 ? parts.join(META_SEP) : null;
}

/** Applicable scopes joined with compact separator. */
export function formatApplicableScopes(scopes: string[]): string | null {
  const cleaned = scopes.map((s) => s.trim()).filter(Boolean);
  if (cleaned.length === 0) return null;
  return cleaned.join(SCOPE_SEP);
}

export function sortChangeItemCandidates(
  items: ChangeItemCandidate[],
): ChangeItemCandidate[] {
  return [...items].sort((a, b) => {
    if (b.candidate_score !== a.candidate_score) {
      return b.candidate_score - a.candidate_score;
    }
    const nameCmp = a.file_name.localeCompare(b.file_name, "ko");
    if (nameCmp !== 0) return nameCmp;
    return a.slide_no - b.slide_no;
  });
}

export function countDistinctDocuments(items: ChangeItemCandidate[]): number {
  return new Set(items.map((i) => i.document_cache_id)).size;
}
