import type { GuessResult } from "../api";

export type LetterStatus = "correct" | "present" | "absent";

/**
 * Aggregates per-letter keyboard status across all guesses so far. A letter's
 * status can only improve (absent -> present -> correct), never regress —
 * e.g. if "E" was present in one guess but absent in another, it must stay
 * "present" on the keyboard, not flip back to "absent".
 */
export function computeLetterStatus(history: GuessResult[]): Record<string, LetterStatus> {
  const letterStatus: Record<string, LetterStatus> = {};

  for (const result of history) {
    result.guess.split("").forEach((letter, i) => {
      const status: LetterStatus = result.correct_positions.includes(i)
        ? "correct"
        : result.present_letters.includes(i)
          ? "present"
          : "absent";
      const existing = letterStatus[letter];
      if (!existing || status === "correct" || (status === "present" && existing === "absent")) {
        letterStatus[letter] = status;
      }
    });
  }

  return letterStatus;
}
