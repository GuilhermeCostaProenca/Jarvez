# Config (v0.8)

Env vars drive most behavior:

- Security/Env: `JARVEZ_API_KEY` (required for protected API), `JARVEZ_ENV` (local/production).
- LLM/Voice/Vision: `OPENAI_API_KEY`, `JARVEZ_MODEL`, `JARVEZ_VISION_ENABLED`, `JARVEZ_VISION_ALLOW_SCREEN`, `JARVEZ_VISION_ALLOW_CAMERA`, `JARVEZ_VISION_PROVIDER`, `JARVEZ_VISION_MODEL`, `JARVEZ_VOICE`, `JARVEZ_CAPTURE_DIR`.
- Personality/Mood: `JARVEZ_PERSONALITY_PROFILE` (default_gui/coach_firme/comfort_mode), `JARVEZ_MOOD_ENABLED` (default on).
- Automation/System: `JARVEZ_ALLOW_AUTOMATION`, `JARVEZ_ALLOW_COMMANDS`, `JARVEZ_WORKSPACE_DIR`, `JARVEZ_VSCODE`, `JARVEZ_BROWSER`, `JARVEZ_DEFAULT_URL`, `JARVEZ_PLAYLIST_URL`.
- Home Assistant: `HA_BASE_URL`, `HA_WEBHOOK_TOKEN` for webhook calls.
- Modes default: stored in memory.state.last_mode; can be overridden via CLI/API.

All flags are read in `jarvez/config.py`; defaults are safe (vision and automation off unless enabled).
