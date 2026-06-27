import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { GuessResult, TodayPuzzle } from "../api";
import { api } from "../api";
import { GameBoard } from "./GameBoard";

vi.mock("../api", () => ({
  api: {
    getToday: vi.fn(),
    submitGuess: vi.fn(),
    recordEvent: vi.fn(),
  },
}));

const basePuzzle: TodayPuzzle = {
  word_date: "2026-06-27",
  category: "movie",
  clue: "Green ogre, big personality",
  word_length: 5,
  history: [],
  game_over: false,
  answer: null,
  is_archive: false,
};

function makeGuessResult(overrides: Partial<GuessResult>): GuessResult {
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

describe("GameBoard", () => {
  beforeEach(() => {
    vi.mocked(api.recordEvent).mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays today's puzzle clue and category", async () => {
    vi.mocked(api.getToday).mockResolvedValue(basePuzzle);

    render(<GameBoard userId="user-1" />);

    expect(screen.getByText(/loading today's puzzle/i)).toBeInTheDocument();
    expect(await screen.findByText("Green ogre, big personality")).toBeInTheDocument();
    expect(screen.getByText("MOVIE")).toBeInTheDocument();
  });

  it("types letters via the on-screen keyboard and submits on Enter", async () => {
    vi.mocked(api.getToday).mockResolvedValue(basePuzzle);
    vi.mocked(api.submitGuess).mockResolvedValue(
      makeGuessResult({ guess: "BLIMP", correct_positions: [], present_letters: [] }),
    );

    const user = userEvent.setup();
    render(<GameBoard userId="user-1" />);
    await screen.findByText("Green ogre, big personality");

    for (const letter of "BLIMP") {
      await user.click(screen.getByRole("button", { name: letter }));
    }
    await user.click(screen.getByRole("button", { name: "Enter" }));

    await waitFor(() => expect(api.submitGuess).toHaveBeenCalledWith("user-1", "BLIMP", undefined));
  });

  it("colors tiles correct/present/absent based on the guess result", async () => {
    vi.mocked(api.getToday).mockResolvedValue(basePuzzle);
    vi.mocked(api.submitGuess).mockResolvedValue(
      makeGuessResult({ guess: "SHREK", correct_positions: [0, 1], present_letters: [2] }),
    );

    render(<GameBoard userId="user-1" />);
    await screen.findByText("Green ogre, big personality");

    for (const letter of "SHREK") {
      fireEvent.keyDown(window, { key: letter });
    }
    fireEvent.keyDown(window, { key: "Enter" });

    await waitFor(() => expect(api.submitGuess).toHaveBeenCalled());

    const tiles = await screen.findAllByText(/^[SHREK]$/);
    const tileClasses = tiles.map((t) => t.className);
    expect(tileClasses[0]).toContain("correct");
    expect(tileClasses[1]).toContain("correct");
    expect(tileClasses[2]).toContain("present");
    expect(tileClasses[3]).toContain("absent");
    expect(tileClasses[4]).toContain("absent");
  });

  it("disables a keyboard key once that letter is marked absent", async () => {
    vi.mocked(api.getToday).mockResolvedValue(basePuzzle);
    vi.mocked(api.submitGuess).mockResolvedValue(
      makeGuessResult({ guess: "BLIMP", correct_positions: [], present_letters: [] }),
    );

    const user = userEvent.setup();
    render(<GameBoard userId="user-1" />);
    await screen.findByText("Green ogre, big personality");

    for (const letter of "BLIMP") {
      await user.click(screen.getByRole("button", { name: letter }));
    }
    await user.click(screen.getByRole("button", { name: "Enter" }));

    await waitFor(() => expect(screen.getByRole("button", { name: "B" })).toBeDisabled());
  });

  it("shows the win banner and hides the keyboard once the game is over", async () => {
    vi.mocked(api.getToday).mockResolvedValue(basePuzzle);
    vi.mocked(api.submitGuess).mockResolvedValue(
      makeGuessResult({
        guess: "SHREK",
        correct_positions: [0, 1, 2, 3, 4],
        won: true,
        game_over: true,
        answer: "SHREK",
      }),
    );

    const onGameOver = vi.fn();
    const user = userEvent.setup();
    render(<GameBoard userId="user-1" onGameOver={onGameOver} />);
    await screen.findByText("Green ogre, big personality");

    for (const letter of "SHREK") {
      await user.click(screen.getByRole("button", { name: letter }));
    }
    await user.click(screen.getByRole("button", { name: "Enter" }));

    expect(await screen.findByText(/solved in 1 guess/i)).toBeInTheDocument();
    expect(screen.getByText(/the word was shrek/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Enter" })).not.toBeInTheDocument();
    expect(onGameOver).toHaveBeenCalledWith(true);
  });

  it("resumes an in-progress game from puzzle history without re-submitting", async () => {
    vi.mocked(api.getToday).mockResolvedValue({
      ...basePuzzle,
      history: [makeGuessResult({ guess: "BLIMP", correct_positions: [], present_letters: [] })],
      game_over: false,
    });

    const { container } = render(<GameBoard userId="user-1" />);

    await waitFor(() => {
      const filledTiles = Array.from(container.querySelectorAll(".tile")).filter(
        (el) => el.textContent?.trim().length,
      );
      expect(filledTiles.map((el) => el.textContent)).toEqual(["B", "L", "I", "M", "P"]);
    });
    expect(api.submitGuess).not.toHaveBeenCalled();
  });
});
