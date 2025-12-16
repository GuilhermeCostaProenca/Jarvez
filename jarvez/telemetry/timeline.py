from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from jarvez.storage.db import JarvezDatabase

DB = JarvezDatabase()


def recent(limit: int = 50, event_type: Optional[str] = None) -> List[Dict]:
    events = DB.recent_events(limit=limit, event_type=event_type)
    return events


def filter_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    event_type: Optional[str] = None,
    mode: Optional[str] = None,
) -> List[Dict]:
    events = DB.recent_events(limit=500, event_type=event_type)
    results: List[Dict] = []
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if start else None
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
    for e in events:
        if mode and e.get("payload", {}).get("mode") != mode:
            continue
        ts = e.get("created_at")
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
