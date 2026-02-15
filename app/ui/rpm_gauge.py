from PyQt5 import QtWidgets, QtCore, QtGui

class RpmGauge(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 500)
        self.rpm = 0
        self.rpm_warn = 0
        self.rpm_rev_limiter = 0

        self.start_angle = -210
        self.total_angle = 240

        self.blink_state = True
        self.blink_timer = QtCore.QTimer()
        self.blink_timer.timeout.connect(self._toggle_blink)
        self.blink_timer.start(70)   # velocidade do piscar

        self.primary = QtGui.QColor(255, 80, 80)
        self.outer_ring = QtGui.QColor(110, 120, 200)
    
    def _toggle_blink(self):
        if self.rpm_warn > 0 and self.rpm >= self.rpm_warn:
            self.blink_state = not self.blink_state
            self.update()
        else:
            self.blink_state = True

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
        self._draw_red_zone(painter, radius)
        self._draw_active_arc(painter, radius)
        self._draw_inner_glow(painter, radius)
        self._draw_directional_light(painter, radius)
        self._draw_ticks_and_numbers(painter, radius)
        self._draw_text(painter)

    def _draw_directional_light(self, painter, radius):
        """
        Cria iluminação direcional superior simulando reflexo em vidro.
        """

        painter.save()

        # Gradiente linear do topo para o centro
        gradient = QtGui.QLinearGradient(0, -radius, 0, 0)
        gradient.setColorAt(0.0, QtGui.QColor(255, 255, 255, 70))
        gradient.setColorAt(0.4, QtGui.QColor(255, 255, 255, 30))
        gradient.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)

        painter.drawEllipse(QtCore.QPointF(0, 0), radius, radius)

        painter.restore()

    # =========================================================
    # BACKGROUND
    # =========================================================
    def _draw_background(self, painter, radius):
        gradient = QtGui.QRadialGradient(0, 0, radius)
        gradient.setColorAt(0, QtGui.QColor(30, 25, 45))
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
    # RED ZONE
    # =========================================================
    def _draw_red_zone(self, painter, radius):
        if self.rpm_rev_limiter == 0:
            return

        rect = QtCore.QRectF(-radius, -radius, radius * 2, radius * 2)

        warn_ratio = self.rpm_warn / self.rpm_rev_limiter
        red_span_ratio = 1.0 - warn_ratio

        start = self.start_angle + warn_ratio * self.total_angle
        span = -self.total_angle * red_span_ratio

        pen = QtGui.QPen(QtGui.QColor(255, 60, 60))
        pen.setWidth(8)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)

        painter.drawArc(
            rect,
            int((90 - start) * 16),
            int(span * 16)
        )

    # =========================================================
    # ACTIVE ARC
    # =========================================================
    def _draw_active_arc(self, painter, radius):
        rect = QtCore.QRectF(-radius, -radius, radius * 2, radius * 2)

        if self.rpm_rev_limiter > 0:
            ratio = self.rpm / self.rpm_rev_limiter
        else:
            ratio = 0
        if self.rpm >= self.rpm_warn and not self.blink_state:
            glow_alpha = 255 if self.blink_state else 20
            arc_intensity = 255 if self.blink_state else 150
            pulse_width = 38 if self.blink_state else 18
        else:
            glow_alpha = 80
            arc_intensity = 255
            pulse_width = 22
        span = -self.total_angle * ratio

        # Glow
        glow_pen = QtGui.QPen(self.primary)
        glow_color = QtGui.QColor(self.primary)
        glow_color.setAlpha(glow_alpha)
        glow_pen.setColor(glow_color)
        glow_pen.setWidth(30)
        glow_pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(glow_pen)

        painter.drawArc(rect,
                        int((90 - self.start_angle) * 16),
                        int(span * 16))

        # Gradiente angular
        gradient = QtGui.QConicalGradient(0, 0, -self.start_angle)

        gradient.setColorAt(0.0, QtGui.QColor(255, 170, 170))
        gradient.setColorAt(0.30, QtGui.QColor(255, 130, 130))
        gradient.setColorAt(0.60, QtGui.QColor(255, 90, 90))
        gradient.setColorAt(0.85, QtGui.QColor(255, 70, 70))
        gradient.setColorAt(1.0, QtGui.QColor(arc_intensity, 60, 60))

        pen = QtGui.QPen(QtGui.QBrush(gradient), 12)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)

        painter.drawArc(rect,
                        int((90 - self.start_angle) * 16),
                        int(span * 16))

        # Highlight ponta
        end_angle = self.start_angle + ratio * self.total_angle
        painter.save()
        painter.rotate(end_angle)
        highlight_pen = QtGui.QPen(QtGui.QColor(255, 200, 200))
        highlight_pen.setWidth(6)
        painter.setPen(highlight_pen)
        painter.drawLine(0, -radius, 0, -radius + 20)
        painter.restore()

    # =========================================================
    # INNER GLOW
    # =========================================================
    def _draw_inner_glow(self, painter, radius):
        inner = radius - 45
        ratio = self.rpm / self.rpm_rev_limiter
        if self.rpm_warn > 0 and self.rpm >= self.rpm_warn:
            alpha = 200 if self.blink_state else 60
        else:
            alpha = 120

        gradient = QtGui.QRadialGradient(0, 0, inner)
        gradient.setColorAt(0, QtGui.QColor(255, 80, 80, alpha))
        gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 0))

        painter.setBrush(gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(QtCore.QPointF(0, 0), inner, inner)

    # =========================================================
    # TICKS + NUMBERS
    # =========================================================
    def _draw_ticks_and_numbers(self, painter, radius):
        painter.save()

        major_step = 1000
        minor_step = 500

        tick_radius = radius - 20

        for value in range(0, self.rpm_rev_limiter + 1, minor_step):
            ratio = value / self.rpm_rev_limiter
            angle = self.start_angle + ratio * self.total_angle

            painter.save()
            painter.rotate(angle)

            if value % major_step == 0:
                pen = QtGui.QPen(QtGui.QColor(230, 230, 255))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawLine(0, -tick_radius, 0, -tick_radius + 18)

                painter.save()
                painter.translate(0, -tick_radius + 40)
                painter.rotate(-angle)

                painter.setFont(QtGui.QFont("Arial", 14))
                painter.drawText(QtCore.QRectF(-25, -15, 50, 30),
                                 QtCore.Qt.AlignCenter,
                                 str(value // 1000))
                painter.restore()
            else:
                pen = QtGui.QPen(QtGui.QColor(200, 200, 255, 120))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(0, -tick_radius, 0, -tick_radius + 10)

            painter.restore()

        painter.restore()

    # =========================================================
    # TEXT
    # =========================================================
    def _draw_text(self, painter):
        value = str(int(self.rpm))
        ratio = self.rpm / self.rpm_rev_limiter

        if self.rpm >= self.rpm_warn and not self.blink_state:
            return

        painter.setPen(QtGui.QColor(0, 0, 0, 160))
        painter.setFont(QtGui.QFont("Arial", 60, QtGui.QFont.Bold))
        painter.drawText(QtCore.QRectF(-140, -60, 280, 120),
                         QtCore.Qt.AlignCenter,
                         value)

        painter.setPen(QtGui.QColor(240, 240, 255))
        painter.drawText(QtCore.QRectF(-140, -65, 280, 120),
                         QtCore.Qt.AlignCenter,
                         value)

        painter.setFont(QtGui.QFont("Arial", 16))
        painter.setPen(QtGui.QColor(200, 200, 230))
        painter.drawText(QtCore.QRectF(-140, 40, 280, 60),
                         QtCore.Qt.AlignCenter,
                         "RPM x1000")