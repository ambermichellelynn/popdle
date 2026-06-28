/**
 * Formats a plain "YYYY-MM-DD" date string (no time/timezone) for display.
 *
 * `new Date("2026-06-28")` parses as UTC midnight, then `.toLocaleDateString()`
 * converts to the browser's local timezone — which shifts the displayed date
 * back a day for anyone west of UTC. Since these are calendar dates with no
 * actual time component, we build the Date from local year/month/day parts
 * instead of letting the string parser assume UTC.
 */
export function formatPuzzleDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
