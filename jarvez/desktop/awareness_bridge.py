from __future__ import annotations

import time
from typing import Callable, Dict, Optional

from jarvez.telemetry.logger import log_event


class AwarenessBridge:
    def __init__(self, send_proactive: Callable[[str, Dict], None], cooldown_seconds: int = 300):
        self.send_proactive = send_proactive
        self.cooldown_seconds = cooldown_seconds
        self.last_sent: Dict[str, float] = {}

    def on_context_change(self, context: Dict[str, str]) -> None:
        ctx_type = context.get("context")
        if not ctx_type:
            return
        now = time.time()
        if ctx_type in self.last_sent and now - self.last_sent[ctx_type] < self.cooldown_seconds:
            return

        message = None
        if ctx_type == "coding_vs_code":
            message = "O Gui abriu o VSCode. Pergunte o que vamos focar hoje e se ha tarefas pendentes."
        elif ctx_type == "study_college":
            message = "O Gui esta em contexto de estudo (FIAP). Sugira retomar o plano de estudo."
        elif ctx_type == "watching_video":
            message = "O Gui esta vendo video (YouTube). Pergunte se quer salvar notas ou registrar aprendizado."
        elif ctx_type == "idle":
            message = "O Gui esta inativo ha um tempo. Sugira pausa curta, agua e alongamento."

        if message:
            log_event("awareness_context_change", context)
            self.send_proactive(message, {"awareness": context})
            self.last_sent[ctx_type] = now
