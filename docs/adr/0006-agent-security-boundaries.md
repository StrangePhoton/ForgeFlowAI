# ADR-006: Agent security boundaries

## Status

Accepted (implemented in Milestone 6).

## Context

An investigation agent reads untrusted manuals, telemetry, and comments, and can propose write actions. If the model is treated as an authorization oracle, prompt injection or a malformed plan can escalate privileges.

## Decision

- Authentication and RBAC live in application code. Roles: viewer, engineer, maintenance_manager, admin.
- HTTP permissions and MCP `RoleToolAuthorizer` both run. `ApprovalGate` remains a second check on `create_work_order`.
- Retrieved documents and tool outputs are treated as untrusted data, never as instructions.
- Secrets stay in the environment; logs redact connection-string passwords; audit events omit credentials.
- The LLM is never asked whether a user is allowed to perform an action.

## Consequences

- Security tests assert 401/403 and tool denials without involving a paid model.
- Injection fixtures in `tests/security` show that malicious manual/user text cannot skip approval.
- Demo HMAC tokens and seeded passwords are for local development, not a production IdP.
