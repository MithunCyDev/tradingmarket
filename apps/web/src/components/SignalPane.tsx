import {
  actionLabel,
  biasLabel,
  confidenceLabel,
  formatTimestamp,
  toneClass,
} from "../lib/format";
import { assertNever } from "../lib/assertNever";
import {
  SCALP_BIAS_FRAMES,
  SWING_BIAS_FRAMES,
  type SignalStyle,
  type SignalTicket,
  type Timeframe,
} from "../types";
import { SignalLevels } from "./SignalLevels";

interface SignalPaneProps {
  ticket: SignalTicket | null | undefined;
  error: Error | undefined;
  decimals: number;
  symbolLabel: string;
  style: SignalStyle;
}

function biasFrames(ticket: SignalTicket): Timeframe[] {
  const style = ticket.style ?? "swing";
  switch (style) {
    case "scalp":
      return SCALP_BIAS_FRAMES.filter((timeframe) => ticket.timeframeBias[timeframe] != null);
    case "swing":
      return SWING_BIAS_FRAMES.filter((timeframe) => ticket.timeframeBias[timeframe] != null);
    default:
      return assertNever(style);
  }
}

function emptyTicketCopy(style: SignalStyle, symbolLabel: string): { title: string; hint: string } {
  switch (style) {
    case "scalp":
      return {
        title: "No scalp ticket.",
        hint: `In Cursor say: analyze scalp ${symbolLabel}`,
      };
    case "swing":
      return {
        title: "No signal yet.",
        hint: `In Cursor say: analyze ${symbolLabel}`,
      };
    default:
      return assertNever(style);
  }
}

export function SignalPane({
  ticket,
  error,
  decimals,
  symbolLabel,
  style,
}: SignalPaneProps) {
  const emptyCopy = ticket === null && !error ? emptyTicketCopy(style, symbolLabel) : null;

  return (
    <aside className="signal-pane" aria-label="Signal ticket">
      <div className="pane-header">
        <h2>Signal ticket</h2>
        <span className="pane-sub">{symbolLabel}</span>
      </div>
      {error ? <p className="state error">Signal feed unavailable.</p> : null}
      {ticket === undefined && !error ? (
        <p className="state">Loading ticket…</p>
      ) : null}
      {emptyCopy ? (
        <div className="empty-ticket">
          <p>{emptyCopy.title}</p>
          <p className="hint">{emptyCopy.hint}</p>
        </div>
      ) : null}
      {ticket ? (
        <div className="ticket">
          <div className={`action-badge ${toneClass(ticket.action)}`}>
            {actionLabel(ticket.action)}
          </div>
          <div className="ticket-meta">
            <span>
              {ticket.timeframe} · {confidenceLabel(ticket.confidence)}{" "}
              confidence
            </span>
            <span>{formatTimestamp(ticket.analyzedAt)}</span>
          </div>
          <SignalLevels ticket={ticket} decimals={decimals} />
          <div className="bias-row">
            {biasFrames(ticket).map((timeframe) => {
              const bias = ticket.timeframeBias[timeframe];
              if (bias == null) {
                return null;
              }
              return (
                <span key={timeframe} className={`bias-chip ${toneClass(bias)}`}>
                  {timeframe} {biasLabel(bias)}
                </span>
              );
            })}
          </div>
          <section>
            <h3>Why</h3>
            <p>{ticket.narrative}</p>
          </section>
          <section>
            <h3>Risk</h3>
            <p>{ticket.riskNotes}</p>
          </section>
        </div>
      ) : null}
    </aside>
  );
}
