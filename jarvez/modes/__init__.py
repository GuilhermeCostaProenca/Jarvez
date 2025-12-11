from __future__ import annotations

from typing import Dict

from jarvez.modes.base import Mode
from jarvez.modes.focus_mode import MODE as FOCUS_MODE
from jarvez.modes.life_coach_mode import MODE as LIFE_COACH_MODE
from jarvez.modes.planner_mode import MODE as PLANNER_MODE
from jarvez.modes.study_mode import MODE as STUDY_MODE
from jarvez.modes.system_mode import MODE as SYSTEM_MODE

_MODES: Dict[str, Mode] = {
    "system": SYSTEM_MODE,
    "focus": FOCUS_MODE,
    "study": STUDY_MODE,
    "planner": PLANNER_MODE,
    "life_coach": LIFE_COACH_MODE,
}


def get_mode(name: str | None) -> Mode:
    if not name:
        return SYSTEM_MODE
    key = name.lower().replace(" ", "_")
    return _MODES.get(key, SYSTEM_MODE)


def list_modes() -> Dict[str, Mode]:
    return _MODES
