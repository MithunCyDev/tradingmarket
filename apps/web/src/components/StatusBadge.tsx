import { statusClass } from "../lib/format";
import type { StatusLabel } from "../types";

interface StatusBadgeProps {
  status: StatusLabel;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-badge ${statusClass(status)}`}>{status}</span>;
}
