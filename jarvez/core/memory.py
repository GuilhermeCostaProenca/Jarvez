from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from jarvez.storage.db import JarvezDatabase, _utcnow


class MemoryStore:
    """SQLite-backed memory store supporting importance detection and profiling."""

    def __init__(self, db: JarvezDatabase | None = None):
        self.db = db or JarvezDatabase()

    def _load(self) -> Dict[str, Any]:
        # Reconstruct a structure close to the legacy JSON for backward compatibility
        memories = self.db.search_memories(limit=500)
        facts = [m for m in memories if m.get("section") == "facts"]
        dynamics = [m for m in memories if m.get("section") == "dynamic_facts"]
        user_profile = self.db.get_setting("user_profile")
        user_data = {}
        if user_profile:
            try:
                user_data = json.loads(user_profile)
            except Exception:
                user_data = {}
        last_mode = self.db.get_setting("last_mode") or "system"
        return {"user": user_data, "facts": facts, "dynamic_facts": dynamics, "state": {"last_mode": last_mode}}

    def get_memory(self) -> Dict[str, Any]:
        return self._load()

    def save_memory(self) -> None:  # pragma: no cover - kept for API compatibility
        # No-op because persistence happens on each insert.
        return

    def update_memory(self, entry: Dict[str, Any], section: str = "facts") -> Dict[str, Any]:
        entry.setdefault("timestamp", _utcnow())
        mem_id = entry.get("id") or f"mem-{int(datetime.utcnow().timestamp())}"
        tags = entry.get("tags", [])
        self.db.upsert_memory(
            mem_id,
            text=entry.get("content", ""),
            tags=tags,
            importance=entry.get("importance"),
            source=entry.get("source"),
            created_at=entry.get("timestamp"),
            expires_at=entry.get("expires_at"),
            privacy_level=entry.get("privacy_level"),
            section=section,
            metadata={k: v for k, v in entry.items() if k not in {"id", "content", "tags", "timestamp", "expires_at"}},
        )
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
        memories = self.db.search_memories(limit=limit * 2)
        ordered = list(memories)
        return [fact.get("text", "") for fact in ordered[:limit] if fact.get("text")]

    def get_last_mode(self) -> str:
        return self.db.get_setting("last_mode") or "system"

    def set_last_mode(self, mode: str) -> None:
        self.db.upsert_setting("last_mode", mode)

    def dynamic_documents(self) -> List[Dict[str, Any]]:
        return [m for m in self.db.search_memories(section="dynamic_facts", limit=20)]

    def describe_user(self) -> str:
        user = self.get_memory().get("user", {})
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
        data = self.get_memory()
        projects = [f["text"] for f in data.get("facts", []) if f.get("metadata", {}).get("type") == "project" and f.get("text")]
        if not projects:
            return "Sem projetos registrados."
        return "Projetos ativos: " + "; ".join(projects)

    def describe_goals(self) -> str:
        data = self.get_memory()
        user_goals = data.get("user", {}).get("goals", [])
        dynamic_goals = [
            f["text"]
            for f in data.get("dynamic_facts", [])
            if ("goal" in (f.get("tags") or []) or f.get("metadata", {}).get("type") == "goal") and f.get("text")
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
        data = self.get_memory()
        user = data.get("user", {})
        name = user.get("name", "Guilherme")
        language = user.get("language", "pt-BR")
        timezone = user.get("timezone", "America/Sao_Paulo")
        style = user.get("style", "conciso e pratico")
        goals = user.get("goals", [])

        static_projects = [
            f.get("text")
            for f in data.get("facts", [])
            if f.get("metadata", {}).get("type") == "project" and f.get("text")
        ]
        preferences = [
            f.get("text")
            for f in data.get("facts", [])
            if f.get("metadata", {}).get("type") == "preference" and f.get("text")
        ]
        dynamic = list(reversed(data.get("dynamic_facts", [])))[:dynamic_limit]
        dynamic_texts = [item.get("text", "") for item in dynamic if item.get("text")]

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
