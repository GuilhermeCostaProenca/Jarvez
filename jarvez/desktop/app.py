from __future__ import annotations

import asyncio
import os
import sys
import threading

from PySide6 import QtCore, QtWidgets
import httpx

from jarvez.desktop.chat_panel import ChatPanel
from jarvez.desktop.orb_widget import OrbWidget
from jarvez.desktop.awareness_bridge import AwarenessBridge
from jarvez.awareness.loop import AwarenessLoop
from jarvez.config import load_config


class JarvezRemoteClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}
        self.client = httpx.Client(timeout=30)

    def chat(self, message: str, mode: str | None = None, extra_context: dict | None = None) -> dict:
        payload = {"message": message, "mode": mode, "debug": True}
        if extra_context:
            payload["context"] = extra_context
        resp = self.client.post(f"{self.base_url}/chat", json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()


class DesktopApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        cfg = load_config()
        base_url = os.environ.get("JARVEZ_API_URL", "http://localhost:8000")
        api_key = cfg.api_key or os.environ.get("JARVEZ_API_KEY", "")
        self.client = JarvezRemoteClient(base_url, api_key)

        self.orb = OrbWidget()
        self.orb.move(20, self.primaryScreen().size().height() - 100)
        self.panel = ChatPanel()
        self.orb.clicked.connect(self.toggle_panel)
        self.panel.send_message.connect(self.send_message)

        self.orb.show()

        self.awareness = AwarenessLoop(self.on_context_change)
        self.awareness_bridge = AwarenessBridge(self.send_proactive)
        self._awareness_thread = threading.Thread(target=self.awareness.run, daemon=True)
        self._awareness_thread.start()

    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.panel.move(self.orb.x() + self.orb.width() + 10, self.orb.y() - 50)
            self.panel.show()

    def send_message(self, text: str):
        try:
            self.orb.set_state("talk")
            data = self.client.chat(text)
            self.panel.append_message("jarvez", data.get("reply", ""))
        except Exception as exc:
            self.panel.append_message("error", str(exc))
        finally:
            self.orb.set_state("idle")

    def send_proactive(self, text: str, ctx: dict):
        QtCore.QTimer.singleShot(0, lambda: self._send_proactive_impl(text, ctx))

    def _send_proactive_impl(self, text: str, ctx: dict):
        try:
            self.orb.set_state("talk")
            data = self.client.chat(text, mode=ctx.get("awareness", {}).get("context"))
            self.panel.append_message("jarvez", data.get("reply", ""))
        except Exception as exc:
            self.panel.append_message("error", f"proactive failed: {exc}")
        finally:
            self.orb.set_state("idle")

    def on_context_change(self, context: dict):
        QtCore.QTimer.singleShot(0, lambda: self.awareness_bridge.on_context_change(context))


def main():
    app = DesktopApp(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
