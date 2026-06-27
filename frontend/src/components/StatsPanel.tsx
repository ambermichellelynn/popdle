interface StatsPanelProps {
  gamesPlayed: number;
  gamesWon: number;
  currentStreak: number;
  bestStreak: number;
  onUpgradeClick: () => void;
}

export function StatsPanel({
  gamesPlayed,
  gamesWon,
  currentStreak,
  bestStreak,
  onUpgradeClick,
}: StatsPanelProps) {
  const winRate = gamesPlayed > 0 ? Math.round((gamesWon / gamesPlayed) * 100) : 0;

  return (
    <div className="stats-panel">
      <h2>Your record</h2>
      <div className="stats-grid">
        <Stat label="Played" value={gamesPlayed} />
        <Stat label="Win %" value={winRate} />
        <Stat label="Streak" value={currentStreak} />
        <Stat label="Best" value={bestStreak} />
      </div>
      <button className="upgrade-btn" onClick={onUpgradeClick}>
        See full stats history with Premium
      </button>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
