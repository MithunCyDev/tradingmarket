import type { SignalStyle, Timeframe } from "../types";
import { assertNever } from "./assertNever";

const STORAGE_KEY = "elite-forex-signal-style";

export function readDeskStyle(): SignalStyle {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "scalp" || stored === "swing") {
      return stored;
    }
  } catch {
    // Private mode / blocked storage should not break the desk.
  }
  return "swing";
}

export function persistDeskStyle(style: SignalStyle): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, style);
  } catch {
    // Ignore quota or privacy errors.
  }
}

export function defaultTimeframe(style: SignalStyle): Timeframe {
  switch (style) {
    case "scalp":
      return "M5";
    case "swing":
      return "H1";
    default:
      return assertNever(style);
  }
}
