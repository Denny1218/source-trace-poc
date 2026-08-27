export const PATH_COPY_SUCCESS_MESSAGE = "폴더 경로를 클립보드에 복사했습니다.";
export const PATH_COPY_FAILURE_MESSAGE =
  "폴더 경로를 복사하지 못했습니다. 경로 보기에서 직접 확인해 주세요.";

/**
 * Legacy DOM copy for HTTP / insecure contexts where Clipboard API is unavailable.
 * Always removes the temporary textarea in finally.
 */
export function copyTextViaLegacyExecCommand(text: string): boolean {
  if (typeof document === "undefined") return false;

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "0";
  textarea.style.width = "1px";
  textarea.style.height = "1px";
  textarea.style.padding = "0";
  textarea.style.border = "none";
  textarea.style.outline = "none";
  textarea.style.boxShadow = "none";
  textarea.style.background = "transparent";
  textarea.style.opacity = "0";

  document.body.appendChild(textarea);

  try {
    textarea.focus();
    textarea.select();
    textarea.setSelectionRange(0, text.length);
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    textarea.remove();
  }
}

/**
 * Copy text: Clipboard API first, then legacy execCommand fallback.
 * Returns true on either success path; false only when both fail or text is empty.
 */
export async function copyTextToClipboard(text: string): Promise<boolean> {
  const trimmed = text.trim();
  if (!trimmed) return false;

  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(trimmed);
      return true;
    } catch {
      // Fall through to legacy compatibility path (e.g. HTTP insecure context).
    }
  }

  return copyTextViaLegacyExecCommand(trimmed);
}
