from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets
import math


class OrbWidget(QtWidgets.QWidget):
    clicked = QtCore.Signal()

    def __init__(self, diameter: int = 72, parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)

        # Sempre no topo, sem bordas
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
        )

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Estados: idle / talk / listen / alert / etc
        self._state = "idle"

        # Cor base
        self._base_color = QtGui.QColor("#4dabf7")

        # Timer da animação (~60 FPS)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self.update)
        self._timer.start()

        # Fase para animação sinusoidal
        self._phase = 0

    def set_state(self, state: str, color: str | None = None) -> None:
        self._state = state
        if color:
            self._base_color = QtGui.QColor(color)
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, True)

        rect = self.rect()

        # Progresso da animação
        self._phase = (self._phase + 2) % 360

        # Substituindo qSin/qDegreesToRadians por math.sin/math.radians
        if self._state == "idle":
            pulse = 2 * math.sin(math.radians(self._phase))
        elif self._state == "talk":
            pulse = 5 * math.sin(math.radians(self._phase * 2))
        elif self._state == "listen":
            pulse = 3 * math.sin(math.radians(self._phase * 1.5))
        else:
            pulse = 0

        # Configura cor base
        color = QtGui.QColor(self._base_color)
        color.setAlpha(200)

        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)

        # Calcula tamanho pulsante
        diameter = self.diameter + pulse
        offset = (self.diameter - diameter) / 2

        # Desenha orb suavemente
        painter.drawEllipse(rect.adjusted(offset, offset, -offset, -offset))

        painter.end()
