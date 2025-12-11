# Mobile (v0.9)

## Client pieces
- `mobile_client/api.py`: wrapper for /chat, /events, /push/send with API key.
- `mobile_client/push.py`: FCM sender (stub if no server key).
- `mobile_client/events.py`: helpers to build location/movement events.
- Remote CLI: `python -m jarvez.interface.remote_cli --url ... --api-key ... --debug`.

## Server endpoints
- `/chat` (X-API-Key)
- `/events` for location/presence/movement/schedule/device_state (X-API-Key)
- `/push/send` (X-API-Key) for outbound mobile pushes.

## Integrations
- Use `/events` to send presence/loc from the phone; orchestrator can switch modes or trigger automations.
- Use `/push/send` to deliver reminders, study suggestions, mood reflections, or HA automation prompts.
