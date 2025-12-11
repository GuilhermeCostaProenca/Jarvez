from __future__ import annotations

import logging
import time
from typing import Dict, Optional

try:
    import psutil
except Exception:
    psutil = None

try:
    import pygetwindow as gw  # optional
except Exception:
    gw = None


def active_app() -> Dict[str, Optional[str]]:
    proc_name = None
    title = None
    if gw:
        try:
            win = gw.getActiveWindow()
            if win:
                title = win.title
        except Exception as exc:
            logging.debug("Failed to get active window title: %s", exc)
    if psutil:
        try:
            if hasattr(psutil, "Process"):
                # best-effort; on Windows we could inspect foreground window PID, but keep simple
                procs = sorted(psutil.process_iter(["name", "create_time"]), key=lambda p: p.info.get("create_time", 0), reverse=True)
                if procs:
                    proc_name = procs[0].info.get("name")
        except Exception as exc:
            logging.debug("Failed to get active process: %s", exc)
    return {"process": proc_name, "title": title}


def detect_context(app: Dict[str, Optional[str]]) -> str:
    process = (app.get("process") or "").lower()
    title = (app.get("title") or "").lower()
    if "code" in process or "vscode" in process:
        return "coding_vs_code"
    if "chrome" in process or "edge" in process or "firefox" in process:
        if "fiap" in title:
            return "study_college"
        if "youtube" in title:
            return "watching_video"
        return "browsing"
    return "idle"


def idle_detector(last_activity: float, idle_threshold: int = 900) -> bool:
    return (time.time() - last_activity) > idle_threshold
