import { useMemo, useState } from "react";

import { AnalysisChart } from "./components/AnalysisChart";
import { ConfluenceBoard } from "./components/ConfluenceBoard";
import { Disclaimer } from "./components/Disclaimer";
import { SignalPane } from "./components/SignalPane";
import { TopBar } from "./components/TopBar";
import { TradingViewChart } from "./components/TradingViewChart";
import { Watchlist } from "./components/Watchlist";
import { useAnalysis } from "./hooks/useAnalysis";
import { useInstruments } from "./hooks/useInstruments";
import { useQuotes } from "./hooks/useQuotes";
import { useSignal } from "./hooks/useSignal";
import { defaultTimeframe, persistDeskStyle, readDeskStyle } from "./lib/deskStyle";
import { FALLBACK_INSTRUMENTS, type SignalStyle, type StatusLabel, type SymbolId } from "./types";

export default function App() {
  const { data: instrumentResponse } = useInstruments();
  const instruments = instrumentResponse?.data ?? FALLBACK_INSTRUMENTS;
  const [selectedId, setSelectedId] = useState<SymbolId>("XAUUSD");
  const [style, setStyle] = useState<SignalStyle>(() => readDeskStyle());
  const selected = useMemo(
    () =>
      instruments.find((item) => item.id === selectedId) ??
      instruments[0] ??
      FALLBACK_INSTRUMENTS[0],
    [instruments, selectedId],
  );
  const { data: quoteResponse, error: quotesError } = useQuotes();
  const { data: ticket, error: signalError } = useSignal(selected.id, style);
  const { data: analysis } = useAnalysis(selected.id, style);
  const quotes = quoteResponse?.data ?? [];
  const selectedQuote = quotes.find((item) => item.symbol === selected.id);
  const statuses: Partial<Record<SymbolId, StatusLabel>> = Object.fromEntries(
    quotes.map((quote) => [quote.symbol, quote.statusLabel]),
  );

  return (
    <div className="desk">
      <TopBar
        instruments={instruments}
        selected={selected}
        quote={selectedQuote}
        statuses={statuses}
        analyzedAt={ticket?.analyzedAt ?? null}
        style={style}
        onSelect={setSelectedId}
        onStyleChange={(next) => {
          setStyle(next);
          persistDeskStyle(next);
        }}
      />
      <main className="desk-body">
        <TradingViewChart tvSymbol={selected.tvSymbol} />
        <SignalPane
          ticket={ticket}
          error={signalError}
          decimals={selected.priceDecimals}
          symbolLabel={selected.label}
          style={style}
        />
        <AnalysisChart
          symbol={selected.id}
          timeframe={ticket?.timeframe ?? defaultTimeframe(style)}
          levels={analysis?.levels ?? []}
          decimals={selected.priceDecimals}
        />
        <ConfluenceBoard
          report={analysis?.confluence}
          isMissing={ticket === null}
        />
        <Watchlist
          instruments={instruments}
          quotes={quotes}
          selected={selected.id}
          quotesError={Boolean(quotesError)}
          onSelect={setSelectedId}
        />
      </main>
      <Disclaimer />
    </div>
  );
}
