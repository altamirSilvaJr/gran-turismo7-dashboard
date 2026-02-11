import sys
import threading
from collections import deque

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from infrastructure.udp_client import GT7UdpClient
from infrastructure.crypto import decrypt
from domain.game_state import GameState
import struct
import numpy as np

def telemetry_loop(client: GT7UdpClient, state: GameState):
    while True:
        data, _ = client.receive()
        packet = decrypt(data)

        if not packet:
            continue

        throttle = packet[0x91] / 255.0
        brake = packet[0x92] / 255.0

        speed_mps = struct.unpack_from("<f", packet, 0x4C)[0]
        speed_kmh = speed_mps * 3.6

        state.update(
            throttle=throttle,
            brake=brake,
            speed_kmh=speed_kmh
        )

class TelemetryWindow(QtWidgets.QMainWindow):
    def __init__(self, state: GameState):
        super().__init__()
        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.plot = pg.PlotWidget()

        layout.addWidget(self.plot, stretch=3)

        # ===== Speedometer =====
        self.speed_plot = pg.PlotWidget()
        self.speed_plot.setAspectLocked()
        self.speed_plot.hideAxis("bottom")
        self.speed_plot.hideAxis("left")
        self.speed_plot.setXRange(-1.2, 1.2)
        self.speed_plot.setYRange(-1.2, 1.2)

        layout.addWidget(self.speed_plot, stretch=1)

        self.speed_pointer = pg.PlotDataItem(
            [0, 0],
            [0, 0.9],
            pen=pg.mkPen("cyan", width=3)
        )
        self.speed_plot.addItem(self.speed_pointer)


        self.state = state

        self.setWindowTitle("GT7 Telemetry - Throttle / Brake")
        self.resize(900, 400)

        self.plot.setYRange(0, 1.05)
        self.plot.showGrid(x=True, y=True)

        self.throttle_curve = self.plot.plot(
            pen=pg.mkPen("lime", width=2),
            name="Throttle"
        )
        self.brake_curve = self.plot.plot(
            pen=pg.mkPen("red", width=2),
            name="Brake"
        )

        self.buffer_size = 150
        self.throttle_buffer = deque([0.0] * self.buffer_size, maxlen=self.buffer_size)
        self.brake_buffer = deque([0.0] * self.buffer_size, maxlen=self.buffer_size)

        self.speed_text = pg.TextItem(
            text="0 km/h",
            anchor=(0.5, 0.5),
            color="white"
        )
        self.speed_text.setFont(pg.QtGui.QFont("Arial", 18, pg.QtGui.QFont.Bold))
        self.speed_text.setPos(0, -0.2)
        self.speed_plot.addItem(self.speed_text)

        # Timer da GUI (≈ 60 FPS)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(16)

    def update_plot(self):
        # ===== buffers existentes =====
        self.throttle_buffer.append(self.state.throttle)
        self.brake_buffer.append(self.state.brake)

        self.throttle_curve.setData(self.throttle_buffer)
        self.brake_curve.setData(self.brake_buffer)

        # ===== SPEEDOMETER =====
        speed = max(0.0, self.state.speed_kmh)
        max_speed = 300.0

        ratio = min(speed / max_speed, 1.0)

        # -135° → +135°
        angle = -135 + (270 * ratio)
        rad = angle * 3.14159 / 180.0

        x = 0.9 * np.sin(rad)
        y = 0.9 * np.cos(rad)

        self.speed_pointer.setData([0, x], [0, y])
        self.speed_text.setText(f"{int(speed)} km/h")
        self.speed_text.setFont(pg.QtGui.QFont("Arial", 18, pg.QtGui.QFont.Bold))
        self.speed_text.setPos(0, -0.2)
        self.speed_plot.addItem(self.speed_text)


def main():
    client = GT7UdpClient()
    client.start()

    state = GameState()

    # Thread de rede
    threading.Thread(
        target=telemetry_loop,
        args=(client, state),
        daemon=True
    ).start()

    # Qt App (SEMPRE no main thread)
    app = QtWidgets.QApplication(sys.argv)
    window = TelemetryWindow(state)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
