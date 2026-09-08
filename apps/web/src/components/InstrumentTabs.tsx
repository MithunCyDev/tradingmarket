import type { Instrument, StatusLabel, SymbolId } from "../types";

interface InstrumentTabsProps {
  instruments: Instrument[];
  selected: SymbolId;
  statuses: Partial<Record<SymbolId, StatusLabel>>;
  onSelect: (symbol: SymbolId) => void;
}

export function InstrumentTabs({
  instruments,
  selected,
  statuses,
  onSelect,
}: InstrumentTabsProps) {
  return (
    <nav className="tabs" aria-label="Instruments">
      {instruments.map((instrument) => {
        const status = statuses[instrument.id];
        const closed = status === "CLOSED";
        return (
          <button
            key={instrument.id}
            type="button"
            className={instrument.id === selected ? "tab active" : "tab"}
            aria-pressed={instrument.id === selected}
            onClick={() => onSelect(instrument.id)}
          >
            {instrument.label}
            {closed ? <span className="tab-closed">CLOSED</span> : null}
          </button>
        );
      })}
    </nav>
  );
}
