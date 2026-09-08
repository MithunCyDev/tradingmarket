import useSWR from "swr";

import { fetchJson } from "../lib/api";
import type { ChartResponse, SymbolId, Timeframe } from "../types";

export function useChart(symbol: SymbolId, timeframe: Timeframe) {
  return useSWR<ChartResponse>(
    `/api/v1/charts/${symbol}?timeframe=${timeframe}`,
    fetchJson,
    {
      refreshInterval: 30000,
      shouldRetryOnError: true,
    },
  );
}
