from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from jarvez.telemetry.logger import TELEMETRY_PATH


def _load() -> List[Dict]:
    if not TELEMETRY_PATH.exists():
        return []
    events: List[Dict] = []
    with TELEMETRY_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    return events


def recent(limit: int = 50, event_type: Optional[str] = None) -> List[Dict]:
    events = _load()
    if event_type:
        events = [e for e in events if e.get("type") == event_type]
    return events[-limit:]


def filter_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    event_type: Optional[str] = None,
    mode: Optional[str] = None,
) -> List[Dict]:
    events = _load()
    results: List[Dict] = []
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else None
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
    for e in events:
        if event_type and e.get("type") != event_type:
            continue
        if mode and e.get("payload", {}).get("mode") != mode:
            continue
        ts = e.get("ts")
        if ts:
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if start_dt and ts_dt < start_dt:
                    continue
                if end_dt and ts_dt > end_dt:
                    continue
            except Exception:
                pass
        results.append(e)
    return results
