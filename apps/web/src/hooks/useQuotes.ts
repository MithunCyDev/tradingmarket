import useSWR from "swr";

import { fetchJson } from "../lib/api";
import type { QuoteListResponse } from "../types";

export function useQuotes() {
  return useSWR<QuoteListResponse>("/api/v1/quotes", fetchJson, {
    refreshInterval: (latest) => {
      if (!latest) {
        return 4000;
      }
      return latest.data.some((quote) => quote.marketState === "open") ? 4000 : 20000;
    },
    shouldRetryOnError: true,
  });
}
