# Journal (v0.6)

## Features
- `journal create ...` / natural “quero desabafar ...” saves entries to `data/journal/DATE.json`.
- Entries are mood-tagged, and (if retriever available) indexed into RAG.
- Summaries: `journal summary semana` or `journal summary mes` (stubbed heuristic for now).

## Flow
1. Skill creates journal entry, storing text + timestamp.
2. Mood detected from entry; appended to mood trace.
3. Entry is indexed into RAG for future Q&A about feelings/contexts.

## Usage
- CLI/voice/API can call journal commands; life_coach mode can suggest journaling when mood is strong.

## Extensibility
- Add real summarization of journal patterns (themes, triggers, helpers).
- Link journal entries to planner tasks or reminders.
