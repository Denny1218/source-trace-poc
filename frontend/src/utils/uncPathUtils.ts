/**
 * Windows UNC path helpers for parent-folder copy (Frontend only).
 * No file:// conversion — folder-open via browser is not supported in this POC.
 */

/** True when path is a UNC file or directory path (\\server\share\...). */
export function isUncPath(path: string): boolean {
  const normalized = path.trim().replace(/\//g, "\\");
  return normalized.startsWith("\\\\") && normalized.length > 2;
}

/**
 * Parent directory of a document full path.
 * Returns null for non-UNC, empty, malformed, or share-root-only paths.
 *
 * Example:
 *   \\server\share\folder1\folder2\doc.pptx
 *   → \\server\share\folder1\folder2
 */
export function getUncParentDirectory(documentPath: string): string | null {
  const trimmed = documentPath?.trim();
  if (!trimmed || !isUncPath(trimmed)) return null;

  const normalized = trimmed.replace(/\//g, "\\").replace(/\\+$/, "");
  const lastSep = normalized.lastIndexOf("\\");
  if (lastSep <= 1) return null;

  const parent = normalized.slice(0, lastSep);
  const segments = parent.slice(2).split("\\").filter(Boolean);
  // Require at least \\server\share (parent of a file inside a share).
  if (segments.length < 2) return null;

  return parent;
}
