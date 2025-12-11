from __future__ import annotations

from typing import Dict

from jarvez.automation.base import Workflow


def build_workflows() -> Dict[str, Workflow]:
    return {
        "study_networks": Workflow(
            id="study_networks",
            description="Sessao de estudo de redes: abre browser, cria nota e playlist.",
            actions=["open_browser_default", "create_session_note", "play_playlist"],
        ),
        "focus_session": Workflow(
            id="focus_session",
            description="Sessao de foco: abre VSCode, cria nota, playlist.",
            actions=["open_vscode", "create_session_note", "play_playlist"],
        ),
        "curriculum_boost": Workflow(
            id="curriculum_boost",
            description="Workflow para trabalhar no curriculo.",
            actions=["open_vscode", "create_session_note"],
        ),
    }
