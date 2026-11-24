# Security Policy

ForgeFlow AI is a demonstration platform, not a hosted production service. There is no supported release train. Use it locally or in an isolated lab.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability.

1. Use GitHub **Privately report a vulnerability** on this repository if it is enabled, or
2. Open a private security advisory, or
3. Contact the maintainers through the repository’s listed contact method.

Include the affected path, a minimal reproduction, and impact. We will acknowledge reports that we can reproduce.

## What this project is not

- Demo logins (`engineer` / `engineer-dev`, `manager` / `manager-dev`, and the other accounts in `.env.example`) are local development only.
- `FORGEFLOW_AUTH_SECRET`, Grafana `admin`/`admin`, and Compose Postgres passwords are sample values. Change them before any shared deployment.
- `GET /metrics` is unauthenticated so a local Prometheus can scrape. Do not expose it on an untrusted network.
- The LLM is not a security boundary. Authorization, write-action gating, and schema validation live in application code. See [docs/security.md](docs/security.md).

## Scope

In scope: authentication bypass, RBAC bypass, skipping `create_work_order` approval, secret leakage in logs, and injection that changes authorization.

Out of scope: using the synthetic plant as if it were real industrial data, and issues that require a deployed production identity provider we do not ship.
