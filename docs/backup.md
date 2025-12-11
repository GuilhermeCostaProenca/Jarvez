# Backup & Restore (v0.7)

## What is backed up
- Files: `data/memory.json`, `data/planner.json`, `data/rag_index.json`, `data/mood_trace.json`
- Directories: `data/journal`, `data/notes`, `data/captures`
- Stored under `backups/backup-<timestamp>-v0.7.zip`

## How to create
- CLI: `jarvez backup` (inside CLI prompt)
- Code: `from jarvez.backup.engine import create_backup; create_backup()`

## How to restore
- CLI: `jarvez restore backups/backup-YYYYMMDD-HHMMSS-v0.7.zip`
- Code: `from jarvez.backup.engine import restore_backup; restore_backup(path)`
- Existing directories get `.bak` when replaced (notes/journal/captures).

## Safety
- Restore copies files; directories are moved to `.bak` if already present.
- Verify backups before deleting existing data.
