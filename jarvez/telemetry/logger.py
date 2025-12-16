from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from jarvez.storage.db import JarvezDatabase

DB = JarvezDatabase()


def log_event(event_type: str, payload: Optional[Dict[str, Any]] = None) -> str:
    """Append a structured telemetry event; returns event id."""
    event_id = str(uuid.uuid4())
    DB.add_event(event_id, event_type, payload=payload or {}, source="telemetry")
    return event_id
