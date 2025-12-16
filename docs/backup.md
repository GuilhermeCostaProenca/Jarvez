# Backup & Restore (v1.0)

## What is backed up
- Files: `data/jarvez.db` (memories, notes, plans, journal, mood, events, settings, RAG, deletions_audit)
- Directories: `data/captures`, `assets/` relevantes
- Stored under `backups/backup-<timestamp>-v1.0.zip`

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
