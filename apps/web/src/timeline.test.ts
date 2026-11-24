import { describe, expect, it } from "vitest";
import { toolCallsFromInvestigation, workflowTimeline } from "./timeline";
import type { InvestigationResult } from "./types";

function sample(status: InvestigationResult["status"]): InvestigationResult {
  return {
    request: "Investigate overheating on CNC-042",
    equipment_code: "CNC-042",
    plan: {
      steps: ["resolve_equipment", "retrieve_telemetry", "retrieve_documentation"],
      lookback_days: 30,
      rationale: "Look up the asset",
    },
    evidence: {
      reading_count: 1,
      alarm_count: 1,
      temp_high_count: 1,
      evidence_sufficient: true,
      likely_cause: "cooling",
      confidence: "high",
      facts: [{ kind: "FACT", statement: "TEMP_HIGH", source: "get_alarm_history" }],
      inferences: [],
      recommendations: [],
      overdue_maintenance: [],
    },
    report: {
      title: "CNC-042",
      equipment_code: "CNC-042",
      summary: "Cooling issue",
      findings: [
        { kind: "FACT", statement: "TEMP_HIGH", source: "get_alarm_history" },
        { kind: "FACT", statement: "manual", source: "search_documentation" },
      ],
      likely_cause: "cooling",
      confidence: "high",
      evidence_sufficient: true,
      recommended_actions: ["inspect"],
    },
    status,
    investigation_id: "abc",
    approval:
      status === "awaiting_approval"
        ? {
            investigation_id: "abc",
            tool_name: "create_work_order",
            risk: "high",
            proposal: {},
          }
        : null,
    work_order:
      status === "completed"
        ? {
            id: "1",
            number: "WO-1",
            title: "Inspect",
            description: "loop",
            status: "open",
            priority: "high",
          }
        : null,
  };
}

describe("workflowTimeline", () => {
  it("marks approval as current while waiting", () => {
    const steps = workflowTimeline(sample("awaiting_approval"));
    const approval = steps.find((step) => step.id === "approval");
    expect(approval?.current).toBe(true);
    expect(steps.some((step) => step.id === "retrieve_documentation")).toBe(true);
  });

  it("includes the work order after approve", () => {
    const steps = workflowTimeline(sample("completed"));
    expect(steps.some((step) => step.id === "executed")).toBe(true);
  });
});

describe("toolCallsFromInvestigation", () => {
  it("groups evidence sources and waiting writes", () => {
    const tools = toolCallsFromInvestigation(sample("awaiting_approval"));
    expect(tools.map((item) => item.name)).toContain("search_documentation");
    expect(tools.some((item) => item.status === "waiting")).toBe(true);
  });
});
