import useSWR from "swr";

import { fetchSignal } from "../lib/api";
import type { SignalStyle, SignalTicket, SymbolId } from "../types";

export function useSignal(symbol: SymbolId, style: SignalStyle) {
  return useSWR<SignalTicket | null>(
    `/api/v1/signals/${symbol}?style=${style}`,
    fetchSignal,
    {
      refreshInterval: 3000,
    },
  );
}
