# Presence (v0.8)

## Components
- `presence/detectors.py`: maps events (location/presence) to contexts (home, work, fiap).
- `presence/context.py`: suggests mode changes based on context; logs telemetry.

## Event model
- `/events` accepts types like `location`, `presence`, `movement`, `schedule`, `device_state`.
- Payload example:
```json
{
  "source": "mobile",
  "type": "location",
  "event": "home",
  "metadata": { "label": "home", "lat": -23.5, "lon": -46.6 }
}
```

## Mode suggestions
- fiap -> study_mode
- home/work -> focus_mode
- Extend `handle_presence_event` for richer logic (life_coach for negative mood, relax at home, etc).

## Telemetry
- Events are logged via telemetry; filters can be applied with `timeline.filter_events`.
