# Security model

Milestone 6 enforces authentication, RBAC, tool authorization, audit events, and untrusted-data handling in application code. The LLM is never asked whether an action is allowed.

## Authentication

Protected routes require `Authorization: Bearer <token>`.

`POST /api/v1/auth/login` issues an HMAC token signed with `FORGEFLOW_AUTH_SECRET`. Tokens expire after `FORGEFLOW_AUTH_TOKEN_TTL_SECONDS` (default eight hours).

Health, readiness, OpenAPI, and login stay public so probes and local docs keep working. The React console stores the bearer token in `sessionStorage` and sends it on API calls. CORS allows the configured Vite and nginx origins; it is not a substitute for RBAC.

Demo accounts (local development only):

| Username | Password | Role |
| --- | --- | --- |
| `viewer` | `viewer-dev` | viewer |
| `engineer` | `engineer-dev` | engineer |
| `manager` | `manager-dev` | maintenance_manager |
| `admin` | `admin-dev` | admin |

Change `FORGEFLOW_AUTH_SECRET` outside local use. This is not a production identity provider.

## RBAC

| Role | Can |
| --- | --- |
| viewer | Read equipment, investigations, approvals, and audit |
| engineer | Viewer plus start investigations |
| maintenance_manager | Engineer plus approve/reject writes and invoke `create_work_order` after approval |
| admin | All of the above |

HTTP checks permissions before a handler runs. MCP tools check again.

## Tool authorization

`RoleToolAuthorizer` plus `ApprovalGate` run as a composite:

1. The caller's role must allow the tool (`tools:read` or `tools:write`).
2. `create_work_order` also needs a recorded human grant of that investigation's idempotency key.

An engineer cannot create a work order even if the gate was granted. A manager cannot create one without the grant. Prompt text cannot change either check.

## Untrusted data

User requests, tool payloads, and retrieved manuals are wrapped in `<untrusted_data>` when sent to the model. Evidence evaluation treats manual text as FACT citations, not instructions. Security tests include injection strings that try to skip approval; writes still require a manager approve.

## Audit

`GET /api/v1/audit` lists login success/failure, authorization denials, investigation start, approval decisions, and work-order creates. Passwords and tokens are not stored. When `CHECKPOINT_BACKEND=postgres`, events go to `audit_events` and login uses the seeded `users` table. Pytest uses `memory` and keeps the audit log and demo directory in-process.
