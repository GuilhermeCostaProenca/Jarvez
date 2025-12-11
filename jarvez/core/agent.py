from __future__ import annotations

from typing import Dict, List

from jarvez.skills.registry import SkillRegistry

from .llm_client import LLMClient
from .memory import MemoryStore
from .orchestrator import AgentResponse, Orchestrator


class Agent:
    """Primary entry point for Jarvez interactions."""

    def __init__(self, default_mode: str | None = None) -> None:
        self.history: List[Dict[str, str]] = []
        self.memory_store = MemoryStore()
        self.llm_client = LLMClient()
        self.skill_registry = SkillRegistry()
        self.orchestrator = Orchestrator(
            self.llm_client,
            self.memory_store,
            self.skill_registry,
            default_mode=default_mode,
        )
        self.last_input: str | None = None
        self.last_output: str | None = None

    def handle(self, user_input: str) -> AgentResponse:
        result = self.orchestrator.handle(user_input, self.history)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": result.text})
        self.last_input = user_input
        self.last_output = result.text
        return result

    def set_mode(self, mode_name: str | None) -> str:
        return self.orchestrator.set_mode(mode_name)
