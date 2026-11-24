import type {
  AuditEvent,
  InvestigationResult,
  Me,
  PendingApproval,
} from "./types";

export const TOKEN_KEY = "forgeflow.token";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function apiBase(): string {
  const configured = import.meta.env.VITE_API_BASE;
  if (configured && configured.length > 0) {
    return configured.replace(/\/$/, "");
  }
  return "/api/v1";
}

export function readToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function writeToken(token: string | null): void {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = readToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${apiBase()}${path}`, { ...init, headers });
  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }
  if (!response.ok) {
    const error = asErrorEnvelope(payload);
    throw new ApiError(response.status, error.code, error.message);
  }
  return payload as T;
}

function asErrorEnvelope(payload: unknown): { code: string; message: string } {
  if (
    payload &&
    typeof payload === "object" &&
    "error" in payload &&
    payload.error &&
    typeof payload.error === "object"
  ) {
    const body = payload.error as { code?: unknown; message?: unknown };
    return {
      code: typeof body.code === "string" ? body.code : "http_error",
      message: typeof body.message === "string" ? body.message : "Request failed",
    };
  }
  return { code: "http_error", message: "Request failed" };
}

export async function login(username: string, password: string): Promise<string> {
  const body = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return body.access_token;
}

export async function fetchMe(): Promise<Me> {
  return request<Me>("/auth/me");
}

export async function fetchHealth(): Promise<{ status: string; environment: string }> {
  return request("/health");
}

export async function fetchReady(): Promise<{ status: string }> {
  try {
    return await request("/ready");
  } catch (err) {
    if (err instanceof ApiError) {
      return { status: "not_ready" };
    }
    throw err;
  }
}

export async function listInvestigations(): Promise<InvestigationResult[]> {
  return request("/investigations");
}

export async function createInvestigation(text: string): Promise<InvestigationResult> {
  return request("/investigations", {
    method: "POST",
    body: JSON.stringify({ request: text }),
  });
}

export async function getInvestigation(id: string): Promise<InvestigationResult> {
  return request(`/investigations/${id}`);
}

export async function listApprovals(): Promise<PendingApproval[]> {
  return request("/approvals");
}

export async function decideApproval(
  id: string,
  decision: "approve" | "reject",
  extras: { reason?: string; title?: string; description?: string; priority?: string } = {},
): Promise<InvestigationResult> {
  return request(`/approvals/${id}/${decision}`, {
    method: "POST",
    body: JSON.stringify({ decision, ...extras }),
  });
}

export async function listAudit(params: {
  event_type?: string;
  tool_name?: string;
  status?: string;
} = {}): Promise<AuditEvent[]> {
  const query = new URLSearchParams();
  if (params.event_type) {
    query.set("event_type", params.event_type);
  }
  if (params.tool_name) {
    query.set("tool_name", params.tool_name);
  }
  if (params.status) {
    query.set("status", params.status);
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/audit${suffix}`);
}
