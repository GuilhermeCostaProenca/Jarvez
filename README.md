# Jarvez v0.9

Jarvez is a personal OS style assistant for Guilherme. v0.9 adds a Desktop Orb client with local awareness, on top of the cloud core: modes, planner, RAG, vision, mood, personality, journaling, automation stubs, telemetry, backup/restore, HA integration, API security, and remote CLI.

## Quickstart (cloud/local)
1) python -m venv .venv && .venv\Scripts\activate
2) pip install -r requirements.txt
3) Copie `.env.example` para `.env` e preencha chaves locais (OPENAI_API_KEY opcional)
4) Clique duplo em `start_jarvez.bat` para subir brain (WS 8787), API/painel (127.0.0.1:8888) e o corpo Godot. Logs em `logs/brain.log` e `logs/panel.log`.
5) Para rodar manualmente: `uvicorn jarvez.api.server:app --reload` e `python -m jarvez.brain`
6) Remote CLI: `python -m jarvez.interface.remote_cli --url https://jarvez-core.fly.dev --api-key <token> --debug`
7) Tests: `pytest`

## Cloud Core
- Dockerfile (python:3.11-slim) runs uvicorn on 8000; Fly.io sample config (`fly.toml`).
- API key required on critical routes (/chat, /plan, /automation/run, /events, /push/send).
- Home Assistant webhooks (`ha.*` actions) and /events ingestion.

## Desktop Orb (v0.9) [LEGACY]
- PySide6 orb widget (always-on-top, circular, idle/talk states, mood-ready colors).
- Chat panel anchored to orb; talks to cloud `/chat` via API key.
- Awareness loop (Windows-friendly) detects active app/title, VSCode, browser, YouTube, idle; emits context changes.
- Awareness bridge sends proactive prompts to Jarvez Cloud (rate-limited) and shows replies in the panel.
- Entry: `python -m jarvez.desktop.app` (set `JARVEZ_API_URL`, `JARVEZ_API_KEY`).
- Status: legacy; superseded by the Godot 3D body.

## New 3D Body (Godot 4, replacing the PySide orb)
- Folder `godot_body/` is a Godot 4 project; main scene `scenes/Orb.tscn` renders the energy core + rings + particles at 60 fps.
- Shaders: `shaders/orb_energy.gdshader` (core emissive) and `shaders/ring_distortion.gdshader` (rings/filaments).
- Scripts: `scripts/state_bus.gd` (WebSocket client to `ws://127.0.0.1:8787`) and `scripts/orb_controller.gd` (state-driven visuals, mouse drag/scroll, proximity distortion).
- Run: open `godot_body/project.godot` in Godot 4.x on Windows and press Play. Send JSON over WS like `{"state":"thinking","intensity":0.8,"mood":"calm"}`; the orb responds live.

## One-click start (brain + body)
- `start_jarvez.bat` agora carrega `.env`, define `JARVEZ_DB_PATH` para `data\jarvez.db`, inicia brain (`jarvez/brain.py`), API/painel (FastAPI+Uvicorn) e tenta abrir o corpo Godot. Todos os processos escrevem em `logs/*.log`.
- Se `godot_body\bin\JarvezOrb.exe` nao existir, o script abre o editor Godot se instalado e mostra instrucoes para exportar.
- Para auto-start no Windows: crie um atalho para `start_jarvez.bat` em `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.

## Armazenamento (SQLite, local-first)
- Banco unico: `data/jarvez.db` com tabelas `events`, `memories`, `notes`, `plans`, `journal_entries`, `mood_trace`, `settings`, `deletions_audit`, `rag_chunks`.
- Migracao automatica: ao iniciar, JSONs legados em `data/` sao importados uma vez (memory.json, planner.json, mood_trace.json, rag_index.json, telemetry.log.jsonl, notas txt).
- Forget: POST `/forget` com `confirm=true` remove registros dos stores (memoria, eventos, RAG, notas, planos, journal, humor) e grava apenas hashes em `deletions_audit`.

## Captura e privacidade (Mode A)
- Sensores Windows-friendly publicam em um bus de eventos: janela ativa (processo/titulo), idle aproximado, navegacao (títulos/cmdline de browsers), midia em execucao (Spotify/YouTube heuristico), digitação (editor + contagem, sem texto por padrao).
- Por default apenas metadados/resumos sao persistidos (sem texto raw). Flags RAW devem ser ativadas pelo painel/variaveis.
- Comandos de soberania: suspender (DORMANT), acordar (PASSIVE_AWARE) e forget com eliminacao definitiva.

## Presence & Events
- `/events` accepts external events (mobile/HA) and returns presence hints; presence module maps location/presence to suggested modes (home/work/fiap → focus/study).
- Telemetry logs awareness and external events.

## Home Assistant integration
- Webhooks via `ha.*` actions (AC, relax lights, goodnight).
- HA → Jarvez: POST `/events` with presence/location/device state (with API key).
- Jarvez → HA: `/automation/run` with `action_id=ha.ac_on` etc.

## Mobile integration (stubs)
- `mobile_client/*` for API wrapper, push sender (FCM stub), and event helpers.
- `/push/send` endpoint for outbound pushes (stub-friendly).

## Backup & Telemetry
- Backup/Restore: `jarvez backup` / `jarvez restore <zip>`; snapshots include memory, planner, rag_index, mood, journal, notes, captures.
- Telemetry: agora em `data/jarvez.db` (tabela `events`); inclui inputs, skills, planner, vision, mood, journaling, awareness, home/mobile events. JSONL legado eh migrado automaticamente.

## Config (selected)
- Security/Env: `JARVEZ_API_KEY`, `JARVEZ_ENV`, `JARVEZ_API_URL` (desktop client), `FCM_SERVER_KEY` (push stub), `HA_BASE_URL`, `HA_WEBHOOK_TOKEN`.
- LLM/vision/voice: `OPENAI_API_KEY`, `JARVEZ_MODEL`, `JARVEZ_VISION_ENABLED`, `JARVEZ_VISION_ALLOW_SCREEN`, `JARVEZ_VISION_ALLOW_CAMERA`, `JARVEZ_VOICE_ENABLED`, `JARVEZ_WAKE_WORD`, `JARVEZ_MIC_DEVICE`, `JARVEZ_TRANSCRIBE_BACKEND`.
- Personality/mood: `JARVEZ_PERSONALITY_PROFILE`, `JARVEZ_MOOD_ENABLED`.
- Automation/System: `JARVEZ_ALLOW_AUTOMATION`, `JARVEZ_ALLOW_COMMANDS`, `JARVEZ_WORKSPACE_DIR`, `JARVEZ_VSCODE`, `JARVEZ_BROWSER`.

## Desktop usage
- Launch: `python -m jarvez.desktop.app` (set API URL/key).
- Orb click opens chat panel; awareness triggers proactive prompts for VSCode, FIAP browsing, YouTube, idle.

## Deployment example (Fly.io)
```
fly launch
fly secrets set JARVEZ_API_KEY=meutoken OPENAI_API_KEY=...
fly deploy
```

## Next steps (v0.10 ideas)
- Real audio capture for desktop orb; richer awareness detectors; FAISS/SQLite RAG; auth/rate limiting; push gateway hardened; HA entity sync; streaming/wake-word.
