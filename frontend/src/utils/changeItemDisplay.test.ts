import { describe, expect, it } from "vitest";
import type { ChangeItemCandidate } from "../api/pptCache";
import {
  countDistinctDocuments,
  formatApplicableScopes,
  formatMetaPrimaryLine,
  sortChangeItemCandidates,
} from "./changeItemDisplay";

function sampleItem(overrides: Partial<ChangeItemCandidate> = {}): ChangeItemCandidate {
  return {
    change_item_cache_id: 1,
    document_cache_id: 10,
    slide_no: 3,
    file_path: "\\\\server\\share\\doc.pptx",
    file_name: "doc.pptx",
    item_no: "1",
    change_title: "코레일 15분 재승차 허용기관 추가",
    csr_no: "SR260529_42025",
    business_background: null,
    current_status: null,
    as_is: null,
    to_be: null,
    source_functions: [],
    test_cases: [],
    applicable_scopes: ["9호선2,3단계", "진접", "우이신설", "신림"],
    matched_keywords: ["15분"],
    candidate_score: 75,
    ...overrides,
  };
}

describe("formatMetaPrimaryLine", () => {
  it("joins slide, item, csr with separator", () => {
    expect(formatMetaPrimaryLine(sampleItem())).toBe(
      "Slide 3 · 항목 1 · CSR SR260529_42025",
    );
  });

  it("omits csr when absent", () => {
    expect(formatMetaPrimaryLine(sampleItem({ csr_no: null }))).toBe("Slide 3 · 항목 1");
  });

  it("omits item when absent", () => {
    expect(formatMetaPrimaryLine(sampleItem({ item_no: null, csr_no: null }))).toBe("Slide 3");
  });
});

describe("formatApplicableScopes", () => {
  it("joins scopes with middle dot", () => {
    expect(formatApplicableScopes(["9호선2,3단계", "진접", "우이신설"])).toBe(
      "9호선2,3단계 · 진접 · 우이신설",
    );
  });

  it("returns null for empty scopes", () => {
    expect(formatApplicableScopes([])).toBeNull();
  });
});

describe("sortChangeItemCandidates", () => {
  it("sorts by score desc then file name", () => {
    const items = [
      sampleItem({ change_item_cache_id: 1, candidate_score: 35, file_name: "b.pptx" }),
      sampleItem({ change_item_cache_id: 2, candidate_score: 75, file_name: "a.pptx" }),
      sampleItem({ change_item_cache_id: 3, candidate_score: 75, file_name: "c.pptx", slide_no: 1 }),
    ];
    const sorted = sortChangeItemCandidates(items);
    expect(sorted.map((i) => i.change_item_cache_id)).toEqual([2, 3, 1]);
  });
});

describe("countDistinctDocuments", () => {
  it("counts unique document_cache_id without deduping change items", () => {
    const items = [
      sampleItem({ change_item_cache_id: 1, document_cache_id: 10 }),
      sampleItem({ change_item_cache_id: 2, document_cache_id: 10 }),
      sampleItem({ change_item_cache_id: 3, document_cache_id: 20 }),
    ];
    expect(countDistinctDocuments(items)).toBe(2);
    expect(items).toHaveLength(3);
  });
});

describe("regression: 영수증 / 15분 synthetic UI data", () => {
  it("15분 keyword item keeps title-first meta and scopes", () => {
    const item = sampleItem({
      change_title: "코레일 15분 재승차 허용기관 추가",
      matched_keywords: ["15분"],
      candidate_score: 75,
    });
    expect(formatMetaPrimaryLine(item)).toContain("Slide 3");
    expect(formatApplicableScopes(item.applicable_scopes)).toContain("진접");
  });

  it("영수증-style item without csr/scopes omits empty meta rows", () => {
    const item = sampleItem({
      change_title: "영수증 출력 조건 변경",
      csr_no: null,
      item_no: null,
      applicable_scopes: [],
      candidate_score: 40,
    });
    expect(formatMetaPrimaryLine(item)).toBe("Slide 3");
    expect(formatApplicableScopes(item.applicable_scopes)).toBeNull();
  });
});
