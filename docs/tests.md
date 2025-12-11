# Tests (v0.9)

## Running
- `pytest`

## Coverage (minimal)
- Memory: read/write basics.
- RAG: index and retrieve.
- Planner: create plan and persist.
- Mood: heuristic detection and store append.
- Journal: create entry and stub summary.

## Notes
- Tests avoid calling external APIs (OpenAI not required).
- Planner/journal paths are monkeypatched to temp dirs in tests.
