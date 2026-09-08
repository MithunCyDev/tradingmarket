import { formatPrice } from "../lib/format";
import { levelColor } from "../lib/levels";
import type { AnalysisLevel } from "../types";

interface ChartLegendProps {
  levels: AnalysisLevel[];
  decimals: number;
}

export function ChartLegend({ levels, decimals }: ChartLegendProps) {
  if (levels.length === 0) {
    return (
      <p className="hint">Structure only — no trade levels on this ticket.</p>
    );
  }
  return (
    <ul className="chart-legend">
      {levels.map((level) => (
        <li key={level.id}>
          <span
            className="legend-swatch"
            style={{ background: levelColor(level.kind) }}
          />
          {level.label} {formatPrice(level.price, decimals)}
        </li>
      ))}
      <li>
        <span className="legend-swatch ema20" />
        EMA 20
      </li>
      <li>
        <span className="legend-swatch ema50" />
        EMA 50
      </li>
    </ul>
  );
}
