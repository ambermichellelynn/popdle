import { useEffect, useState } from "react";
import "./App.css";
import { GameBoard } from "./components/GameBoard";
import { Onboarding } from "./components/Onboarding";
import { PaywallModal } from "./components/PaywallModal";
import { StatsPanel } from "./components/StatsPanel";
import { useUserId } from "./hooks/useUserId";
import { api } from "./api";

const STATS_KEY = "popdle_stats";

interface Stats {
  gamesPlayed: number;
  gamesWon: number;
  currentStreak: number;
  bestStreak: number;
  lastPlayedDate: string | null;
}

function loadStats(): Stats {
  const raw = localStorage.getItem(STATS_KEY);
  return raw
    ? JSON.parse(raw)
    : { gamesPlayed: 0, gamesWon: 0, currentStreak: 0, bestStreak: 0, lastPlayedDate: null };
}

function App() {
  const userId = useUserId();
  const [onboarded, setOnboarded] = useState(() => localStorage.getItem("popdle_onboarded") === "1");
  const [stats, setStats] = useState<Stats>(loadStats);
  const [showPaywall, setShowPaywall] = useState(false);

  useEffect(() => {
    api.ensureUser(userId).then(() => api.recordEvent(userId, "signup")).catch(() => {});
  }, [userId]);

  useEffect(() => {
    if (onboarded) api.recordEvent(userId, "game_started").catch(() => {});
  }, [onboarded, userId]);

  function handleOnboardingDone() {
    localStorage.setItem("popdle_onboarded", "1");
    setOnboarded(true);
  }

  function handleGameOver(won: boolean) {
    const today = new Date().toISOString().slice(0, 10);
    setStats((prev) => {
      const next: Stats = {
        gamesPlayed: prev.gamesPlayed + 1,
        gamesWon: prev.gamesWon + (won ? 1 : 0),
        currentStreak: won ? prev.currentStreak + 1 : 0,
        bestStreak: won ? Math.max(prev.bestStreak, prev.currentStreak + 1) : prev.bestStreak,
        lastPlayedDate: today,
      };
      localStorage.setItem(STATS_KEY, JSON.stringify(next));
      return next;
    });
  }

  function handlePaywallOpen() {
    api.recordEvent(userId, "paywall_viewed").catch(() => {});
    setShowPaywall(true);
  }

  function handleUpgrade() {
    api.recordEvent(userId, "upgraded").catch(() => {});
    setShowPaywall(false);
  }

  if (!onboarded) {
    return <Onboarding userId={userId} onDone={handleOnboardingDone} />;
  }

  return (
    <div className="app">
      <GameBoard userId={userId} onGameOver={handleGameOver} />
      <StatsPanel
        gamesPlayed={stats.gamesPlayed}
        gamesWon={stats.gamesWon}
        currentStreak={stats.currentStreak}
        bestStreak={stats.bestStreak}
        onUpgradeClick={handlePaywallOpen}
      />
      {showPaywall && (
        <PaywallModal onClose={() => setShowPaywall(false)} onUpgrade={handleUpgrade} />
      )}
    </div>
  );
}

export default App;
