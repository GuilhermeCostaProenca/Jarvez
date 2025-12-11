from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvez.skills import notes

PLANNER_PATH = Path(__file__).resolve().parents[2] / "data" / "planner.json"
PLANNER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_store() -> Dict[str, List[Dict]]:
    if not PLANNER_PATH.exists():
        return {"plans": []}
    try:
        return json.loads(PLANNER_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.error("Failed to load planner store: %s", exc)
        return {"plans": []}


def _save_store(data: Dict[str, List[Dict]]) -> None:
    PLANNER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


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

    store = _load_store()
    store.setdefault("plans", []).append(plan)
    _save_store(store)

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
    store = _load_store()
    plans = store.get("plans", [])
    if goal_filter:
        plans = [p for p in plans if goal_filter.lower() in p.get("goal", "").lower()]

    if not plans:
        return "Nenhum plano registrado."

    lines = ["Planos abertos:"]
    for plan in plans:
        lines.append(f"- {plan.get('goal')} (deadline: {plan.get('deadline')}, passos: {len(plan.get('steps', []))})")
    return "\n".join(lines)


def get_plans() -> List[Dict[str, Any]]:
    store = _load_store()
    return store.get("plans", [])
