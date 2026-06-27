const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export type Category = "movie" | "tv" | "actor";

export interface GuessResult {
  guess: string;
  correct_positions: number[];
  present_letters: number[];
  won: boolean;
  attempts_used: number;
  game_over: boolean;
  answer: string | null;
}

export interface TodayPuzzle {
  word_date: string;
  category: Category;
  clue: string;
  word_length: number;
  history: GuessResult[];
  game_over: boolean;
  answer: string | null;
  is_archive: boolean;
}

export interface ArchiveEntry {
  word_date: string;
  category: Category;
  clue: string;
  word_length: number;
  played: boolean;
  game_over: boolean;
  won: boolean | null;
}

export interface HistoryEntry {
  word_date: string;
  category: Category;
  answer: string | null;
  won: boolean;
  attempts_used: number;
  game_over: boolean;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail ?? `Request failed: ${res.status}`, res.status);
  }
  return res.json();
}

export interface UserRecord {
  id: string;
  email: string;
  is_premium: boolean;
}

export const api = {
  ensureUser: (userId: string) =>
    request<UserRecord>("/users/ensure", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  signup: (userId: string, email: string, password: string) =>
    request<UserRecord>("/users/signup", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, email, password }),
    }),

  login: (email: string, password: string) =>
    request<UserRecord>("/users/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  createCheckoutSession: (userId: string) =>
    request<{ url: string; session_id: string; simulated: boolean }>("/billing/checkout-session", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  confirmCheckout: (userId: string, sessionId: string) =>
    request<{ is_premium: boolean; simulated: boolean }>("/billing/confirm", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, session_id: sessionId }),
    }),

  getToday: (userId: string, wordDate?: string) =>
    request<TodayPuzzle>(
      `/game/today?user_id=${encodeURIComponent(userId)}${wordDate ? `&date_str=${wordDate}` : ""}`,
    ),

  submitGuess: (userId: string, guess: string, wordDate?: string) =>
    request<GuessResult>("/game/guess", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, guess, word_date: wordDate ?? null }),
    }),

  getArchive: (userId: string) =>
    request<ArchiveEntry[]>(`/game/archive?user_id=${encodeURIComponent(userId)}`),

  getHistory: (userId: string) =>
    request<HistoryEntry[]>(`/game/history?user_id=${encodeURIComponent(userId)}`),

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
