from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class ChatPanel(QtWidgets.QWidget):
    send_message = QtCore.Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Jarvez")
        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumWidth(320)
        self.output.setPlaceholderText("Jarvez pronto...")

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Fala comigo...")
        self.input.returnPressed.connect(self._emit_message)

        self.layout.addWidget(self.output)
        self.layout.addWidget(self.input)

    def _emit_message(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.append_message("you", text)
        self.input.clear()
        self.send_message.emit(text)

    def append_message(self, sender: str, text: str) -> None:
        prefix = "You" if sender in {"you", "me", "user"} else sender.capitalize()
        self.output.append(f"{prefix}: {text}")
        self.output.moveCursor(QtGui.QTextCursor.End)
