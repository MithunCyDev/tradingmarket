export type SessionName = "Asia" | "London" | "New York";

export function activeSessions(now: Date): SessionName[] {
  const hour = now.getUTCHours();
  const sessions: SessionName[] = [];
  if (hour >= 0 && hour < 8) {
    sessions.push("Asia");
  }
  if (hour >= 7 && hour < 16) {
    sessions.push("London");
  }
  if (hour >= 13 && hour < 22) {
    sessions.push("New York");
  }
  return sessions;
}

export function sessionLabel(now: Date): string {
  const sessions = activeSessions(now);
  return sessions.length === 0 ? "Off session" : sessions.join(" / ");
}

export function utcClock(now: Date): string {
  return now.toISOString().slice(11, 19) + " UTC";
}
