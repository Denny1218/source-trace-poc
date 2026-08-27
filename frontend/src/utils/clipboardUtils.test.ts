import { afterEach, describe, expect, it, vi } from "vitest";
import {
  copyTextToClipboard,
  copyTextViaLegacyExecCommand,
  PATH_COPY_FAILURE_MESSAGE,
  PATH_COPY_SUCCESS_MESSAGE,
} from "./clipboardUtils";

type FakeTextarea = {
  value: string;
  style: Record<string, string>;
  setAttribute: ReturnType<typeof vi.fn>;
  focus: ReturnType<typeof vi.fn>;
  select: ReturnType<typeof vi.fn>;
  setSelectionRange: ReturnType<typeof vi.fn>;
  remove: ReturnType<typeof vi.fn>;
};

function stubLegacyDocument(execCommandImpl: () => boolean) {
  const textarea: FakeTextarea = {
    value: "",
    style: {},
    setAttribute: vi.fn(),
    focus: vi.fn(),
    select: vi.fn(),
    setSelectionRange: vi.fn(),
    remove: vi.fn(),
  };
  const appendChild = vi.fn();
  const execCommand = vi.fn(execCommandImpl);
  const createElement = vi.fn(() => textarea);

  vi.stubGlobal("document", {
    createElement,
    execCommand,
    body: { appendChild },
  });

  return { textarea, appendChild, createElement, execCommand };
}

describe("copyTextToClipboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns true when navigator.clipboard.writeText succeeds", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });

    await expect(copyTextToClipboard("\\\\server\\share\\doc.pptx")).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("\\\\server\\share\\doc.pptx");
  });

  it("uses legacy fallback when navigator.clipboard is missing", async () => {
    vi.stubGlobal("navigator", {});
    const { execCommand, textarea, appendChild } = stubLegacyDocument(() => true);

    await expect(copyTextToClipboard("\\\\server\\share\\doc.pptx")).resolves.toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(appendChild).toHaveBeenCalledWith(textarea);
    expect(textarea.remove).toHaveBeenCalled();
  });

  it("uses legacy fallback when writeText rejects", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("NotAllowedError"));
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    const { execCommand } = stubLegacyDocument(() => true);

    await expect(copyTextToClipboard("\\\\server\\share\\doc.pptx")).resolves.toBe(true);
    expect(writeText).toHaveBeenCalled();
    expect(execCommand).toHaveBeenCalledWith("copy");
  });

  it("returns true when execCommand copy succeeds via fallback", async () => {
    vi.stubGlobal("navigator", {});
    stubLegacyDocument(() => true);
    await expect(copyTextToClipboard("\\\\server\\share\\doc.pptx")).resolves.toBe(true);
  });

  it("returns false when execCommand copy fails", async () => {
    vi.stubGlobal("navigator", {});
    stubLegacyDocument(() => false);
    await expect(copyTextToClipboard("\\\\server\\share\\doc.pptx")).resolves.toBe(false);
  });

  it("returns false for empty string without calling clipboard", async () => {
    const writeText = vi.fn();
    vi.stubGlobal("navigator", { clipboard: { writeText } });

    await expect(copyTextToClipboard("   ")).resolves.toBe(false);
    expect(writeText).not.toHaveBeenCalled();
  });
});

describe("copyTextViaLegacyExecCommand", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns true when execCommand succeeds and removes textarea", () => {
    const { execCommand, textarea, appendChild } = stubLegacyDocument(() => true);

    expect(copyTextViaLegacyExecCommand("\\\\server\\share\\a.pptx")).toBe(true);
    expect(execCommand).toHaveBeenCalledWith("copy");
    expect(appendChild).toHaveBeenCalledWith(textarea);
    expect(textarea.remove).toHaveBeenCalledTimes(1);
    expect(textarea.value).toBe("\\\\server\\share\\a.pptx");
  });

  it("removes textarea even when execCommand fails", () => {
    const { textarea } = stubLegacyDocument(() => false);

    expect(copyTextViaLegacyExecCommand("\\\\server\\share\\a.pptx")).toBe(false);
    expect(textarea.remove).toHaveBeenCalledTimes(1);
  });

  it("removes textarea when execCommand throws", () => {
    const { textarea } = stubLegacyDocument(() => {
      throw new Error("copy blocked");
    });

    expect(copyTextViaLegacyExecCommand("\\\\server\\share\\a.pptx")).toBe(false);
    expect(textarea.remove).toHaveBeenCalledTimes(1);
  });
});

describe("path copy messages", () => {
  it("exposes user-facing success and failure copy", () => {
    expect(PATH_COPY_SUCCESS_MESSAGE).toBe("폴더 경로를 클립보드에 복사했습니다.");
    expect(PATH_COPY_FAILURE_MESSAGE).toBe(
      "폴더 경로를 복사하지 못했습니다. 경로 보기에서 직접 확인해 주세요.",
    );
  });
});

describe("folder path copy target", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("copies UNC parent folder, not full document path or file URL", async () => {
    const { getUncParentDirectory } = await import("./uncPathUtils");
    const full =
      "\\\\server\\share\\folder1\\folder2\\프로그램변경내역서_xxx.pptx";
    const parent = getUncParentDirectory(full);
    expect(parent).toBe("\\\\server\\share\\folder1\\folder2");

    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });

    await expect(copyTextToClipboard(parent!)).resolves.toBe(true);
    expect(writeText).toHaveBeenCalledWith("\\\\server\\share\\folder1\\folder2");
    expect(writeText).not.toHaveBeenCalledWith(full);
    expect(writeText.mock.calls[0][0]).not.toContain("file://");
    expect(writeText.mock.calls[0][0]).not.toContain(".pptx");
  });
});
