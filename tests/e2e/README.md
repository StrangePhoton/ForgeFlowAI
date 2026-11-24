# End-to-end tests

The operations console is covered by Vitest unit tests in `apps/web` plus a manual CNC-042 pass in the browser (login as engineer, start the investigation, approve as manager). Playwright is not in this repository yet.

Investigation scoring lives in `python -m evals` (see [docs/evaluation.md](../../docs/evaluation.md)). Those reports are generated, not hand-written.
