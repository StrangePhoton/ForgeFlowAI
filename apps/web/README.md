# Operations console

React 19 + TypeScript + Vite console for ForgeFlow investigations.

## Screens

- Sign in (demo accounts)
- Dashboard (investigations, API health, pending approvals)
- New investigation
- Investigation detail (workflow timeline, evidence, tool-call viewer)
- Approval queue (approve / edit proposal / reject)
- Audit log (event, tool, status filters)

README images live in [docs/screenshots](../../docs/screenshots/). Recapture steps: [docs/screenshots/README.md](../../docs/screenshots/README.md).

Timeline and tool-call rows are derived from the stored investigation result. The graph does not persist hidden chain-of-thought.

## Local Vite (API on the host)

From the repository root, start PostgreSQL and the API, then:

```powershell
cd apps/web
npm ci
npm run dev
```

Vite listens on [http://localhost:5173](http://localhost:5173) and proxies `/api` to `http://127.0.0.1:8000`. Default login is `engineer` / `engineer-dev`. Approve writes as `manager` / `manager-dev`.

## Checks

```powershell
npm run lint
npm test
npm run build
```

## Docker

`docker compose up --build` builds this app into nginx on port 3000 and proxies `/api` to the API service.
