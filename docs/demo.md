# Demo walkthrough

Record this path once the stack is up. It is the same CNC-042 scenario the tests and evals use.

## Setup

```bash
docker compose up --build
docker compose exec api python -m forgeflow.domain.seed --reset
```

Open [http://localhost:3000](http://localhost:3000). The default Compose LLM is the in-process mock, so you do not need Ollama or an API key. Optional: set `LLM_PROVIDER=ollama` in `.env` for a local model.

## Script (about 30 seconds)

1. Sign in as `engineer` / `engineer-dev`.
2. Open **New investigation**. The request field already contains `Investigate overheating on CNC-042`.
3. Click **Run investigation**. Wait until status is `awaiting_approval`.
4. Show **Evidence** (facts cite coolant flow, `TEMP_HIGH` alarms, and the fictional cooling manual) and **Tool calls**.
5. Sign out. Sign in as `manager` / `manager-dev`.
6. Open **Approvals**, leave or edit the proposed work-order title, click **Approve**.
7. Return to the investigation: a work-order number is present. Optionally open **Audit log**.

Peer assets (for example PUMP-AX200) should not propose a cooling work order. That contrast is useful in a longer recording, not required for a short GIF.

## Recording tools

| Tool | Notes |
| --- | --- |
| Windows Game Bar | **Win+G** → Capture. Saves an MP4 under Videos/Captures. |
| Snipping Tool | **Win+Shift+S**, then record if the installed version supports video. |
| ScreenToGif | Export a looping GIF under ~8 MB for a GitHub README. |
| ffmpeg | `ffmpeg -i capture.mp4 -vf "fps=10,scale=1280:-1" docs/screenshots/demo.gif` |

Do not commit a large MP4. Link a GitHub Release asset or keep a short GIF next to the stills in `docs/screenshots/`. Still screenshots are the default README media.

## What the clip should prove

- A human starts the investigation; the model does not log itself in.
- Tools retrieve plant data and manuals.
- `create_work_order` does not run until a manager approves.
- The likely cause is grounded in seeded CNC-042 signals, not a generic chatbot answer.
