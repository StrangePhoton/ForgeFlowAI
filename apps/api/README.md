# API process

ASGI entrypoint for the ForgeFlow HTTP API.

```bash
uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Application factory: `forgeflow.api.app.create_app`.
