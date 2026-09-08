import { useEffect, useState } from "react";

import { formatPrice, formatTimestamp } from "../lib/format";
import { sessionLabel, utcClock } from "../lib/session";
import type { Instrument, Quote, SignalStyle, StatusLabel, SymbolId } from "../types";
import { InstrumentTabs } from "./InstrumentTabs";
import { StatusBadge } from "./StatusBadge";

interface TopBarProps {
  instruments: Instrument[];
  selected: Instrument;
  quote: Quote | undefined;
  statuses: Partial<Record<SymbolId, StatusLabel>>;
  analyzedAt: string | null;
  style: SignalStyle;
  onSelect: (symbol: SymbolId) => void;
  onStyleChange: (style: SignalStyle) => void;
}

export function TopBar({
  instruments,
  selected,
  quote,
  statuses,
  analyzedAt,
  style,
  onSelect,
  onStyleChange,
}: TopBarProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const change = quote?.change ?? 0;

  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-name">Elite Forex</span>
        <span className="brand-credit">Developed by Mithuncy</span>
      </div>
      <InstrumentTabs
        instruments={instruments}
        selected={selected.id}
        statuses={statuses}
        onSelect={onSelect}
      />
      <div className="top-meta">
        <div className="price-block">
          <span className="meta-label">{selected.label}</span>
          <strong className={change >= 0 ? "up" : "down"}>
            {quote?.last == null ? "—" : formatPrice(quote.last, selected.priceDecimals)}
          </strong>
          {quote ? <StatusBadge status={quote.statusLabel} /> : null}
        </div>
        <div className="session-block">
          <span className="meta-label">Session</span>
          <strong>{sessionLabel(now)}</strong>
          <span className="clock">{utcClock(now)}</span>
        </div>
        <div className="session-block">
          <span className="meta-label">Desk</span>
          <div className="style-toggle" role="tablist" aria-label="Ticket style">
            <button
              type="button"
              role="tab"
              aria-selected={style === "swing"}
              className={style === "swing" ? "active" : undefined}
              onClick={() => onStyleChange("swing")}
            >
              SWING
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={style === "scalp"}
              className={style === "scalp" ? "active" : undefined}
              onClick={() => onStyleChange("scalp")}
            >
              SCALP
            </button>
          </div>
        </div>
        <div className="session-block">
          <span className="meta-label">Last signal</span>
          <strong>{analyzedAt ? formatTimestamp(analyzedAt) : "None"}</strong>
        </div>
      </div>
    </header>
  );
}
