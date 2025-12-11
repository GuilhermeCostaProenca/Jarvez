from __future__ import annotations

import os
import subprocess
import webbrowser


def open_url(url: str) -> str:
    target = url.strip()
    if not target:
        return "No URL provided"
    try:
        webbrowser.open(target)
        return f"Opened URL: {target}"
    except Exception as exc:
        return f"Failed to open URL: {exc}"


def open_application(app_name: str) -> str:
    if not app_name:
        return "No application provided"
    return f"App launch requested: {app_name} (implement platform-specific launcher)"


def run_command(command: str, execute: bool | None = None) -> str:
    if not command:
        return "No command provided"

    allow = execute if execute is not None else os.environ.get("JARVEZ_ALLOW_COMMANDS") == "1"
    if not allow:
        return f"Safe mode: command not executed -> {command}"

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=20)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            return f"Command failed ({result.returncode}): {stderr or stdout}"
        return stdout or "Command executed."
    except Exception as exc:
        return f"Command error: {exc}"
