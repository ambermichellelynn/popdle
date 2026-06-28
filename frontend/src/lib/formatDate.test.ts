import { describe, expect, it } from "vitest";
import { formatPuzzleDate } from "./formatDate";

describe("formatPuzzleDate", () => {
  it("does not shift the date backward regardless of local timezone", () => {
    // The classic bug: new Date("2026-06-28") parses as UTC midnight, then
    // .toLocaleDateString() converts to local time — showing "Jun 27" for
    // any timezone behind UTC (e.g. EDT). This must always show Jun 28.
    expect(formatPuzzleDate("2026-06-28")).toBe("Jun 28");
  });

  it("handles single-digit days and months correctly", () => {
    expect(formatPuzzleDate("2026-01-05")).toBe("Jan 5");
  });

  it("handles the last day of the year", () => {
    expect(formatPuzzleDate("2026-12-31")).toBe("Dec 31");
  });
});
