from __future__ import annotations

import logging
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict

from jarvez.config import load_config
from jarvez.skills import notes

config = load_config()


def _run_command(command: str) -> str:
    if not config.allow_automation:
        return f"SAFE_MODE: not executing '{command}'"
    try:
        subprocess.Popen(command, shell=True)
        return f"EXECUTED: {command}"
    except Exception as exc:
        logging.error("Automation command failed: %s", exc)
        return f"ERROR: {exc}"


def open_vscode() -> str:
    return _run_command(f"{config.paths.vscode_path} {config.paths.workspace_dir}")


def open_browser_default() -> str:
    url = config.paths.default_url
    try:
        webbrowser.open(url)
        return f"OPENED_BROWSER: {url}"
    except Exception as exc:
        return f"ERROR_BROWSER: {exc}"


def open_workspace_folder() -> str:
    path = Path(config.paths.workspace_dir)
    if not path.exists():
        return f"WORKSPACE_NOT_FOUND: {path}"
    if os.name == "nt":
        return _run_command(f'start "" "{path}"')
    return _run_command(f'open "{path}"')


def create_session_note() -> str:
    title = "sessao-" + Path(config.paths.workspace_dir).name
    content = "Sessao iniciada."
    return notes.create_note(title, content)


def play_playlist() -> str:
    url = config.paths.playlist_url
    try:
        webbrowser.open(url)
        return f"PLAYLIST: {url}"
    except Exception as exc:
        return f"ERROR_PLAYLIST: {exc}"


def build_actions() -> Dict[str, "Action"]:
    from jarvez.automation.base import Action

    return {
        "open_vscode": Action(
            id="open_vscode",
            description="Abre VSCode no workspace",
            execute=open_vscode,
            requires_allow=True,
        ),
        "open_browser_default": Action(
            id="open_browser_default",
            description="Abre o navegador na URL padrao",
            execute=open_browser_default,
            requires_allow=False,
        ),
        "open_workspace_folder": Action(
            id="open_workspace_folder",
            description="Abre a pasta do workspace",
            execute=open_workspace_folder,
            requires_allow=True,
        ),
        "create_session_note": Action(
            id="create_session_note",
            description="Cria uma nota de sessao",
            execute=create_session_note,
            requires_allow=False,
        ),
        "play_playlist": Action(
            id="play_playlist",
            description="Abre a playlist padrao no navegador",
            execute=play_playlist,
            requires_allow=False,
        ),
    }
