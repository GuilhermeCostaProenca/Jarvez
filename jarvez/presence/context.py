from __future__ import annotations

from typing import Dict, Optional

from jarvez.presence.detectors import detect_context
from jarvez.telemetry.logger import log_event


def handle_presence_event(event: Dict, current_mode: str) -> Dict[str, str]:
    ctx = detect_context(event)
    suggested_mode = None
    suggestion = ""
    if ctx == "fiap":
        suggested_mode = "study"
        suggestion = "Entrando em study_mode (FIAP)."
    elif ctx == "home":
        suggested_mode = "focus"
        suggestion = "Entrando em focus_mode (home)."
    elif ctx == "work":
        suggested_mode = "focus"
        suggestion = "Entrando em focus_mode (work)."

    if suggested_mode and suggested_mode != current_mode:
        log_event("presence.mode_suggest", {"from": current_mode, "to": suggested_mode, "context": ctx})
    return {"context": ctx or "unknown", "suggested_mode": suggested_mode, "note": suggestion}
