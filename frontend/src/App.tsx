import { useEffect, useState } from "react";
import "./App.css";
import { ArchivePage } from "./components/ArchivePage";
import { GameBoard } from "./components/GameBoard";
import { PaywallModal } from "./components/PaywallModal";
import { StatsModal } from "./components/StatsModal";
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

type View = "game" | "archive" | "archive-puzzle";

function loadStats(): Stats {
  const raw = localStorage.getItem(STATS_KEY);
  return raw
    ? JSON.parse(raw)
    : { gamesPlayed: 0, gamesWon: 0, currentStreak: 0, bestStreak: 0, lastPlayedDate: null };
}

function isAnonymousEmail(email: string | null): boolean {
  return !email || email.endsWith("@anon.popdle.local");
}

function App() {
  const [userId, setUserId] = useUserId();
  const [stats, setStats] = useState<Stats>(loadStats);
  const [showPaywall, setShowPaywall] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"upgrade" | "account">("upgrade");
  const [isPremium, setIsPremium] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [checkoutNotice, setCheckoutNotice] = useState<string | null>(null);
  const [view, setView] = useState<View>("game");
  const [archivePuzzleDate, setArchivePuzzleDate] = useState<string | null>(null);

  useEffect(() => {
    api
      .ensureUser(userId)
      .then((user) => {
        setIsPremium(user.is_premium);
        setUserEmail(user.email);
        return api.recordEvent(userId, "signup");
      })
      .catch(() => {});
  }, [userId]);

  useEffect(() => {
    api.recordEvent(userId, "game_started").catch(() => {});
  }, [userId]);

  // Handle the redirect back from Stripe Checkout (?checkout=success&session_id=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const checkout = params.get("checkout");
    const sessionId = params.get("session_id");

    if (checkout === "success" && sessionId) {
      api
        .confirmCheckout(userId, sessionId)
        .then(() => {
          setIsPremium(true);
          api.recordEvent(userId, "upgraded").catch(() => {});
          setCheckoutNotice("You're Premium. Stats and the archive are unlocked.");
        })
        .catch(() => setCheckoutNotice("We couldn't confirm that checkout — please try again."));
    } else if (checkout === "cancel") {
      setCheckoutNotice("Checkout canceled — no charge was made.");
    }

    if (checkout) {
      window.history.replaceState({}, "", window.location.pathname);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Toast notices auto-dismiss after a few seconds instead of sticking around forever.
  useEffect(() => {
    if (!checkoutNotice) return;
    const timeout = setTimeout(() => setCheckoutNotice(null), 4000);
    return () => clearTimeout(timeout);
  }, [checkoutNotice]);

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
    setAuthModalMode("upgrade");
    setShowPaywall(true);
  }

  function handleSignInOpen() {
    setAuthModalMode("account");
    setShowPaywall(true);
  }

  function handleSignOut() {
    const newId = crypto.randomUUID();
    setUserId(newId);
    setIsPremium(false);
    setUserEmail(null);
    setView("game");
    setArchivePuzzleDate(null);
  }

  async function handleLoggedIn(newUserId: string) {
    setUserId(newUserId);
    try {
      const user = await api.ensureUser(newUserId);
      setIsPremium(user.is_premium);
      setUserEmail(user.email);
    } catch {
      // ignore — UI will reconcile on next ensureUser call
    }
  }

  function handleStatsClick() {
    if (isPremium) {
      setShowStats(true);
    } else {
      handlePaywallOpen();
    }
  }

  function handleArchiveClick() {
    if (isPremium) {
      setView("archive");
    } else {
      handlePaywallOpen();
    }
  }

  function handleTitleClick() {
    setView("game");
    setArchivePuzzleDate(null);
  }

  function handleHeaderLeftClick() {
    if (view === "archive-puzzle") {
      setView("archive");
    } else {
      handleArchiveClick();
    }
  }

  const loggedIn = !isAnonymousEmail(userEmail);
  const headerLeftLabel =
    view === "archive-puzzle" ? "Back to archive" : isPremium ? "Browse archive" : "Upgrade for the archive";

  return (
    <div className="app">
      <div className="app-header">
        <button className="auth-link" onClick={handleHeaderLeftClick}>
          {headerLeftLabel}
        </button>
        {loggedIn ? (
          <button className="auth-link" onClick={handleSignOut}>
            Sign out
          </button>
        ) : (
          <button className="auth-link" onClick={handleSignInOpen}>
            Sign in
          </button>
        )}
      </div>

      <h1 className="app-title app-title-link" onClick={handleTitleClick}>
        Popdle
      </h1>

      {checkoutNotice && (
        <div className="toast" role="status">
          {checkoutNotice}
        </div>
      )}

      {view === "game" && (
        <>
          <GameBoard userId={userId} onGameOver={handleGameOver} />
          <button className="stats-link" onClick={handleStatsClick}>
            {isPremium ? "View stats" : "Upgrade to see your stats"}
          </button>
        </>
      )}

      {view === "archive" && (
        <ArchivePage
          userId={userId}
          onSelectPuzzle={(wordDate) => {
            setArchivePuzzleDate(wordDate);
            setView("archive-puzzle");
          }}
          onViewStats={() => setShowStats(true)}
        />
      )}

      {view === "archive-puzzle" && archivePuzzleDate && (
        <div className="archive-puzzle-view">
          <GameBoard userId={userId} wordDate={archivePuzzleDate} />
          <button className="stats-link" onClick={() => setShowStats(true)}>
            View stats
          </button>
        </div>
      )}

      {showStats && (
        <StatsModal
          userId={userId}
          gamesPlayed={stats.gamesPlayed}
          gamesWon={stats.gamesWon}
          currentStreak={stats.currentStreak}
          bestStreak={stats.bestStreak}
          onClose={() => setShowStats(false)}
        />
      )}

      {showPaywall && (
        <PaywallModal
          userId={userId}
          mode={authModalMode}
          onClose={() => setShowPaywall(false)}
          onLoggedIn={handleLoggedIn}
        />
      )}
    </div>
  );
}

export default App;
