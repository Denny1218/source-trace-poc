/**
 * C symbol extraction and query augmentation for the Extension MVP.
 * Mirrors a subset of backend continue_service symbol logic — only shapes
 * the request before POST; does not duplicate Evidence search.
 */

const C_IDENT_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;

/** C keywords / weak tokens — never treat as a detected symbol. */
const C_KEYWORDS = new Set([
  "if",
  "else",
  "for",
  "while",
  "do",
  "switch",
  "case",
  "break",
  "continue",
  "return",
  "goto",
  "sizeof",
  "typedef",
  "struct",
  "union",
  "enum",
  "static",
  "extern",
  "inline",
  "const",
  "volatile",
  "unsigned",
  "signed",
  "void",
  "int",
  "char",
  "short",
  "long",
  "float",
  "double",
  "bool",
  "true",
  "false",
  "NULL",
]);

const C_FUNC_DEF_RE =
  /(?:\b(?:static|inline|extern|const|unsigned|signed|volatile)\s+)*(?:struct\s+\w+\s+)?\b([A-Za-z_][A-Za-z0-9_]*)\b[ \t]*\*{0,2}[ \t]*\(/;

const C_FUNC_CALL_RE = /\b([A-Za-z_][A-Za-z0-9_]*)\s*\(/g;

/**
 * Best-effort primary C symbol from selected text.
 * - Single identifier → that name
 * - Declaration / call site → first meaningful function name
 */
export function extractDetectedSymbol(selectedText: string | undefined): string | undefined {
  const raw = (selectedText ?? "").trim();
  if (!raw) {
    return undefined;
  }

  if (C_IDENT_RE.test(raw) && !C_KEYWORDS.has(raw)) {
    return raw;
  }

  const defMatch = raw.match(C_FUNC_DEF_RE);
  if (defMatch) {
    const name = defMatch[1];
    if (!C_KEYWORDS.has(name.toLowerCase())) {
      return name;
    }
  }

  for (const match of raw.matchAll(C_FUNC_CALL_RE)) {
    const name = match[1];
    if (!C_KEYWORDS.has(name.toLowerCase())) {
      return name;
    }
  }

  return undefined;
}

/**
 * Best-effort enclosing C function name for an arbitrary selected line/block
 * (PROJECT_SPEC v2.4 §4 — 선택 코드 변경 근거 조회 "포함 함수").
 *
 * Walks upward from `startLine` tracking unmatched `}` characters so nested
 * control blocks (if/for/while/switch/struct) are skipped and only the
 * function definition whose body brace directly encloses the selection is
 * returned. Best-effort only — returns `undefined` (never throws/guesses)
 * when the enclosing scope cannot be confidently determined (e.g. selection
 * is outside any function, or brace matching is inconclusive within the
 * scan window).
 */
export function findEnclosingFunctionSymbol(
  lines: string[],
  startLine: number
): string | undefined {
  if (!lines.length) {
    return undefined;
  }
  let pendingCloses = 0;
  const start = Math.min(Math.max(startLine, 0), lines.length - 1);
  const limit = Math.max(0, start - 4000);
  for (let i = start; i >= limit; i--) {
    const line = lines[i] ?? "";
    for (let ci = line.length - 1; ci >= 0; ci--) {
      const ch = line[ci];
      if (ch === "}") {
        pendingCloses++;
      } else if (ch === "{") {
        if (pendingCloses > 0) {
          pendingCloses--;
          continue;
        }
        // This brace directly opens the scope enclosing our position.
        // Two brace styles are common in this codebase:
        //   K&R:    `if (x) {`            — signature/keyword shares the line with `{`.
        //   Allman: `{` on its own line, signature on the previous line.
        const beforeBrace = line.slice(0, ci);
        const sigText = beforeBrace.trim() ? beforeBrace : findPrecedingNonBlankLine(lines, i) ?? "";
        if (/^\s*(if|for|while|switch)\b/.test(sigText)) {
          // Control-block brace — its own enclosing scope is one level up.
          continue;
        }
        const match = sigText.match(C_FUNC_DEF_RE);
        if (match && !C_KEYWORDS.has(match[1].toLowerCase())) {
          return match[1];
        }
        // Brace opens a non-function block (e.g. struct/else) we cannot
        // name — keep scanning upward for the real enclosing function.
      }
    }
  }
  return undefined;
}

/** Nearest non-blank line above `fromIndex`, used to resolve Allman-style `{` placement. */
function findPrecedingNonBlankLine(lines: string[], fromIndex: number): string | undefined {
  for (let j = fromIndex - 1; j >= 0 && j >= fromIndex - 5; j--) {
    const candidate = lines[j] ?? "";
    if (candidate.trim()) {
      return candidate;
    }
  }
  return undefined;
}

/**
 * Ensure the Backend search query includes the detected symbol.
 * Example: `이 함수 언제 추가되었어?` + `test_Alias` → `test_Alias 함수 언제 추가되었어?`
 */
export function augmentQueryWithSymbol(query: string, symbol: string | undefined): string {
  const q = (query ?? "").trim();
  if (!symbol || !q) {
    return q;
  }
  if (q.includes(symbol)) {
    return q;
  }

  const pronounReplaced = q.replace(/이\s*함수/g, `${symbol} 함수`);
  if (pronounReplaced !== q) {
    return pronounReplaced;
  }

  return `${symbol} ${q}`;
}
