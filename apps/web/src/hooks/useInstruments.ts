import useSWR from "swr";

import { fetchJson } from "../lib/api";
import { FALLBACK_INSTRUMENTS, type InstrumentListResponse } from "../types";

export function useInstruments() {
  return useSWR<InstrumentListResponse>("/api/v1/instruments", fetchJson, {
    fallbackData: { data: FALLBACK_INSTRUMENTS },
    revalidateOnFocus: false,
  });
}
