# ADR-004: Human approval via persisted graph interrupt

## Status

Accepted (implementation starts Milestone 5).

## Context

Creating or updating work orders and other write actions must not run automatically. Operators need to approve, edit, or reject a proposed action. Restarting the whole investigation after approval would discard gathered evidence and invite duplicate writes.

## Decision

Classify risky actions in deterministic policy code (not by asking the model). When approval is required, the LangGraph run interrupts and the checkpoint is stored in PostgreSQL. Resume uses the persisted state. Work-order creation is idempotent so a retry after resume cannot create duplicates.

## Consequences

- The API must expose an approval queue and resume endpoints.
- In-memory graph state is insufficient; checkpointing is a Milestone 5 requirement.
- Rejection is a recorded outcome, not a silent no-op.
