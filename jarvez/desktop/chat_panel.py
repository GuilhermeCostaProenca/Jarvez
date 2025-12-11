import os
import json
import httpx

from PySide6 import QtCore, QtGui, QtWidgets


class ChatPanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvez")

        self.layout = QtWidgets.QVBoxLayout(self)

        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)

        self.input = QtWidgets.QLineEdit()
        self.input.returnPressed.connect(self.send_message)

        self.layout.addWidget(self.output)
        self.layout.addWidget(self.input)

        self.api_url = os.getenv("JARVEZ_API_URL")
        self.api_key = os.getenv("JARVEZ_API_KEY")

    def send_message(self):
        text = self.input.text().strip()
        if not text:
            return

        self.output.append(f"Você: {text}")

        self.input.clear()

        # Envia para o Jarvez Cloud
        try:
            resp = httpx.post(
                f"{self.api_url}/chat",
                headers={"X-API-Key": self.api_key},
                json={"message": text, "mode": "system"},
                timeout=20
            )

            data = resp.json()
            reply = data.get("reply", "[sem resposta]")
        except Exception as e:
            reply = f"[erro] {e}"

        self.output.append(f"Jarvez: {reply}\n")
