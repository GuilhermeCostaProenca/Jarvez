from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_MEMORY_PATH = Path(__file__).resolve().parents[2] / "data" / "memory.json"


class MemoryStore:
    """JSON-backed memory store supporting simple importance detection and profiling."""

    def __init__(self, path: Path | str = DEFAULT_MEMORY_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {"user": {}, "facts": [], "dynamic_facts": [], "state": {}}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as exc:
                logging.error("Failed to load memory file: %s", exc)
                self._data = {"facts": []}
        else:
            self.save_memory()
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        self._data.setdefault("user", {})
        self._data.setdefault("facts", [])
        self._data.setdefault("dynamic_facts", [])
        state = self._data.setdefault("state", {})
        state.setdefault("last_mode", "system")

    def get_memory(self) -> Dict[str, Any]:
        return self._data

    def save_memory(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def update_memory(self, entry: Dict[str, Any], section: str = "facts") -> Dict[str, Any]:
        entry.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
        bucket = self._data.setdefault(section, [])
        bucket.append(entry)
        self.save_memory()
        logging.debug("Memory updated in section '%s': %s", section, entry.get("content", "")[:120])
        return entry

    def detect_important(self, user_input: str) -> List[Dict[str, Any]]:
        text = user_input.strip()
        if not text:
            return []

        lower = text.lower()
        base_keywords = ("remember", "important", "note", "save this")
        goal_keywords = ("goal", "objetivo", "meta", "objetivos", "metas")
        project_keywords = ("projeto", "project", "initiativa", "initiative")
        decision_keywords = ("decidi", "decisao", "decide", "decided")
        change_keywords = ("mudei", "mudanca", "change", "update")
        win_keywords = ("conquista", "entreguei", "alcancei", "terminei", "finalizei", "shipped")

        tags: List[str] = []
        if any(word in lower for word in goal_keywords):
            tags.append("goal")
        if any(word in lower for word in project_keywords):
            tags.append("project")
        if any(word in lower for word in decision_keywords):
            tags.append("decision")
        if any(word in lower for word in change_keywords):
            tags.append("change")
        if any(word in lower for word in win_keywords):
            tags.append("achievement")

        hit = any(word in lower for word in base_keywords) or bool(tags)
        long_enough = len(text) > 140

        if not hit and not long_enough:
            return []

        entry = {
            "id": f"fact-{int(datetime.utcnow().timestamp())}",
            "content": text,
            "source": "user",
            "type": "observation",
            "tags": tags,
            "_section": "dynamic_facts",
        }
        return [entry]

    def relevant_facts(self, limit: int = 5) -> List[str]:
        facts = list(self._data.get("facts", [])) + list(self._data.get("dynamic_facts", []))
        ordered = list(reversed(facts))
        return [fact.get("content", "") for fact in ordered[:limit] if fact.get("content")]

    def get_last_mode(self) -> str:
        state = self._data.get("state", {})
        return state.get("last_mode", "system")

    def set_last_mode(self, mode: str) -> None:
        self._data.setdefault("state", {})["last_mode"] = mode
        self.save_memory()

    def dynamic_documents(self) -> List[Dict[str, Any]]:
        return list(self._data.get("dynamic_facts", []))

    def describe_user(self) -> str:
        user = self._data.get("user", {})
        name = user.get("name", "Gui")
        language = user.get("language", "pt-BR")
        timezone = user.get("timezone", "America/Sao_Paulo")
        style = user.get("style", "conciso e pratico")
        goals = user.get("goals", [])
        goal_text = "; ".join(goals) if goals else "Sem metas registradas."

        return (
            f"Usuario: {name} | Idioma: {language} | Fuso: {timezone} | Estilo: {style}. "
            f"Objetivos: {goal_text}"
        )

    def describe_projects(self) -> str:
        projects = [f["content"] for f in self._data.get("facts", []) if f.get("type") == "project" and f.get("content")]
        if not projects:
            return "Sem projetos registrados."
        return "Projetos ativos: " + "; ".join(projects)

    def describe_goals(self) -> str:
        user_goals = self._data.get("user", {}).get("goals", [])
        dynamic_goals = [
            f["content"]
            for f in self._data.get("dynamic_facts", [])
            if ("goal" in f.get("tags", []) or f.get("type") == "goal") and f.get("content")
        ]
        all_goals = list(user_goals) + dynamic_goals
        if not all_goals:
            return "Sem objetivos registrados."
        return "Objetivos: " + "; ".join(all_goals)

    def answer_from_memory(self, user_input: str) -> Optional[str]:
        lower = user_input.lower()
        about_user = ("quem sou eu", "quem sou", "who am i", "sobre mim", "about me")
        about_projects = ("quais sao meus projetos", "meus projetos", "my projects", "projetos principais")
        about_goals = ("quais sao meus objetivos", "meus objetivos", "my goals", "objetivos de medio prazo", "metas")

        if any(key in lower for key in about_user):
            return self.describe_user()

        if any(key in lower for key in about_projects):
            return self.describe_projects()

        if any(key in lower for key in about_goals):
            return self.describe_goals()

        return None

    def system_context(self, note_summaries: Optional[List[str]] = None, dynamic_limit: int = 3) -> str:
        user = self._data.get("user", {})
        name = user.get("name", "Guilherme")
        language = user.get("language", "pt-BR")
        timezone = user.get("timezone", "America/Sao_Paulo")
        style = user.get("style", "conciso e pratico")
        goals = user.get("goals", [])

        static_projects = [
            f["content"] for f in self._data.get("facts", []) if f.get("type") == "project" and f.get("content")
        ]
        preferences = [
            f["content"] for f in self._data.get("facts", []) if f.get("type") == "preference" and f.get("content")
        ]
        dynamic = list(reversed(self._data.get("dynamic_facts", [])))[:dynamic_limit]
        dynamic_texts = [item.get("content", "") for item in dynamic if item.get("content")]

        note_lines = note_summaries or []

        sections: List[str] = [
            f"Perfil do usuario: {name} | Idioma: {language} | Fuso: {timezone} | Estilo: {style}",
        ]
        if goals:
            sections.append("Objetivos atuais: " + "; ".join(goals))
        if static_projects:
            sections.append("Projetos principais: " + "; ".join(static_projects))
        if preferences:
            sections.append("Preferencias: " + "; ".join(preferences))
        if dynamic_texts:
            sections.append("Memoria dinamica recente: " + "; ".join(dynamic_texts))
        if note_lines:
            sections.append("Notas relevantes: " + "; ".join(note_lines))

        return " | ".join(sections)
