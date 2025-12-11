from __future__ import annotations

from jarvez.modes.base import Mode

MODE = Mode(
    name="system",
    description="Modo padrao equilibrado, assistente geral.",
    tone="claro, direto, profissional",
    system_instructions="Responder como OS pessoal do Gui, curto e acionavel.",
    priority_skills=["notes", "planner", "system"],
)
