import sys
from PyQt5 import QtWidgets
from app.config import TRACK_INVERT_X, TRACK_INVERT_Z
from infrastructure.udp_client import GT7UdpClient
from domain.game_state import GameState
from domain.lap_telemetry import LapTelemetryState
from app.telemetry import TelemetryService
from app.services.track_service import TrackService
from app.ui.dashboard_window import DashboardWindow

def main():
    client = GT7UdpClient()
    client.start()

    state = GameState()
    lap_state = LapTelemetryState(max_laps=10, max_points_per_lap=10000)
    track_service = TrackService(
        lap_state=lap_state,
        min_distance_m=1.2,
        sample_interval_ms=50,
        invert_x=TRACK_INVERT_X,
        invert_z=TRACK_INVERT_Z,
    )
    telemetry = TelemetryService(client, state, track_service=track_service)
    telemetry.start()

    # Qt App (SEMPRE no main thread)
    app = QtWidgets.QApplication(sys.argv)
    window = DashboardWindow(state=state, lap_state=lap_state)
    window.show()
    window.open_track_window()
    if window.track_window is not None:
        window.track_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
