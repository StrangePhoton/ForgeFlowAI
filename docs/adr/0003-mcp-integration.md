# ADR-003: MCP as the tool execution boundary

## Status

Accepted (implementation starts Milestone 2).

## Context

Agents need equipment, maintenance, and documentation tools. If the graph queries operational tables directly, tool schemas, authorization, timeouts, and audit become entangled with prompting.

## Decision

Expose operational capabilities through Model Context Protocol servers (equipment, maintenance, documentation). Each tool has an explicit input/output schema, validation, logging, and authorization in deterministic code. The agent selects and calls tools; it does not bypass them for data that belongs behind a tool.

## Consequences

- MCP is a real process/module boundary, not a documentation keyword.
- Tests can invoke tools through an MCP client without exercising the full LLM loop.
- Extra latency versus in-process SQL is accepted for isolation and a realistic industrial integration shape.
