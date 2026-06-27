import { describe, expect, it } from "vitest";
import type { GuessResult } from "../api";
import { computeLetterStatus } from "./letterStatus";

function guess(overrides: Partial<GuessResult>): GuessResult {
  return {
    guess: "",
    correct_positions: [],
    present_letters: [],
    won: false,
    attempts_used: 1,
    game_over: false,
    answer: null,
    ...overrides,
  };
}

describe("computeLetterStatus", () => {
  it("returns an empty map for no history", () => {
    expect(computeLetterStatus([])).toEqual({});
  });

  it("marks correct, present, and absent letters from a single guess", () => {
    const status = computeLetterStatus([
      guess({ guess: "SHREK", correct_positions: [0, 1], present_letters: [2] }),
    ]);
    expect(status.S).toBe("correct");
    expect(status.H).toBe("correct");
    expect(status.R).toBe("present");
    expect(status.E).toBe("absent");
    expect(status.K).toBe("absent");
  });

  it("upgrades a letter from absent to present across guesses", () => {
    const status = computeLetterStatus([
      guess({ guess: "AXXXX", correct_positions: [], present_letters: [] }),
      guess({ guess: "XXXXA", correct_positions: [], present_letters: [4] }),
    ]);
    expect(status.A).toBe("present");
  });

  it("upgrades a letter from present to correct across guesses", () => {
    const status = computeLetterStatus([
      guess({ guess: "AXXXX", correct_positions: [], present_letters: [0] }),
      guess({ guess: "XXXXA", correct_positions: [4], present_letters: [] }),
    ]);
    expect(status.A).toBe("correct");
  });

  it("never downgrades a letter once marked correct", () => {
    // Same letter shows up "correct" first, then a later guess scores that
    // letter as merely "present" or "absent" elsewhere — must stay correct.
    const status = computeLetterStatus([
      guess({ guess: "AXXXX", correct_positions: [0], present_letters: [] }),
      guess({ guess: "XXXXA", correct_positions: [], present_letters: [] }),
    ]);
    expect(status.A).toBe("correct");
  });

  it("never downgrades a letter from present back to absent", () => {
    const status = computeLetterStatus([
      guess({ guess: "AXXXX", correct_positions: [], present_letters: [0] }),
      guess({ guess: "XXXXA", correct_positions: [], present_letters: [] }),
    ]);
    expect(status.A).toBe("present");
  });

  it("handles repeated letters within the same guess independently per position", () => {
    // Real backend scoring only marks as many positions present as the
    // answer's letter count allows, but the keyboard status should still
    // reflect the best (highest) status seen for that letter.
    const status = computeLetterStatus([
      guess({ guess: "TOTTI", correct_positions: [], present_letters: [0] }),
    ]);
    expect(status.T).toBe("present");
    expect(status.O).toBe("absent");
    expect(status.I).toBe("absent");
  });
});
