import type { Action, Bias, Confidence, StatusLabel } from "../types";
import { assertNever } from "./assertNever";

export function formatPrice(value: number, decimals: number): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatSignedPrice(value: number, decimals: number): string {
  const formatted = formatPrice(Math.abs(value), decimals);
  if (value > 0) {
    return `+${formatted}`;
  }
  if (value < 0) {
    return `-${formatted}`;
  }
  return formatted;
}

export function formatPercent(value: number): string {
  const formatted = Math.abs(value).toFixed(2);
  if (value > 0) {
    return `+${formatted}%`;
  }
  if (value < 0) {
    return `-${formatted}%`;
  }
  return `${formatted}%`;
}

export function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  return date.toLocaleString("en-GB", {
    hour12: false,
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function actionLabel(action: Action): string {
  switch (action) {
    case "long":
      return "LONG";
    case "short":
      return "SHORT";
    case "no_trade":
      return "NO TRADE";
    default:
      return assertNever(action);
  }
}

export function biasLabel(bias: Bias): string {
  switch (bias) {
    case "long":
      return "Long";
    case "short":
      return "Short";
    case "range":
      return "Range";
    default:
      return assertNever(bias);
  }
}

export function confidenceLabel(confidence: Confidence): string {
  switch (confidence) {
    case "low":
      return "Low";
    case "medium":
      return "Medium";
    case "high":
      return "High";
    default:
      return assertNever(confidence);
  }
}

export function statusClass(status: StatusLabel): string {
  switch (status) {
    case "LIVE":
      return "status-live";
    case "DELAYED":
      return "status-delayed";
    case "CLOSED":
      return "status-closed";
    default:
      return assertNever(status);
  }
}

export function toneClass(value: Action | Bias | number): string {
  if (typeof value === "number") {
    if (value > 0) {
      return "up";
    }
    if (value < 0) {
      return "down";
    }
    return "flat";
  }
  switch (value) {
    case "long":
      return "up";
    case "short":
      return "down";
    case "range":
    case "no_trade":
      return "flat";
    default:
      return assertNever(value);
  }
}
