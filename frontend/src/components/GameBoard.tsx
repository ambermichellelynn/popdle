import { useEffect, useState } from "react";
import { api, type GuessResult, type TodayPuzzle } from "../api";

interface GameBoardProps {
  userId: string;
  onGameOver: (won: boolean) => void;
}

export function GameBoard({ userId, onGameOver }: GameBoardProps) {
  const [puzzle, setPuzzle] = useState<TodayPuzzle | null>(null);
  const [currentGuess, setCurrentGuess] = useState("");
  const [history, setHistory] = useState<GuessResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    api.getToday().then(setPuzzle).catch((e) => setError(e.message));
  }, []);

  if (!puzzle) return <div>Loading today's puzzle...</div>;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const result = await api.submitGuess(userId, currentGuess);
      setHistory((h) => [...h, result]);
      setCurrentGuess("");
      if (result.game_over) {
        setFinished(true);
        if (result.won) await api.recordEvent(userId, "game_won");
        onGameOver(result.won);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="game-board">
      <p className="clue">
        {puzzle.category.toUpperCase()} · {puzzle.clue}
      </p>
      <div className="rows">
        {history.map((result, idx) => (
          <div key={idx} className="row">
            {result.guess.split("").map((letter, i) => {
              const status = result.correct_positions.includes(i)
                ? "correct"
                : result.present_letters.includes(i)
                  ? "present"
                  : "absent";
              return (
                <span key={i} className={`tile ${status}`}>
                  {letter}
                </span>
              );
            })}
          </div>
        ))}
      </div>

      {!finished && (
        <form onSubmit={handleSubmit}>
          <input
            value={currentGuess}
            onChange={(e) => setCurrentGuess(e.target.value.toUpperCase())}
            maxLength={puzzle.word_length}
            minLength={puzzle.word_length}
            placeholder={`${puzzle.word_length}-letter word`}
            autoFocus
          />
          <button type="submit">Guess</button>
        </form>
      )}

      {finished && history.length > 0 && (
        <p className="result-banner">
          {history[history.length - 1].won
            ? `You got it! The answer was ${history[history.length - 1].answer}.`
            : `Out of guesses. The answer was ${history[history.length - 1].answer}.`}
        </p>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  );
}
