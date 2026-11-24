import type { InvestigationStatus } from "../types";

const LABELS: Record<InvestigationStatus, string> = {
  completed: "completed",
  awaiting_approval: "waiting for approval",
  rejected: "rejected",
};

export function StatusBadge({ status }: { status: InvestigationStatus }) {
  return <span className={`badge ${status}`}>{LABELS[status]}</span>;
}
