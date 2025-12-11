# Mood (v0.6)

## Components
- `mood/detector.py`: heuristic classifier based on keywords; returns sentiment + intensity.
- `mood/store.py`: persists mood traces to `data/mood_trace.json` and returns recents.

## Config
- Enable/disable detection: `JARVEZ_MOOD_ENABLED` (default on).

## Flow
1. On each user message, the orchestrator detects mood (if enabled) and appends to the store.
2. Mood summary is injected into the system prompt with personality instructions.
3. API/CLI debug shows detected mood.

## Extensibility
- Swap detector for an LLM classifier or add context from history/time-of-day.
- Add aggregation functions (weekly summaries) for future planner/journal insights.
