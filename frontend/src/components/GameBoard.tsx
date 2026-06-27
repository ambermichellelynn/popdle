import { useEffect, useState } from "react";
import { api, type GuessResult, type TodayPuzzle } from "../api";
import { computeLetterStatus, type LetterStatus } from "../lib/letterStatus";
import { Confetti } from "./Confetti";

interface GameBoardProps {
  userId: string;
  onGameOver?: (won: boolean) => void;
  wordDate?: string;
}

const MAX_ATTEMPTS = 6;
const KEYBOARD_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"];

export function GameBoard({ userId, onGameOver, wordDate }: GameBoardProps) {
  const [puzzle, setPuzzle] = useState<TodayPuzzle | null>(null);
  const [currentGuess, setCurrentGuess] = useState("");
  const [history, setHistory] = useState<GuessResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [finished, setFinished] = useState(false);
  const [won, setWon] = useState(false);
  const [finalAnswer, setFinalAnswer] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [justFlipped, setJustFlipped] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    setPuzzle(null);
    setHistory([]);
    setFinished(false);
    setError(null);

    api
      .getToday(userId, wordDate)
      .then((p) => {
        setPuzzle(p);
        setHistory(p.history);
        setFinished(p.game_over);
        setFinalAnswer(p.answer);
        if (p.history.length > 0) setWon(p.history[p.history.length - 1].won && p.game_over);
      })
      .catch((e) => setError(e.message));
  }, [userId, wordDate]);

  const wordLength = puzzle?.word_length ?? 5;

  async function submitGuess(guess: string) {
    if (!puzzle || guess.length !== wordLength || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const result = await api.submitGuess(userId, guess, wordDate);
      setHistory((h) => [...h, result]);
      setCurrentGuess("");
      setJustFlipped(true);
      setTimeout(() => setJustFlipped(false), 600);
      if (result.game_over) {
        setFinished(true);
        setWon(result.won);
        setFinalAnswer(result.answer);
        if (result.won) {
          setShowConfetti(true);
          await api.recordEvent(userId, "game_won");
        }
        onGameOver?.(result.won);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  const letterStatus = computeLetterStatus(history);

  useEffect(() => {
    if (!puzzle || finished) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Enter") {
        if (currentGuess.length === wordLength) void submitGuess(currentGuess);
        return;
      }
      if (e.key === "Backspace") {
        setCurrentGuess((g) => g.slice(0, -1));
        return;
      }
      if (typeof e.key !== "string") return;
      const letter = e.key.toUpperCase();
      if (
        /^[A-Z]$/.test(letter) &&
        currentGuess.length < wordLength &&
        letterStatus[letter] !== "absent"
      ) {
        setCurrentGuess((g) => (g + letter).slice(0, wordLength));
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puzzle, finished, currentGuess, wordLength, letterStatus]);

  function handleKeyClick(key: string) {
    if (finished) return;
    if (key === "ENTER") {
      if (currentGuess.length === wordLength) void submitGuess(currentGuess);
    } else if (key === "BACK") {
      setCurrentGuess((g) => g.slice(0, -1));
    } else if (currentGuess.length < wordLength && letterStatus[key] !== "absent") {
      setCurrentGuess((g) => g + key);
    }
  }

  if (error && !puzzle) return <p className="error">{error}</p>;
  if (!puzzle) return <div className="loading">Loading today's puzzle…</div>;

  const rows: (GuessResult | null)[] = [...history];
  while (rows.length < MAX_ATTEMPTS) rows.push(null);

  return (
    <div className="game-board">
      <Confetti active={showConfetti} />

      <div className="puzzle-header">
        <span className="category-badge">{puzzle.category.toUpperCase()}</span>
        <p className="clue">{puzzle.clue}</p>
      </div>

      <div className="board-grid">
        {rows.map((result, rowIdx) => {
          const isCurrentRow = rowIdx === history.length && !finished;
          const isJustSubmittedRow = rowIdx === history.length - 1 && justFlipped;
          const letters = result
            ? result.guess.split("")
            : isCurrentRow
              ? currentGuess.padEnd(wordLength).split("")
              : Array(wordLength).fill("");

          return (
            <div className={`row ${isJustSubmittedRow ? "row-flip" : ""}`} key={rowIdx}>
              {letters.map((letter, i) => {
                let status: LetterStatus | "empty" | "filled" = "empty";
                if (result) {
                  status = result.correct_positions.includes(i)
                    ? "correct"
                    : result.present_letters.includes(i)
                      ? "present"
                      : "absent";
                } else if (letter.trim()) {
                  status = "filled";
                }
                return (
                  <span
                    key={i}
                    className={`tile ${status}`}
                    style={isJustSubmittedRow ? { animationDelay: `${i * 80}ms` } : undefined}
                  >
                    {letter.trim()}
                  </span>
                );
              })}
            </div>
          );
        })}
      </div>

      {!finished && (
        <div className="keyboard">
          {KEYBOARD_ROWS.map((row, i) => (
            <div className="keyboard-row" key={i}>
              {i === 2 && (
                <button className="key key-wide" onClick={() => handleKeyClick("ENTER")}>
                  Enter
                </button>
              )}
              {row.split("").map((key) => (
                <button
                  key={key}
                  className={`key ${letterStatus[key] ?? ""}`}
                  onClick={() => handleKeyClick(key)}
                  disabled={letterStatus[key] === "absent"}
                >
                  {key}
                </button>
              ))}
              {i === 2 && (
                <button className="key key-wide" onClick={() => handleKeyClick("BACK")}>
                  ⌫
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {finished && (
        <p className="result-banner">
          {won ? `Solved in ${history.length} ${history.length === 1 ? "guess" : "guesses"}.` : "Not today."}
          {finalAnswer && <span className="result-answer"> The word was {finalAnswer}.</span>}
        </p>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
