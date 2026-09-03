# ADR-002: PostgreSQL and pgvector as the system of record

## Status

Accepted.

## Context

The platform stores relational industrial data, agent run state, audit events, and (later) document embeddings. Splitting those across multiple data stores in the first milestones would add operational cost without a demonstrated need.

## Decision

Use PostgreSQL 16 for all durable state. Enable pgvector in the initial migration so embedding search can live beside operational tables. SQLAlchemy 2 (async) and Alembic own schema change.

## Consequences

- Local development and CI can use one database image (`pgvector/pgvector:pg16`).
- Retrieval can start with metadata-filtered vector search and grow to hybrid search later without a new database product.
- We do not introduce Redis, OpenSearch, or a dedicated vector DB in Milestone 0.
