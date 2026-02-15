from PyQt5 import QtWidgets, QtCore, QtGui

class LapInfoPanel(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(200)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

        # Dados mock
        self.position = "1st"
        self.total_cars = "12"
        self.current_lap = "3"
        self.total_laps = "15"
        self.best_lap = "2:23.947"
        self.last_lap = "2:23.947"
        self.gear = "4"
        self.suggested_gear = "2"

    # =========================================================
    # PAINT
    # =========================================================
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        rect = self.rect()
        radius = 12

        # =====================================================
        # BACKGROUND
        # =====================================================
        bg_gradient = QtGui.QLinearGradient(0, 0, 0, rect.height())
        bg_gradient.setColorAt(0, QtGui.QColor(15, 18, 40))
        bg_gradient.setColorAt(1, QtGui.QColor(5, 6, 15))

        painter.setBrush(bg_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # =====================================================
        # TOP SECTION (POS + LAPS)
        # =====================================================
        margin = 18
        top_height = 70

        # POS label
        painter.setPen(QtGui.QColor(180, 190, 255))
        painter.setFont(QtGui.QFont("Arial", 9))
        painter.drawText(margin, 20, "POS.")

        # POS value
        painter.setFont(QtGui.QFont("Arial", 34, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(margin, 65, f"{self.position}/{self.total_cars}")

        # LAPS label
        painter.setFont(QtGui.QFont("Arial", 9))
        painter.setPen(QtGui.QColor(180, 190, 255))
        painter.drawText(rect.width() - 120, 20, "Laps")

        # LAPS value
        painter.setFont(QtGui.QFont("Arial", 34, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(rect.width() - 150, 65, f"{self.current_lap}/{self.total_laps}")

        # =====================================================
        # DIVIDER GLOW LINE
        # =====================================================
        line_y = top_height + 10

        glow_gradient = QtGui.QLinearGradient(0, line_y - 1,
                                      0, line_y + 3)
        glow_gradient.setColorAt(0, QtGui.QColor(120, 90, 255, 120))
        glow_gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 0))

        painter.setBrush(glow_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(0, line_y - 1, rect.width(), 4)

        # Linha central fina
        pen = QtGui.QPen(QtGui.QColor(150, 120, 255, 220))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, line_y, rect.width(), line_y)

        # =====================================================
        # BOTTOM SECTION
        # =====================================================
        bottom_top = top_height + 35

        column_width = rect.width() / 3

        # ----- LEFT (Best / Last) -----
        left_x = margin

        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.setFont(QtGui.QFont("Arial", 9))
        painter.drawText(left_x, bottom_top, "Best Lap Time")

        painter.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(left_x, bottom_top + 28, self.best_lap)

        painter.setFont(QtGui.QFont("Arial", 9))
        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.drawText(left_x, bottom_top + 48, "Last Lap Time")

        painter.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(200, 200, 255))
        painter.drawText(left_x, bottom_top + 75, self.last_lap)

        # =====================================================
        # VERTICAL DIVIDER
        # =====================================================
        divider_x = int(column_width) + 20

        # Glow suave
        v_glow = QtGui.QLinearGradient(divider_x, top_height + 15,
                                    divider_x, rect.height() - 15)
        v_glow.setColorAt(0, QtGui.QColor(120, 90, 255, 120))
        v_glow.setColorAt(1, QtGui.QColor(0, 0, 0, 0))

        painter.setBrush(v_glow)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(divider_x - 2,
                        top_height + 15,
                        4,
                        rect.height() - top_height - 30)

        # Linha central fina
        pen = QtGui.QPen(QtGui.QColor(150, 120, 255, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(divider_x,
                        top_height + 15,
                        divider_x,
                        rect.height() - 15)


        # ----- CENTER (Gear) -----
        center_x = int(column_width)

        painter.setFont(QtGui.QFont("Arial", 9))
        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.drawText(center_x + 80, bottom_top, "Gear")

        painter.setFont(QtGui.QFont("Arial", 60, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(center_x + 70, bottom_top + 75, self.gear)

        # ----- RIGHT (Suggested Gear) -----
        right_x = int(column_width * 2)

        painter.setFont(QtGui.QFont("Arial", 9))
        painter.setPen(QtGui.QColor(170, 180, 255))
        painter.drawText(right_x + 20, bottom_top, "Suggested Gear")

        painter.setFont(QtGui.QFont("Arial", 48, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor(220, 220, 255))
        painter.drawText(right_x + 50, bottom_top + 70, self.suggested_gear)