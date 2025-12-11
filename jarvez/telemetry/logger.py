from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

TELEMETRY_PATH = Path(__file__).resolve().parents[2] / "data" / "telemetry.log.jsonl"
TELEMETRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_event(event_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
    """Append a structured telemetry event; returns event id."""
    event_id = str(uuid.uuid4())
    record = {
        "id": event_id,
        "type": event_type,
        "payload": payload or {},
        "ts": datetime.utcnow().isoformat() + "Z",
    }
    with TELEMETRY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return event_id
