import type { InvestigationResult, TimelineStep, ToolCallView } from "./types";

const STEP_LABELS: Record<string, string> = {
  resolve_equipment: "Equipment resolved",
  retrieve_telemetry: "Telemetry retrieved",
  retrieve_alarms: "Alarm history retrieved",
  retrieve_maintenance: "Maintenance history retrieved",
  retrieve_documentation: "Manuals searched",
  evaluate_evidence: "Evidence evaluated",
  generate_report: "Report generated",
};

export function workflowTimeline(investigation: InvestigationResult): TimelineStep[] {
  const steps: TimelineStep[] = [
    {
      id: "request",
      label: "Request received",
      done: true,
      current: false,
      detail: investigation.request,
    },
    {
      id: "plan",
      label: "Plan created",
      done: investigation.plan.steps.length > 0,
      current: false,
      detail: investigation.plan.rationale,
    },
  ];
  for (const name of investigation.plan.steps) {
    steps.push({
      id: name,
      label: STEP_LABELS[name] ?? name.replaceAll("_", " "),
      done: true,
      current: false,
    });
  }
  steps.push({
    id: "report",
    label: "Root-cause report",
    done: Boolean(investigation.report.summary),
    current: false,
    detail: investigation.report.confidence,
  });
  const awaiting = investigation.status === "awaiting_approval";
  const decided = investigation.status === "rejected" || investigation.work_order !== null;
  if (awaiting || decided || investigation.approval) {
    steps.push({
      id: "approval",
      label: awaiting ? "Waiting for approval" : "Approval requested",
      done: true,
      current: awaiting,
      detail: investigation.approval?.tool_name,
    });
  }
  if (investigation.status === "rejected") {
    steps.push({
      id: "rejected",
      label: "Action rejected",
      done: true,
      current: true,
    });
  }
  if (investigation.work_order) {
    steps.push({
      id: "executed",
      label: "Work order created",
      done: true,
      current: true,
      detail: investigation.work_order.number,
    });
  }
  if (investigation.status === "completed" && !investigation.work_order) {
    steps.push({
      id: "complete",
      label: "Completed without a write",
      done: true,
      current: true,
    });
  }
  return steps;
}

export function toolCallsFromInvestigation(investigation: InvestigationResult): ToolCallView[] {
  const counts = new Map<string, number>();
  for (const item of investigation.report.findings) {
    counts.set(item.source, (counts.get(item.source) ?? 0) + 1);
  }
  const fromFindings: ToolCallView[] = [...counts.entries()].map(([name, count]) => ({
    name,
    status: "used",
    detail: `${count} evidence item${count === 1 ? "" : "s"}`,
  }));
  if (investigation.work_order) {
    fromFindings.push({
      name: "create_work_order",
      status: "executed",
      detail: investigation.work_order.number,
    });
  } else if (investigation.status === "awaiting_approval") {
    fromFindings.push({
      name: investigation.approval?.tool_name ?? "create_work_order",
      status: "waiting",
      detail: "Human approval required",
    });
  } else if (investigation.status === "rejected") {
    fromFindings.push({
      name: "create_work_order",
      status: "rejected",
      detail: "Not executed",
    });
  }
  return fromFindings;
}
