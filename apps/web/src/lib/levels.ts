import type { AnalysisLevel } from "../types";
import { assertNever } from "./assertNever";

export function levelColor(kind: AnalysisLevel["kind"]): string {
  switch (kind) {
    case "entry":
      return "#d4a017";
    case "stop":
      return "#ef5350";
    case "target":
      return "#26a69a";
    case "invalidation":
      return "#c778d0";
    default:
      return assertNever(kind);
  }
}
