import { describe, expect, it } from "vitest";
import { fmt, pct, relativeTime, shortDate } from "./utils";

describe("formatting helpers", () => {
  it("formats numbers with separators", () => {
    expect(fmt(1234567)).toBe("1,234,567");
    expect(fmt(null)).toBe("—");
    expect(fmt(undefined)).toBe("—");
  });

  it("formats percentages with one decimal", () => {
    expect(pct(97.13)).toBe("97.1%");
    expect(pct(50)).toBe("50%");
  });

  it("renders short dates", () => {
    const result = shortDate("2026-08-03T12:00:00Z");
    expect(result).toMatch(/Aug/);
    expect(result).toMatch(/3/);
  });

  it("reports relative time", () => {
    expect(relativeTime(null)).toBe("never");
    const now = new Date().toISOString();
    expect(relativeTime(now)).toBe("today");
  });
});
