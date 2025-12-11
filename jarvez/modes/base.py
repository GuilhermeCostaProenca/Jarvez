from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Mode:
    name: str
    description: str
    tone: str
    system_instructions: str
    priority_skills: List[str] = field(default_factory=list)
