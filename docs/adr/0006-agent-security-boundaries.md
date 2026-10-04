# ADR-006: Agent security boundaries

## Status

Accepted (enforcement starts Milestone 6; principles apply immediately).

## Context

An investigation agent reads untrusted manuals, telemetry, and comments, and can propose write actions. If the model is treated as an authorization oracle, prompt injection or a malformed plan can escalate privileges.

## Decision

- Authentication and RBAC live in application code. Roles: viewer, engineer, maintenance_manager, admin.
- Tool authorization is checked in the tool layer regardless of what the model requested.
- Retrieved documents and tool outputs are treated as untrusted data, never as instructions.
- Secrets stay in the environment; logs redact connection-string passwords.
- The LLM is never asked whether a user is allowed to perform an action.

## Consequences

- Security tests can assert denials without involving a model.
- Prompt-injection fixtures belong in `tests/security` once retrieval exists. Retrieved manuals are cited as FACT text and cannot grant `create_work_order`.
- Defense in depth is more important than a clever system prompt.
