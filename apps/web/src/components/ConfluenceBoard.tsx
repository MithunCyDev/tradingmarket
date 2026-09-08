import { confidenceLabel, toneClass } from "../lib/format";
import type { ConfluenceReport } from "../types";

interface ConfluenceBoardProps {
  report: ConfluenceReport | undefined;
  isMissing: boolean;
}

export function ConfluenceBoard({ report, isMissing }: ConfluenceBoardProps) {
  return (
    <aside className="confluence-board" aria-label="Visual analysis">
      <div className="pane-header">
        <h2>Chart reason</h2>
        {report ? (
          <span className={`pane-sub ${toneClass(report.action)}`}>
            {report.passedCount}/{report.factorCount}
          </span>
        ) : null}
      </div>
      {isMissing ? (
        <p className="state">No ticket to mark up. Analyze this symbol first.</p>
      ) : null}
      {report ? (
        <div>
          <div className={`action-badge ${toneClass(report.action)}`}>{report.headline}</div>
          <p className="confluence-summary">{report.summary}</p>
          <div
            className="confluence-meter"
            aria-label={`${report.passedCount} of ${report.factorCount} checks`}
          >
            {report.factors.map((factor) => (
              <span
                key={factor.id}
                className={factor.passed ? "meter-pip on" : "meter-pip"}
              />
            ))}
          </div>
          {report.suggestedConfidence && report.suggestedConfidence !== report.confidence ? (
            <p className="hint">
              Structure score reads {confidenceLabel(report.suggestedConfidence)}; ticket is{" "}
              {confidenceLabel(report.confidence)}.
            </p>
          ) : null}
          <ul className="factor-list">
            {report.factors.map((factor) => (
              <li key={factor.id} className={factor.passed ? "factor-pass" : "factor-fail"}>
                <span className="factor-mark">{factor.passed ? "PASS" : "MISS"}</span>
                <div>
                  <strong>{factor.title}</strong>
                  <p>{factor.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </aside>
  );
}
