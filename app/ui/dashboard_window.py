from PyQt5 import QtWidgets, QtCore
from domain.game_state import GameState
from app.ui.speed_hauge import SpeedGauge
from app.ui.rpm_gauge import RpmGauge
from app.ui.lap_info_panel import LapInfoPanel
from app.ui.telemetry_graph import TelemetryGraph
from app.ui.fuel_panel import FuelPanel

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