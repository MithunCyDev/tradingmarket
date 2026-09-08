import useSWR from "swr";

import { fetchSignal } from "../lib/api";
import type { AnalysisResponse, SignalStyle, SymbolId } from "../types";

export function useAnalysis(symbol: SymbolId, style: SignalStyle) {
  return useSWR<AnalysisResponse | null>(
    `/api/v1/analysis/${symbol}?style=${style}`,
    fetchSignal,
    {
      refreshInterval: 3000,
    },
  );
}
