import { useState } from "react";

const STORAGE_KEY = "popdle_user_id";

function getOrCreateUserId(): string {
  const existing = localStorage.getItem(STORAGE_KEY);
  if (existing) return existing;
  const id = crypto.randomUUID();
  localStorage.setItem(STORAGE_KEY, id);
  return id;
}

export function useUserId(): string {
  const [userId] = useState(getOrCreateUserId);
  return userId;
}
