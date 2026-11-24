# Console screenshots

These images are captured from the running operations console. They are not mockups. `demo.gif` is the same engineer → investigation → manager approve → work order path.

| File | Screen | When to capture |
| --- | --- | --- |
| `demo.gif` | Engineer → investigation → manager approve | Same path as [demo.md](../demo.md); rebuilt from the stills below |
| `login.png` | Sign in | Logged out, [http://localhost:3000/login](http://localhost:3000/login) |
| `dashboard.png` | Operations dashboard | Engineer session after at least one CNC-042 investigation |
| `new-investigation.png` | New investigation form | Engineer, request field showing `Investigate overheating on CNC-042` |
| `investigation.png` | Investigation detail | CNC-042 run in `awaiting_approval` with facts, timeline, and tool calls visible |
| `approvals.png` | Approval queue | Manager session with the pending work order |
| `audit.png` | Audit log | After login, investigation, and an approval decision |

Vite on port 5173 is the same app during local frontend work. Prefer Compose port 3000 for README shots so the URL matches the quick start.

## Capture (Windows)

1. Start the stack and seed:

   ```powershell
   docker compose up --build
   docker compose exec api python -m forgeflow.domain.seed --reset
   ```

2. Open [http://localhost:3000](http://localhost:3000).
3. Press **Win+Shift+S** (Snipping Tool) and save each PNG into this folder with the names above.
   - Or Edge/Chrome: **F12 → Ctrl+Shift+P → “Capture screenshot”** (viewport) or **“Capture full size screenshot”** for long investigation pages.
4. Keep the window about **1280×800**. Avoid overlapping OS notifications.
5. Use the demo accounts only (`engineer` / `engineer-dev`, then `manager` / `manager-dev`). Do not paste real credentials.

Suggested order:

1. Sign out (or a private window) → `login.png`
2. Sign in as engineer → Dashboard → `dashboard.png`
3. **New investigation** (do not submit yet) → `new-investigation.png`
4. Submit the CNC-042 request → wait until status is awaiting approval → `investigation.png` (full-page if the evidence list is long)
5. Sign out → sign in as manager → **Approvals** → `approvals.png`
6. Approve or leave pending, then **Audit log** → `audit.png`

Replace a file in place; GitHub README paths stay the same.

## Demo video or GIF

A 20–40 second clip of the same path is enough. Windows Game Bar (**Win+G** → Capture) or ScreenToGif both work. Keep the clip under ~8 MB if you attach it to a GitHub release; link it from the README rather than committing a large binary. Instructions: [demo.md](../demo.md).
