from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from jarvez.skills import notes
from jarvez.storage.db import JarvezDatabase

DB = JarvezDatabase()


def _default_steps(goal: str) -> List[str]:
    return [
        f"Clarificar sucesso para: {goal}",
        "Listar entregaveis principais",
        "Quebrar em blocos semanais/dias",
        "Executar primeiro bloco e validar",
        "Revisar e preparar proximo passo",
    ]


def _deadline_hint(goal_text: str) -> Optional[str]:
    tokens = goal_text.lower().split()
    for word in tokens:
        if word in {"hoje", "amanha", "amanhã"}:
            return word
    return None


def plan_goal(goal_text: str, deadline: Optional[str] = None, auto_note: bool = True) -> Dict[str, Any]:
    goal = goal_text.strip() or "objetivo"
    steps = _default_steps(goal)
    if "curriculo" in goal.lower() or "currículo" in goal.lower():
        steps = [
            "Coletar experiencias e projetos chave",
            "Selecionar linguagem e formato",
            "Escrever versao draft",
            "Revisar com foco em impacto e numeros",
            "Exportar PDF e revisar links",
        ]

    deadline = deadline or _deadline_hint(goal) or "sem prazo declarado"
    plan_id = f"plan-{int(datetime.utcnow().timestamp())}"
    plan = {
        "id": plan_id,
        "goal": goal,
        "deadline": deadline,
        "steps": steps,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "open",
    }

    DB.upsert_plan(plan_id, goal=goal, deadline=deadline, steps=steps, status="open", created_at=plan["created_at"], updated_at=plan["created_at"])

    note_msg = ""
    if auto_note:
        note_title = f"Plano - {goal}"
        note_body = "\n".join(f"- {s}" for s in steps)
        note_msg = notes.create_note(note_title, note_body)

    logging.debug("Plan created: %s", plan)

    return {
        "message": f"Plano criado para '{goal}' com {len(steps)} passos. Deadline: {deadline}. {note_msg}".strip(),
        "plan": plan,
        "note": note_msg,
    }


def follow_up(goal_filter: Optional[str] = None) -> str:
    plans = DB.list_plans()
    if goal_filter:
        plans = [p for p in plans if goal_filter.lower() in p.get("goal", "").lower()]

    if not plans:
        return "Nenhum plano registrado."

    lines = ["Planos abertos:"]
    for plan in plans:
        lines.append(f"- {plan.get('goal')} (deadline: {plan.get('deadline')}, passos: {len(plan.get('steps', []))})")
    return "\n".join(lines)


def get_plans() -> List[Dict[str, Any]]:
    return DB.list_plans()
