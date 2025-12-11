# Telemetry (v0.7)

## Logger
- `jarvez/telemetry/logger.py` writes JSONL events to `data/telemetry.log.jsonl`.
- Event fields: `id`, `type`, `payload`, `ts`.
- Key event types: `input`, `vision.*`, `planner.plan`, `journal.create`, `mood.detected`, `journal.suggested`, `skill`.

## Timeline
- `jarvez/telemetry/timeline.py` provides `recent()` and `filter_events()` helpers.
- Used by CLI/API to surface status/debug info.

## Debug
- CLI/voice `--debug` shows event ids when present.
- Logs are append-only and lightweight; no network.
