from PyQt5 import QtWidgets, QtCore, QtGui

class FuelPanel(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(120)

        self.total_segments = 10
        self.fuel_percent = 10.0

        self.blink_state = True
        self.blink_timer = QtCore.QTimer()
        self.blink_timer.timeout.connect(self._toggle_blink)
        self.blink_timer.start(300)  # 300ms = piscar confortável

    def _toggle_blink(self):
        if self.fuel_percent <= 20:
            self.blink_state = not self.blink_state
            self.update()
        else:
            if not self.blink_state:
                self.blink_state = True
                self.update()

    def remaining_segments(self):
        percent = max(0.0, min(100.0, self.fuel_percent))
        return int(self.total_segments * (percent / 100.0))

    # =========================================================
    # PAINT
    # =========================================================
    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()

        # BACKGROUND
        bg = QtGui.QLinearGradient(0, 0, 0, rect.height())
        bg.setColorAt(0, QtGui.QColor(6, 10, 30))
        bg.setColorAt(1, QtGui.QColor(2, 4, 15))
        painter.fillRect(rect, bg)

        margin_left = 30
        margin_top = 20

        # =====================================================
        # LEFT SIDE (FUEL + BARS)
        # =====================================================

        # Title
        painter.setPen(QtGui.QColor(220, 220, 255))
        painter.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        painter.drawText(margin_left, margin_top+30, "Fuel")

        # Segment settings
        segment_width = 18
        segment_height = 24
        spacing = 6

        start_x = margin_left
        start_y = margin_top + 45

        active_segments = self.remaining_segments()
        critical = self.fuel_percent <= 20

        for i in range(self.total_segments):

            x = start_x + i * (segment_width + spacing)

            is_active = i >= (self.total_segments - active_segments)

            # Último segmento vermelho
            if i == self.total_segments - 1:
                active_color = QtGui.QColor(220, 40, 40)
            else:
                active_color = QtGui.QColor(0, 150, 255)

            if is_active:

                if critical and not self.blink_state:
                    continue

                # Glow LED
                glow = QtGui.QColor(active_color)
                glow.setAlpha(120)

                glow_pen = QtGui.QPen(glow)
                glow_pen.setWidth(4)
                painter.setPen(glow_pen)
                painter.drawRect(
                    x - 1,
                    start_y - 1,
                    segment_width + 2,
                    segment_height + 2
                )

                painter.fillRect(
                    x,
                    start_y,
                    segment_width,
                    segment_height,
                    active_color
                )

            else:
                painter.fillRect(
                    x,
                    start_y,
                    segment_width,
                    segment_height,
                    QtGui.QColor(25, 35, 55)
                )

        # Scale labels
        painter.setFont(QtGui.QFont("Arial", 9))
        painter.setPen(QtGui.QColor(150, 160, 200))

        painter.drawText(start_x, start_y + 45, "100%")
        painter.drawText(start_x + 4 * (segment_width + spacing),
                         start_y + 45, "50%")
        painter.drawText(start_x + 9 * (segment_width + spacing),
                         start_y + 45, "0%")

        # =====================================================
        # RIGHT SIDE (METRICS)
        # =====================================================

        right_x = rect.width() - 115

        painter.setFont(QtGui.QFont("Arial", 10))
        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.drawText(right_x, margin_top, "Last Lap Consume")

        painter.setFont(QtGui.QFont("Arial", 28, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(right_x, margin_top + 40, f"{self.fuel_percent:.1f}%")

        painter.setFont(QtGui.QFont("Arial", 10))
        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.drawText(right_x, margin_top + 65, "Remaining Laps")

        painter.setFont(QtGui.QFont("Arial", 36, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(right_x+40, margin_top + 115, "20")