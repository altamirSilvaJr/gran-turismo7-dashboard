import sys
import threading
from PyQt5 import QtWidgets
from infrastructure.udp_client import GT7UdpClient
from infrastructure.crypto import decrypt
from domain.game_state import GameState
from app.telemetry import TelemetryService
from app.ui.dashboard_window import DashboardWindow

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