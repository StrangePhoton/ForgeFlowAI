export type Role = "viewer" | "engineer" | "maintenance_manager" | "admin";

export type EvidenceKind = "FACT" | "INFERENCE" | "RECOMMENDATION";

export type InvestigationStatus = "completed" | "awaiting_approval" | "rejected";

export interface Me {
  user_id: string;
  username: string;
  role: Role;
  permissions: string[];
}

export interface EvidenceItem {
  kind: EvidenceKind;
  statement: string;
  source: string;
}

export interface EvidenceBundle {
  reading_count: number;
  alarm_count: number;
  temp_high_count: number;
  evidence_sufficient: boolean;
  likely_cause: string | null;
  confidence: string;
  facts: EvidenceItem[];
  inferences: EvidenceItem[];
  recommendations: EvidenceItem[];
  overdue_maintenance: string[];
}

export interface InvestigationPlan {
  steps: string[];
  lookback_days: number;
  rationale: string;
}

export interface InvestigationReport {
  title: string;
  equipment_code: string | null;
  summary: string;
  findings: EvidenceItem[];
  likely_cause: string | null;
  confidence: string;
  evidence_sufficient: boolean;
  recommended_actions: string[];
}

export interface PendingApproval {
  investigation_id: string;
  tool_name: string;
  risk: string;
  proposal: Record<string, unknown>;
}

export interface WorkOrder {
  id: string;
  number: string;
  title: string;
  description: string;
  status: string;
  priority: string;
}

export interface InvestigationResult {
  request: string;
  equipment_code: string | null;
  plan: InvestigationPlan;
  evidence: EvidenceBundle;
  report: InvestigationReport;
  status: InvestigationStatus;
  investigation_id: string | null;
  approval: PendingApproval | null;
  work_order: WorkOrder | null;
}

export interface AuditEvent {
  id: string;
  occurred_at: string;
  event_type: string;
  status: string;
  username: string | null;
  role: string | null;
  tool_name: string | null;
  resource_type: string | null;
  resource_id: string | null;
  investigation_id: string | null;
  details: Record<string, unknown>;
}

export interface TimelineStep {
  id: string;
  label: string;
  done: boolean;
  current: boolean;
  detail?: string;
}

export interface ToolCallView {
  name: string;
  status: string;
  detail: string;
}
