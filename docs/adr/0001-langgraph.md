# ADR-001: LangGraph for agent orchestration

## Status

Accepted (implementation starts Milestone 3).

## Context

ForgeFlow investigations are long-running workflows: plan, retrieve data, evaluate evidence, possibly re-plan, assess risk, wait for a human, then execute an approved action. The workflow must pause and resume without restarting the investigation.

## Decision

Use LangGraph with an explicit state graph and typed state. Important control-flow decisions are graph nodes and edges, not a hidden prebuilt agent loop.

## Consequences

- Persistence and interrupts map onto graph checkpoints (PostgreSQL checkpointer in Milestone 5).
- The design is more verbose than a generic tool-calling agent and easier to test and audit.
- We accept LangGraph as a core dependency rather than writing a custom state machine.
