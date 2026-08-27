export const DEFAULT_START_DATE = "2000-01-01";

export function formatLocalDateForInput(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function parseKeywordInput(input: string): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const item of input.split(",")) {
    const keyword = item.trim();
    if (!keyword || seen.has(keyword)) {
      continue;
    }
    seen.add(keyword);
    result.push(keyword);
  }

  return result;
}
