from PyQt5 import QtWidgets, QtCore, QtGui

class SpeedGauge(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 500)

        self.speed = 95
        self.max_speed = 240

        self.start_angle = -210
        self.total_angle = 240

        self.primary = QtGui.QColor(130, 90, 255)
        self.outer_ring = QtGui.QColor(110, 120, 200)
        self.bg_dark = QtGui.QColor(8, 10, 20)

    # =========================================================
    # PAINT
    # =========================================================
    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h)

        painter.translate(w / 2, h / 2)
        painter.scale(side / 500, side / 500)

        radius = 210

        self._draw_background(painter, radius)
        self._draw_outer_ring(painter, radius)
        self._draw_active_arc(painter, radius)
        self._draw_inner_glow(painter, radius)
        self._draw_directional_light(painter, radius)
        self._draw_ticks_and_numbers(painter, radius)
        self._draw_text(painter)

    # =========================================================
    # BACKGROUND
    # =========================================================
    def _draw_background(self, painter, radius):
        gradient = QtGui.QRadialGradient(0, 0, radius)
        gradient.setColorAt(0, QtGui.QColor(35, 30, 70))
        gradient.setColorAt(0.6, QtGui.QColor(18, 18, 40))
        gradient.setColorAt(1, QtGui.QColor(8, 10, 20))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(QtCore.QPointF(0, 0), radius, radius)

    # =========================================================
    # OUTER RING
    # =========================================================
    def _draw_outer_ring(self, painter, radius):
        rect = QtCore.QRectF(-radius, -radius, radius * 2, radius * 2)

        pen = QtGui.QPen(self.outer_ring)
        pen.setWidth(3)
        painter.setPen(pen)

        painter.drawArc(
            rect,
            int((90 - self.start_angle) * 16),
            int(-self.total_angle * 16)
        )

    # =========================================================
    # ACTIVE ARC WITH GRADIENT + HIGHLIGHT
    # =========================================================
    def _draw_active_arc(self, painter, radius):
        rect = QtCore.QRectF(-radius, -radius, radius * 2, radius * 2)

        ratio = self.speed / self.max_speed
        span = -self.total_angle * ratio

        # Glow externo
        glow_pen = QtGui.QPen(self.primary)
        glow = QtGui.QColor(self.primary)
        glow.setAlpha(70)
        glow_pen.setColor(glow)
        glow_pen.setWidth(22)
        glow_pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(glow_pen)

        painter.drawArc(rect,
                        int((90 - self.start_angle) * 16),
                        int(span * 16))

        # Gradiente angular simulado
        gradient = QtGui.QConicalGradient(0, 0, -self.start_angle)

        gradient.setColorAt(0.0, QtGui.QColor(90, 70, 255))
        gradient.setColorAt(0.25, QtGui.QColor(110, 85, 255))
        gradient.setColorAt(0.50, QtGui.QColor(130, 100, 255))
        gradient.setColorAt(0.75, QtGui.QColor(150, 115, 255))
        gradient.setColorAt(1.0, QtGui.QColor(170, 130, 255))

        pen = QtGui.QPen(QtGui.QBrush(gradient), 12)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)

        painter.drawArc(rect,
                        int((90 - self.start_angle) * 16),
                        int(span * 16))

        # Highlight na ponta
        end_angle = self.start_angle + ratio * self.total_angle
        painter.save()
        painter.rotate(end_angle)
        highlight_pen = QtGui.QPen(QtGui.QColor(200, 180, 255))
        highlight_pen.setWidth(6)
        highlight_pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(highlight_pen)
        painter.drawLine(0, -radius, 0, -radius + 20)
        painter.restore()

    # =========================================================
    # INNER GLOW
    # =========================================================
    def _draw_inner_glow(self, painter, radius):
        inner = radius - 45

        gradient = QtGui.QRadialGradient(0, 0, inner)
        gradient.setColorAt(0, QtGui.QColor(100, 80, 255, 130))
        gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 0))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(QtCore.QPointF(0, 0), inner, inner)

    # =========================================================
    # DIRECTIONAL TOP LIGHT
    # =========================================================
    def _draw_directional_light(self, painter, radius):
        gradient = QtGui.QLinearGradient(0, -radius, 0, 0)
        gradient.setColorAt(0, QtGui.QColor(255, 255, 255, 60))
        gradient.setColorAt(1, QtGui.QColor(255, 255, 255, 0))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(QtCore.QPointF(0, 0), radius, radius)

    # =========================================================
    # TICKS + NUMBERS
    # =========================================================
    def _draw_ticks_and_numbers(self, painter, radius):
        painter.save()

        major_step = 20
        minor_step = 10

        tick_radius = radius - 20

        for value in range(0, self.max_speed + 1, minor_step):
            ratio = value / self.max_speed
            angle = self.start_angle + ratio * self.total_angle

            painter.save()
            painter.rotate(angle)

            if value % major_step == 0:
                pen = QtGui.QPen(QtGui.QColor(220, 220, 255))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawLine(0, -tick_radius, 0, -tick_radius + 18)

                # Número
                painter.save()
                painter.translate(0, -tick_radius + 40)
                painter.rotate(-angle)

                painter.setPen(QtGui.QColor(230, 230, 255))
                painter.setFont(QtGui.QFont("Arial", 14))
                painter.drawText(QtCore.QRectF(-25, -15, 50, 30),
                                 QtCore.Qt.AlignCenter,
                                 str(value))
                painter.restore()
            else:
                pen = QtGui.QPen(QtGui.QColor(200, 200, 255, 120))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(0, -tick_radius, 0, -tick_radius + 10)

            painter.restore()

        painter.restore()

    # =========================================================
    # TEXT WITH SHADOW
    # =========================================================
    def _draw_text(self, painter):
        value = str(int(self.speed))

        # Sombra
        painter.setPen(QtGui.QColor(0, 0, 0, 160))
        painter.setFont(QtGui.QFont("Arial", 70, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRectF(-140, -60, 280, 120),
                         QtCore.Qt.AlignCenter,
                         value)

        # Texto principal
        painter.setPen(QtGui.QColor(240, 240, 255))
        painter.drawText(QtCore.QRectF(-140, -65, 280, 120),
                         QtCore.Qt.AlignCenter,
                         value)

        # Unidade
        painter.setFont(QtGui.QFont("Arial", 16))
        painter.setPen(QtGui.QColor(200, 200, 230))
        painter.drawText(QtCore.QRectF(-140, 40, 280, 60),
                         QtCore.Qt.AlignCenter,
                         "km/h")