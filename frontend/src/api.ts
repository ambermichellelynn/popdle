const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export type Category = "movie" | "tv" | "actor";

export interface TodayPuzzle {
  word_date: string;
  category: Category;
  clue: string;
  word_length: number;
}

export interface GuessResult {
  guess: string;
  correct_positions: number[];
  present_letters: number[];
  won: boolean;
  attempts_used: number;
  game_over: boolean;
  answer: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  ensureUser: (userId: string) =>
    request<{ id: string; is_premium: boolean }>("/users/ensure", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  getToday: () => request<TodayPuzzle>("/game/today"),

  submitGuess: (userId: string, guess: string) =>
    request<GuessResult>("/game/guess", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, guess }),
    }),

  recordEvent: (userId: string, name: string, properties?: string) =>
    request<unknown>("/events", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, name, properties }),
    }),

  getAssignment: (userId: string, experimentKey: string) =>
    request<{ experiment_key: string; variant: string }>(
      `/experiments/${experimentKey}/assignment?user_id=${encodeURIComponent(userId)}`,
    ),
};
