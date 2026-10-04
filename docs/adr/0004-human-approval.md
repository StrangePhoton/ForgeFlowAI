# ADR-004: Human approval via persisted graph interrupt

## Status

Accepted (implemented in Milestone 5).

## Context

Creating or updating work orders and other write actions must not run automatically. Operators need to approve, edit, or reject a proposed action. Restarting the whole investigation after approval would discard gathered evidence and invite duplicate writes.

## Decision

Classify risky actions in deterministic policy code (not by asking the model). When approval is required, the LangGraph run interrupts and the checkpoint is stored (MemorySaver in tests, PostgreSQL when `CHECKPOINT_BACKEND=postgres`). Resume uses the persisted state. Work-order creation is keyed by `investigation:{id}:create_work_order` so a retry cannot create duplicates.

`ApprovalGate` is the tool-layer control: `create_work_order` is denied until the graph grants that idempotency key after a human `approve` decision.

## Consequences

- The API exposes an approval queue and resume endpoints.
- In-memory graph state is insufficient for process restart; Compose uses the PostgreSQL checkpointer.
- Rejection is a recorded `status=rejected` outcome and creates no work order.
- The HTTP approval index is in-process; checkpoint resume is the durable path.
