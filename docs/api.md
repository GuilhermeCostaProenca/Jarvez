# API (v0.9)

Run:
```
uvicorn jarvez.api.server:app --host 0.0.0.0 --port 8000
```

All critical routes require `X-API-Key` matching `JARVEZ_API_KEY` (can be comma-separated list).

## POST /chat
```json
{ "message": "texto", "mode": "focus", "debug": true }
```
Returns reply, mode, skill_used, memory_used, vision_used, memory/note/rag context, optional plan, mood, personality, journal_suggested.

## POST /plan
```json
{ "goal": "montar curriculo ate domingo" }
```
Creates a plan (planner skill), saves note, updates memory/RAG.

## POST /automation/run
```json
{ "action_id": "open_vscode" }
{ "action_id": "ha.ac_on" }
{ "workflow_id": "study_networks" }
```
Runs automation actions/workflows; `ha.*` maps to Home Assistant webhooks.

## POST /events
Accepts external events (mobile/HA):
```json
{ "source": "home_assistant", "type": "presence", "event": "gui_arrived_home", "metadata": { "zone": "home" } }
```
Logs telemetry; returns presence hints; orchestrator can handle home events.

## POST /push/send
```json
{ "token": "<fcm_token>", "title": "Jarvez", "body": "mensagem", "data": {} }
```
Sends mobile push (FCM stub if no server key).

## GET /status
Returns mode, last input/output, plans_count, automation safe mode, vision/mood flags, personality profile, journal/mood counts, env.
