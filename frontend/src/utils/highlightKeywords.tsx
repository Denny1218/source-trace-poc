import type { ReactNode } from "react";

/** Case-insensitive keyword highlight without dangerouslySetInnerHTML. */
export function highlightKeywords(text: string, keywords: string[]): ReactNode {
  const tokens = keywords.filter((k) => k.trim().length > 0);
  if (tokens.length === 0) return text;
  const escaped = tokens.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = text.split(pattern);
  return parts.map((part, idx) =>
    tokens.some((k) => k.toLowerCase() === part.toLowerCase()) ? (
      <mark key={idx} className="ci-highlight">
        {part}
      </mark>
    ) : (
      <span key={idx}>{part}</span>
    ),
  );
}
