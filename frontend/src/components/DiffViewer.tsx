const BINARY_PLACEHOLDER = "[binary file]";

export type DiffLineType =
  | "file-header"
  | "hunk"
  | "added"
  | "deleted"
  | "context"
  | "binary";

export function classifyDiffLine(line: string): DiffLineType {
  if (line.startsWith("+++ ") || line.startsWith("--- ")) return "file-header";
  if (line.startsWith("@@")) return "hunk";
  if (line.startsWith("+")) return "added";
  if (line.startsWith("-")) return "deleted";
  if (line.startsWith(" ")) return "context";
  return "context";
}

export function isBinaryDiff(diff: string | null | undefined): boolean {
  return diff === BINARY_PLACEHOLDER;
}

export function shortenHash(hash: string, length = 7): string {
  return hash.length > length ? hash.slice(0, length) : hash;
}

export function formatCommitDate(iso: string): string {
  return iso.replace("T", " ").replace("+00:00", " UTC").slice(0, 19);
}

interface DiffViewerProps {
  diff: string | null;
}

export default function DiffViewer({ diff }: DiffViewerProps) {
  if (isBinaryDiff(diff)) {
    return (
      <div className="diff-binary-notice">
        Binary 파일 변경입니다.
        <br />
        내용 Diff는 저장하지 않습니다.
      </div>
    );
  }

  if (!diff || !diff.trim()) {
    return <div className="diff-empty">Diff 내용이 없습니다.</div>;
  }

  const lines = diff.split("\n");

  return (
    <pre className="diff-viewer">
      {lines.map((line, idx) => (
        <div key={idx} className={`diff-line diff-${classifyDiffLine(line)}`}>
          {line || " "}
        </div>
      ))}
    </pre>
  );
}
