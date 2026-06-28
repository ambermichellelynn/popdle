import { useEffect, useState } from "react";
import { api, type ArchiveEntry } from "../api";
import { formatPuzzleDate } from "../lib/formatDate";

interface ArchivePageProps {
  userId: string;
  onSelectPuzzle: (wordDate: string) => void;
  onViewStats: () => void;
}

export function ArchivePage({ userId, onSelectPuzzle, onViewStats }: ArchivePageProps) {
  const [entries, setEntries] = useState<ArchiveEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getArchive(userId).then(setEntries).catch((e) => setError(e.message));
  }, [userId]);

  return (
    <div className="archive-page">
      <div className="archive-page-header">
        <button className="stats-link" onClick={onViewStats}>
          View stats
        </button>
      </div>
      <h2>Archive</h2>
      <p className="archive-subtitle">The last 20 puzzles.</p>

      {error && <p className="error">{error}</p>}
      {!entries && !error && <p className="loading">Loading…</p>}

      <div className="archive-list">
        {entries?.map((entry) => (
          <button key={entry.word_date} className="archive-row" onClick={() => onSelectPuzzle(entry.word_date)}>
            <span className="played-check-slot">
              {entry.played && (
                <span className="played-check" aria-label="Already played">
                  ✓
                </span>
              )}
            </span>
            <span className="archive-date">{formatPuzzleDate(entry.word_date)}</span>
            <span className="archive-clue">{entry.clue}</span>
            <span className="archive-status">
              {!entry.played
                ? "Play"
                : !entry.game_over
                  ? "Continue"
                  : entry.won
                    ? "Won"
                    : "Lost"}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
