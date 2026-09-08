import { formatPrice } from "../lib/format";
import type { SignalTicket } from "../types";

interface SignalLevelsProps {
  ticket: SignalTicket;
  decimals: number;
}

export function SignalLevels({ ticket, decimals }: SignalLevelsProps) {
  if (ticket.action === "no_trade") {
    return (
      <p className="empty-levels">No entry, stop, or targets. Wait for the next clean setup.</p>
    );
  }

  const levels = [
    {
      label: "Entry",
      value:
        ticket.entryZone == null
          ? "—"
          : `${formatPrice(ticket.entryZone.low, decimals)} – ${formatPrice(ticket.entryZone.high, decimals)}`,
    },
    { label: "Stop", value: ticket.stop == null ? "—" : formatPrice(ticket.stop, decimals) },
    {
      label: "TP1",
      value: ticket.targets == null ? "—" : formatPrice(ticket.targets.tp1, decimals),
    },
    {
      label: "TP2",
      value: ticket.targets == null ? "—" : formatPrice(ticket.targets.tp2, decimals),
    },
    {
      label: "Invalid if",
      value: ticket.invalidation == null ? "—" : formatPrice(ticket.invalidation, decimals),
    },
  ];

  return (
    <dl className="level-grid">
      {levels.map((level) => (
        <div key={level.label} className="level-item">
          <dt>{level.label}</dt>
          <dd>{level.value}</dd>
        </div>
      ))}
    </dl>
  );
}
