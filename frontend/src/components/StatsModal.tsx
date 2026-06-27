import { useEffect, useState } from "react";
import { api, type HistoryEntry } from "../api";

interface StatsModalProps {
  userId: string;
  gamesPlayed: number;
  gamesWon: number;
  currentStreak: number;
  bestStreak: number;
  onClose: () => void;
}

export function StatsModal({
  userId,
  gamesPlayed,
  gamesWon,
  currentStreak,
  bestStreak,
  onClose,
}: StatsModalProps) {
  const winRate = gamesPlayed > 0 ? Math.round((gamesWon / gamesPlayed) * 100) : 0;
  const [history, setHistory] = useState<HistoryEntry[] | null>(null);

  useEffect(() => {
    api.getHistory(userId).then(setHistory).catch(() => setHistory([]));
  }, [userId]);

  const distribution = [0, 0, 0, 0, 0, 0];
  history?.forEach((entry) => {
    if (entry.won && entry.attempts_used >= 1 && entry.attempts_used <= 6) {
      distribution[entry.attempts_used - 1] += 1;
    }
  });
  const maxCount = Math.max(1, ...distribution);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal stats-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-x" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h2>Statistics</h2>

        <div className="stats-grid">
          <Stat label="Played" value={gamesPlayed} />
          <Stat label="Win %" value={`${winRate}%`} />
          <Stat label="Streak" value={currentStreak} />
          <Stat label="Best" value={bestStreak} />
        </div>

        {history && (
          <>
            <h3 className="history-heading">Guess distribution</h3>
            <div className="distribution-chart">
              {distribution.map((count, i) => (
                <div className="distribution-row" key={i}>
                  <span className="distribution-label">{i + 1}</span>
                  <div className="distribution-bar-track">
                    <div
                      className="distribution-bar"
                      style={{ width: `${(count / maxCount) * 100}%` }}
                    >
                      <span className="distribution-count">{count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <h3 className="history-heading">History</h3>
        {!history && <p className="loading">Loading…</p>}
        {history && history.length === 0 && <p className="history-empty">No past games yet.</p>}
        <div className="history-list">
          {history?.map((entry) => (
            <div key={entry.word_date} className="history-row">
              <span className="history-date">
                {new Date(entry.word_date).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </span>
              <span className="history-answer">{entry.answer ?? "In progress"}</span>
              <span className="history-result">{entry.won ? "Won" : entry.game_over ? "Lost" : "—"}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
