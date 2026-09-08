import { formatPercent, formatPrice, formatSignedPrice, toneClass } from "../lib/format";
import type { Instrument, Quote, SymbolId } from "../types";
import { StatusBadge } from "./StatusBadge";

interface WatchlistProps {
  instruments: Instrument[];
  quotes: Quote[];
  selected: SymbolId;
  quotesError: boolean;
  onSelect: (symbol: SymbolId) => void;
}

export function Watchlist({ instruments, quotes, selected, quotesError, onSelect }: WatchlistProps) {
  const quoteMap = new Map(quotes.map((quote) => [quote.symbol, quote]));

  return (
    <section className="watchlist" aria-label="Markets">
      <div className="watch-heading">
        <h2>Markets</h2>
        {quotesError ? <p className="watch-note">Quote feed unavailable.</p> : null}
      </div>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Status</th>
            <th>Last</th>
            <th className="watch-change">Change</th>
            <th className="watch-pct">%</th>
          </tr>
        </thead>
        <tbody>
          {instruments.map((instrument) => {
            const quote = quoteMap.get(instrument.id);
            const change = quote?.change ?? 0;
            const closed = quote?.statusLabel === "CLOSED";
            return (
              <tr
                key={instrument.id}
                className={[
                  instrument.id === selected ? "selected" : "",
                  closed ? "market-closed" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onSelect(instrument.id)}
              >
                <td>
                  <button type="button" className="watch-symbol" onClick={() => onSelect(instrument.id)}>
                    {instrument.label}
                  </button>
                </td>
                <td>{quote ? <StatusBadge status={quote.statusLabel} /> : "—"}</td>
                <td>
                  {quote?.last == null ? "—" : formatPrice(quote.last, instrument.priceDecimals)}
                </td>
                <td className={`watch-change ${toneClass(change)}`}>
                  {quote?.change == null
                    ? "—"
                    : formatSignedPrice(quote.change, instrument.priceDecimals)}
                </td>
                <td className={`watch-pct ${toneClass(quote?.changePercent ?? 0)}`}>
                  {quote?.changePercent == null ? "—" : formatPercent(quote.changePercent)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
