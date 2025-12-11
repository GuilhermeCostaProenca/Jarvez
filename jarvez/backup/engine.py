from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

BACKUP_DIR = Path(__file__).resolve().parents[2] / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILES = [
    "data/memory.json",
    "data/planner.json",
    "data/rag_index.json",
    "data/mood_trace.json",
]

DATA_DIRS = [
    "data/journal",
    "data/notes",
    "data/captures",
]


def _existing_path(rel_path: str) -> Path | None:
    path = Path(rel_path)
    return path if path.exists() else None


def create_backup() -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    folder = BACKUP_DIR / f"backup-{timestamp}-v0.7"
    folder.mkdir(parents=True, exist_ok=True)

    for rel in DATA_FILES:
        p = _existing_path(rel)
        if p:
            target = folder / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)

    for rel in DATA_DIRS:
        p = _existing_path(rel)
        if p:
            target = folder / rel
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(p, target)

    archive_path = shutil.make_archive(str(folder), "zip", root_dir=folder)
    return Path(archive_path)


def restore_backup(zip_path: str | Path) -> Path:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"Backup not found: {zip_path}")
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.unpack_archive(str(zip_path), tmpdir)
        tmp_root = Path(tmpdir)
        # find first folder in archive
        candidates = [p for p in tmp_root.iterdir() if p.is_dir()]
        root = candidates[0] if candidates else tmp_root
        for rel in DATA_FILES:
            src = root / rel
            if src.exists():
                dest = Path(rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        for rel in DATA_DIRS:
            src = root / rel
            if src.exists():
                dest = Path(rel)
                if dest.exists():
                    dest_backup = dest.with_suffix(".bak")
                    if dest_backup.exists():
                        shutil.rmtree(dest_backup)
                    shutil.move(dest, dest_backup)
                shutil.copytree(src, dest, dirs_exist_ok=True)
    return zip_path
