import sys
import threading
from collections import deque
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
from infrastructure.udp_client import GT7UdpClient
from infrastructure.crypto import decrypt
from domain.game_state import GameState
import struct
from app.telemetry import TelemetryService
import numpy as np
from turtle import pen
import math

class DashboardWindow(QtWidgets.QWidget):

    def __init__(self, state: GameState = None):
        super().__init__()
        self.setWindowTitle("Racing Dashboard")
        self.setMinimumSize(1500, 700)
        self.setStyleSheet("background-color: black;")
        self.state = state

        self.refrehsh_timer = QtCore.QTimer()
        self.refrehsh_timer.timeout.connect(self.refresh)
        self.refrehsh_timer.start(16)  # Refresh every 16ms (~60 FPS)

        # =========================
        # Layout principal horizontal
        # =========================
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # =========================
        # Widgets
        # =========================
        self.speed_gauge = SpeedGauge()
        self.rpm_gauge = RpmGauge()
        self.lap_panel = LapInfoPanel()
        self.graph_panel = TelemetryGraph()
        self.fuel_panel = FuelPanel()

        # =========================
        # Coluna Central
        # =========================
        center_widget = QtWidgets.QWidget()
        center_layout = QtWidgets.QVBoxLayout(center_widget)
        center_layout.setSpacing(15)
        center_layout.setContentsMargins(0, 0, 0, 0)

        center_layout.addWidget(self.lap_panel, stretch=1)
        center_layout.addWidget(self.graph_panel, stretch=2)
        center_layout.addWidget(self.fuel_panel, stretch=1)

        # =========================
        # Adiciona ao layout principal
        # =========================
        main_layout.addWidget(self.speed_gauge, stretch=1)
        main_layout.addWidget(center_widget, stretch=1)
        main_layout.addWidget(self.rpm_gauge, stretch=1)
    
    def refresh(self):
        # Atualiza dados dos widgets
        self.speed_gauge.speed = self.state.speed_kmh
        self.rpm_gauge.rpm = self.state.rpm
        self.rpm_gauge.rpm_warn = self.state.rpm_warn
        self.rpm_gauge.rpm_rev_limiter = self.state.rpm_rev_limiter
        self.graph_panel.set_inputs(
            self.state.throttle,
            self.state.brake
        )
        self.fuel_panel.fuel_percent = self.state.fuel_ratio
        self.lap_panel.gear = str(self.state.gear)
        self.lap_panel.suggested_gear = str(self.state.suggested_gear)
        self.lap_panel.best_lap = self.state.best_lap
        self.lap_panel.last_lap = self.state.last_lap
        self.lap_panel.current_lap = self.state.current_lap
        self.lap_panel.total_laps = self.state.total_laps
        self.lap_panel.position = self.state.current_position
        self.lap_panel.total_cars = self.state.total_cars
        

        self.update()

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

def main():
    client = GT7UdpClient()
    client.start()

    state = GameState()
    telemetry = TelemetryService(client, state)
    telemetry.start()
    # Thread de rede
    threading.Thread(
        target=telemetry._loop,
        args=(),
        daemon=True
    ).start()

    # Qt App (SEMPRE no main thread)
    app = QtWidgets.QApplication(sys.argv)
    window = DashboardWindow(state=state)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()