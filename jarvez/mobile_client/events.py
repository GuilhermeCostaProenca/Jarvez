from __future__ import annotations

from typing import Dict


def make_location_event(lat: float, lon: float, label: str) -> Dict:
    return {
        "source": "mobile",
        "type": "location",
        "event": label,
        "metadata": {"lat": lat, "lon": lon},
    }


def make_movement_event(state: str) -> Dict:
    return {"source": "mobile", "type": "movement", "event": state, "metadata": {}}
