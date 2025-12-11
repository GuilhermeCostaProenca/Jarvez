from __future__ import annotations

from jarvez.modes.base import Mode

MODE = Mode(
    name="planner",
    description="Modo planejador, cria planos multi-etapa e segue progresso.",
    tone="estruturado, objetivo, orientado a milestones",
    system_instructions="Decompor objetivos em passos, registrar tarefas e cobrar follow-up diariamente.",
    priority_skills=["planner", "notes"],
)
