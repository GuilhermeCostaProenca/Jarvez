# Cloud (v0.8)

## Build & Run
- Dockerfile (python:3.11-slim) runs: `uvicorn jarvez.api.server:app --host 0.0.0.0 --port 8000`
- Build: `docker build -t jarvez:0.8 .`
- Run: `docker run -p 8000:8000 -e JARVEZ_API_KEY=token jarvez:0.8`

## Fly.io example
- `fly launch`
- `fly secrets set JARVEZ_API_KEY=... OPENAI_API_KEY=...`
- `fly deploy`
- Ports: 80/443 → internal 8000 (see fly.toml)

## API Key
- All critical routes require `X-API-Key` and must match `JARVEZ_API_KEY`.

## Backups in cloud
- Use `jarvez.backup.engine.create_backup()` or run CLI remotely (exec into container) to generate zip under `backups/`.
- Persist volumes for `data/` and `backups/` if needed.
