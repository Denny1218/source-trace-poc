import { describe, expect, it } from "vitest";
import {
  getRelevanceLabel,
  getRelevanceLevel,
  RELEVANCE_HIGH_MIN,
  RELEVANCE_MEDIUM_MIN,
} from "./changeItemRelevance";

describe("getRelevanceLevel", () => {
  it("maps high boundary and above to high", () => {
    expect(getRelevanceLevel(RELEVANCE_HIGH_MIN)).toBe("high");
    expect(getRelevanceLevel(105)).toBe("high");
    expect(getRelevanceLevel(140)).toBe("high");
  });

  it("maps just below high boundary to medium", () => {
    expect(getRelevanceLevel(RELEVANCE_HIGH_MIN - 1)).toBe("medium");
    expect(getRelevanceLevel(69)).toBe("medium");
  });

  it("maps medium boundary and above to medium", () => {
    expect(getRelevanceLevel(RELEVANCE_MEDIUM_MIN)).toBe("medium");
    expect(getRelevanceLevel(35)).toBe("medium");
    expect(getRelevanceLevel(45)).toBe("medium");
  });

  it("maps just below medium boundary to low", () => {
    expect(getRelevanceLevel(RELEVANCE_MEDIUM_MIN - 1)).toBe("low");
    expect(getRelevanceLevel(10)).toBe("low");
    expect(getRelevanceLevel(20)).toBe("low");
  });
});

describe("getRelevanceLabel", () => {
  it("returns Korean labels with text (not color-only)", () => {
    expect(getRelevanceLabel(105)).toBe("관련도 높음");
    expect(getRelevanceLabel(45)).toBe("관련도 보통");
    expect(getRelevanceLabel(10)).toBe("관련도 낮음");
  });
});
