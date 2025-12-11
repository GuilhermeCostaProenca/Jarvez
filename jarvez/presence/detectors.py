from __future__ import annotations

from typing import Dict, Optional

HOME_LABELS = {"home", "casa"}
WORK_LABELS = {"work", "trabalho"}
FIAP_LABELS = {"fiap", "faculdade"}


def detect_context(event: Dict) -> Optional[str]:
    etype = event.get("type", "")
    name = event.get("event", "").lower()
    meta = event.get("metadata", {})
    label = meta.get("label", "").lower() if isinstance(meta, dict) else ""

    if etype == "location":
        target = name or label
        if any(k in target for k in HOME_LABELS):
            return "home"
        if any(k in target for k in WORK_LABELS):
            return "work"
        if any(k in target for k in FIAP_LABELS):
            return "fiap"
    if etype == "presence":
        if "arrived" in name or "entered" in name:
            if "home" in name:
                return "home"
            if "work" in name:
                return "work"
            if "fiap" in name:
                return "fiap"
    return None
