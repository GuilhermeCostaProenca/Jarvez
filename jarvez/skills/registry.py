from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from . import journal, notes, planner, system


@dataclass
class SkillResult:
    handled: bool
    message: str = ""
    name: str = ""
    metadata: Optional[Dict[str, str]] = None


class SkillRegistry:
    """Lightweight skill router."""

    def dispatch(self, user_input: str) -> SkillResult:
        text = user_input.strip()
        lower = text.lower()

        if not text:
            return SkillResult(handled=False)

        if lower.startswith(("note create", "create note", "note add", "add note")):
            title, content = self._split_title_content(text)
            created = notes.create_note(title, content)
            return SkillResult(handled=True, message=created, name="notes.create")

        if lower.startswith(("note list", "list notes")):
            listing = notes.list_notes()
            message = "No notes yet." if not listing else "Notes:\n" + "\n".join(f"- {item}" for item in listing)
            return SkillResult(handled=True, message=message, name="notes.list")

        if lower.startswith(("note search", "search note", "find note")):
            term = text.split(None, 2)[-1] if len(text.split()) >= 3 else ""
            matches = notes.search_notes(term)
            if not matches:
                return SkillResult(handled=True, message=f"No notes matching '{term}'", name="notes.search")
            message = "Note matches:\n" + "\n".join(f"- {m}" for m in matches)
            return SkillResult(handled=True, message=message, name="notes.search")

        if lower.startswith(("note read", "read note")):
            title = text.split(None, 2)[-1] if len(text.split()) >= 3 else ""
            message = notes.read_note(title)
            return SkillResult(handled=True, message=message, name="notes.read")

        if lower.startswith(("plan ", "planner ", "plano ", "planejar", "goal ", "objetivo ")):
            goal = text.split(None, 1)[-1] if len(text.split()) >= 2 else ""
            result = planner.plan_goal(goal)
            return SkillResult(handled=True, message=result["message"], name="planner.plan", metadata=result.get("plan"))

        if lower.startswith(("follow up", "seguir plano", "status plano")):
            goal = text.split(None, 2)[-1] if len(text.split()) >= 3 else ""
            message = planner.follow_up(goal_filter=goal)
            return SkillResult(handled=True, message=message, name="planner.follow_up")

        if lower.startswith(("open url", "open http", "open https", "open www", "open ")):
            url = self._extract_url(text)
            message = system.open_url(url)
            return SkillResult(handled=True, message=message, name="system.open_url")

        if lower.startswith(("journal summary", "journal resumo")):
            period = "week"
            if "mes" in lower or "mês" in lower or "month" in lower:
                period = "month"
            message = journal.summarize(period=period)
            return SkillResult(handled=True, message=message, name="journal.summary")

        if lower.startswith(("journal", "diario", "diário")) or "desabafar" in lower:
            content = text.split(None, 1)[-1] if len(text.split()) >= 2 else text
            return SkillResult(handled=True, message="", name="journal.create", metadata={"content": content})

        if lower.startswith(("run ", "exec ", "command ")):
            command = text.split(None, 1)[-1] if len(text.split()) >= 2 else ""
            message = system.run_command(command)
            return SkillResult(handled=True, message=message, name="system.run_command")

        if lower.startswith(("open app", "launch ")):
            app_name = text.split(None, 2)[-1] if len(text.split()) >= 3 else ""
            message = system.open_application(app_name)
            return SkillResult(handled=True, message=message, name="system.open_application")

        return SkillResult(handled=False)

    def _split_title_content(self, text: str) -> tuple[str, str]:
        parts = text.split(":", 1)
        if len(parts) == 2:
            title_part = parts[0]
            content = parts[1].strip()
        else:
            title_part = text
            content = ""

        tokens = title_part.split()
        title = tokens[-1] if tokens else "note"
        if len(tokens) > 2:
            title = " ".join(tokens[2:])
        title = title or "note"

        return title.strip(), content

    def _extract_url(self, text: str) -> str:
        match = re.search(r"(https?://\S+|www\.\S+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return text.split(None, 1)[-1] if text.split() else ""
