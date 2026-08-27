import { describe, expect, it } from "vitest";
import { getUncParentDirectory, isUncPath } from "./uncPathUtils";

describe("isUncPath", () => {
  it("accepts standard UNC", () => {
    expect(isUncPath("\\\\server\\share\\folder\\doc.pptx")).toBe(true);
  });

  it("rejects local and empty paths", () => {
    expect(isUncPath("C:\\folder\\doc.pptx")).toBe(false);
    expect(isUncPath("")).toBe(false);
    expect(isUncPath("   ")).toBe(false);
  });
});

describe("getUncParentDirectory", () => {
  it("returns parent for basic UNC full file path", () => {
    expect(
      getUncParentDirectory(
        "\\\\server\\share\\folder1\\folder2\\프로그램변경내역서_xxx.pptx",
      ),
    ).toBe("\\\\server\\share\\folder1\\folder2");
  });

  it("handles multiple nested folders", () => {
    expect(getUncParentDirectory("//server/share/a/b/c/file.pptx")).toBe(
      "\\\\server\\share\\a\\b\\c",
    );
  });

  it("handles Korean folders and spaces", () => {
    expect(
      getUncParentDirectory("\\\\server\\공유\\변경 내역\\2024 문서\\보고서.pptx"),
    ).toBe("\\\\server\\공유\\변경 내역\\2024 문서");
  });

  it("handles space in filename", () => {
    expect(getUncParentDirectory("\\\\server\\share\\sub\\AG 변경 내역.pptx")).toBe(
      "\\\\server\\share\\sub",
    );
  });

  it("handles Korean filename", () => {
    expect(
      getUncParentDirectory("\\\\server\\share\\docs\\프로그램변경내역서.pptx"),
    ).toBe("\\\\server\\share\\docs");
  });

  it("returns null for local path", () => {
    expect(getUncParentDirectory("C:\\data\\doc.pptx")).toBeNull();
    expect(getUncParentDirectory("D:\\data\\doc.pptx")).toBeNull();
    expect(getUncParentDirectory("Z:\\mapped\\doc.pptx")).toBeNull();
  });

  it("returns null for empty, invalid, and share-root only", () => {
    expect(getUncParentDirectory("")).toBeNull();
    expect(getUncParentDirectory("\\\\server\\share")).toBeNull();
    expect(getUncParentDirectory("invalid")).toBeNull();
  });

  it("does not return file:// or filename-only", () => {
    const parent = getUncParentDirectory(
      "\\\\server\\share\\folder\\프로그램변경내역서.pptx",
    );
    expect(parent).toBe("\\\\server\\share\\folder");
    expect(parent).not.toContain("file://");
    expect(parent).not.toContain(".pptx");
  });
});
