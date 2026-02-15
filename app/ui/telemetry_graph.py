from PyQt5 import QtWidgets, QtCore, QtGui

class TelemetryGraph(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(180)

        self.samples = 120
        self.throttle = [0.0] * self.samples
        self.brake = [0.0] * self.samples
    
    def set_inputs(self, throttle, brake):
        self.throttle.pop(0)
        self.brake.pop(0)
        self.throttle.append(throttle)
        self.brake.append(brake)

    # =========================================================
    # PAINT
    # =========================================================
    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # =====================================================
        # BACKGROUND
        # =====================================================
        painter.fillRect(rect, QtGui.QColor(18, 20, 28))

        # =====================================================
        # GRID LINES (horizontais sutis)
        # =====================================================
        grid_pen = QtGui.QPen(QtGui.QColor(60, 65, 80))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)

        for i in range(1, 5):
            y = int(h * i / 5)
            painter.drawLine(0, y, w, y)

        # =====================================================
        # DRAW GRAPH AREA (menos barra direita)
        # =====================================================
        bar_width = 70
        graph_width = w - bar_width - 10

        step = graph_width / self.samples

        # ----- THROTTLE (verde) -----
        path_throttle = QtGui.QPainterPath()
        path_throttle.moveTo(0, h)

        for i, val in enumerate(self.throttle):
            x = i * step
            y = h * (1 - val)
            path_throttle.lineTo(x, y)

        path_throttle.lineTo(graph_width, h)

        painter.setBrush(QtGui.QColor(0, 255, 120, 60))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPath(path_throttle)

        pen = QtGui.QPen(QtGui.QColor(0, 255, 120), 2)
        painter.setPen(pen)

        for i in range(self.samples - 1):
            x1 = i * step
            y1 = h * (1 - self.throttle[i])
            x2 = (i + 1) * step
            y2 = h * (1 - self.throttle[i + 1])
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # ----- BRAKE (vermelho) -----
        pen = QtGui.QPen(QtGui.QColor(255, 40, 40), 2)
        painter.setPen(pen)

        for i in range(self.samples - 1):
            x1 = i * step
            y1 = h * (1 - self.brake[i])
            x2 = (i + 1) * step
            y2 = h * (1 - self.brake[i + 1])
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # =====================================================
        # RIGHT INPUT BARS (Brake + Throttle)
        # =====================================================

        bar_area_width = 70
        bar_spacing = 8
        single_bar_width = 22

        bar_x_start = w - bar_area_width

        # Fundo da área
        painter.fillRect(bar_x_start, 0, bar_area_width, h,
                        QtGui.QColor(25, 28, 40))

        # Valores atuais
        current_brake = self.brake[-1]
        current_throttle = self.throttle[-1]

        brake_height = int(h * current_brake)
        throttle_height = int(h * current_throttle)

        # =========================
        # BRAKE BAR (esquerda)
        # =========================
        brake_x = bar_x_start + bar_spacing

        # Barra fundo
        painter.fillRect(brake_x, 0,
                        single_bar_width, h,
                        QtGui.QColor(40, 40, 50))

        # Barra ativa
        painter.fillRect(
            brake_x,
            h - brake_height,
            single_bar_width,
            brake_height,
            QtGui.QColor(255, 40, 40)
        )

        # Número topo
        painter.setPen(QtGui.QColor(200, 200, 200))
        painter.setFont(QtGui.QFont("Arial", 9))
        painter.drawText(
            brake_x,
            15,
            single_bar_width,
            15,
            QtCore.Qt.AlignCenter,
            f"{int(current_brake * 100)}"
        )

        # =========================
        # THROTTLE BAR (direita)
        # =========================
        throttle_x = brake_x + single_bar_width + bar_spacing

        # Barra fundo
        painter.fillRect(throttle_x, 0,
                        single_bar_width, h,
                        QtGui.QColor(40, 40, 50))

        # Barra ativa
        painter.fillRect(
            throttle_x,
            h - throttle_height,
            single_bar_width,
            throttle_height,
            QtGui.QColor(0, 255, 120)
        )

        # Número topo
        painter.drawText(
            throttle_x,
            15,
            single_bar_width,
            15,
            QtCore.Qt.AlignCenter,
            f"{int(current_throttle * 100)}"
        )