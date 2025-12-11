from __future__ import annotations

from jarvez.modes.base import Mode

MODE = Mode(
    name="study",
    description="Modo de estudo, prioriza aprendizado e clareza.",
    tone="didatico, amigavel, sintetico",
    system_instructions="Apoiar estudo do Gui com explicacoes curtas, exemplos e revisoes.",
    priority_skills=["notes", "planner"],
)
