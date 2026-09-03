# ADR-005: LLM provider abstraction

## Status

Accepted (implementation starts Milestone 3; configuration keys exist in Milestone 0).

## Context

Local demos should run on Ollama. Cloud use should run on OpenAI. Azure OpenAI should be addable without rewriting graph nodes.

## Decision

Isolate provider selection behind a small interface configured by environment variables (`LLM_PROVIDER`, model, base URL, key, temperature, timeout, retries). Graph nodes depend on the interface, not on SDK clients. Settings already accept these fields so later milestones do not scatter env parsing.

## Consequences

- Tests mock the provider interface; default CI never calls a paid API.
- Azure OpenAI can be a third adapter that reuses the OpenAI-compatible client with a different base URL and headers.
- Changing providers is a deployment concern, not an agent-logic change.
