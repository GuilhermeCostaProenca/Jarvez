# Home Assistant Integration (v0.8)

## Webhook model
- Set `HA_BASE_URL` (e.g., `https://homeassistant.local/api/webhook`) and `HA_WEBHOOK_TOKEN`.
- Jarvez → HA: calls `HA_BASE_URL/<name>` with bearer token.
- Provided actions: `ac_on`, `relax_lights`, `goodnight` (names: `jarvez_ac_on`, `jarvez_relax_lights`, `jarvez_goodnight`).

## Trigger from Jarvez
- API: `POST /automation/run { "action_id": "ha.ac_on" }` with `X-API-Key`.
- Extend `jarvez/home_assistant/actions.py` with more webhooks as needed.

## Home Assistant → Jarvez
- POST `/events` with `X-API-Key`:
```json
{
  "source": "home_assistant",
  "type": "presence",
  "event": "gui_arrived_home",
  "metadata": { "zone": "home" }
}
```
- Jarvez logs telemetry and can update memory; extend `handle_home_event` for more automations (planner, routines).

## Presence-driven modes
- Use `/events` to inform location/presence; Jarvez suggests modes (study/focus/life_coach) and can trigger HA actions.

## Example automation (HA)
- On presence detection, call `POST https://jarvez-core.fly.dev/events` with payload above and API key.
- On bedtime routine, call `/automation/run` with `ha.goodnight`.
