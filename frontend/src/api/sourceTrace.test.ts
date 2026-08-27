import { describe, expect, it } from "vitest";
import {
  buildTraceReportRequest,
  buildTraceSelectionRequest,
  getRepositorySelectionState,
  mapSourceTraceErrorMessage,
} from "./sourceTrace";

describe("buildTraceReportRequest", () => {
  it("builds report request from manual function query fields", () => {
    expect(
      buildTraceReportRequest({
        equipmentId: 7,
        filePath: "src\\fare\\file_save_mgt.c",
        functionName: " file_close_init ",
      }),
    ).toEqual({
      equipment_id: 7,
      query: "선택한 코드가 왜 변경됐는지 알려줘",
      file_path: "src/fare/file_save_mgt.c",
      selected_code: "file_close_init",
      detected_symbol: "file_close_init",
      source_mode: "cursor_word",
      use_ollama: false,
    });
  });
});

describe("buildTraceSelectionRequest", () => {
  it("builds selection request with repo hint and normalized relative path", () => {
    expect(
      buildTraceSelectionRequest({
        equipmentId: 3,
        repositoryId: 11,
        filePath: "\\Fare\\src\\fare_calc.c",
        startLine: 21,
        endLine: 24,
        selectedCode: " return fare; ",
        enclosingSymbol: " fare_is_xfer ",
      }),
    ).toEqual({
      equipment_id: 3,
      repo_relative_path: "Fare/src/fare_calc.c",
      repo_id_hint: 11,
      start_line: 21,
      end_line: 24,
      selected_code: "return fare;",
      enclosing_symbol: "fare_is_xfer",
      revision: "HEAD",
    });
  });
});

describe("getRepositorySelectionState", () => {
  it("marks a single repository as auto-selectable", () => {
    expect(
      getRepositorySelectionState([
        {
          id: 1,
          equipment_id: 1,
          name: "repo-a",
          source_type: "local",
          repository_url: null,
          canonical_repository_url: null,
          yona_username: null,
          local_path: "c:/repo-a",
          status: "ready",
          created_at: "",
          updated_at: "",
        },
      ]),
    ).toEqual({
      hasSingleRepository: true,
      requiresExplicitChoice: false,
    });
  });
});

describe("mapSourceTraceErrorMessage", () => {
  it("maps network failures to a simple user-facing message", () => {
    expect(mapSourceTraceErrorMessage(new Error("Failed to fetch"))).toBe(
      "서버에 연결할 수 없습니다.",
    );
  });

  it("maps repository ambiguity errors", () => {
    expect(mapSourceTraceErrorMessage(new Error("repo_relative_path가 필요합니다."))).toBe(
      "Repository를 특정할 수 없습니다.",
    );
  });
});
