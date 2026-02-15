import threading
import struct
from datetime import datetime
from typing import Optional

from infrastructure.udp_client import GT7UdpClient
from infrastructure.crypto import decrypt
from infrastructure.packet_parser import parse_telemetry
from domain.game_state import GameState

class TelemetryService:
    def __init__(self, client: GT7UdpClient, state: GameState):
        self.client = client
        self.state = state
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _loop(self):
        while self._running:
            data, _ = self.client.receive()
            packet = decrypt(data)
            if not packet:
                continue

            try:
                data = parse_telemetry(packet)
            except ValueError:
                continue

            self.state.update(
                throttle=data.throttle,
                brake=data.brake,
                rpm=data.rpm,
                rpm_warn=data.rpm_warn,
                rpm_rev_limiter=data.rpm_rev_limiter,
                fuel_ratio=data.fuel,
                gear=data.gear,
                suggested_gear=data.suggested_gear,
                speed_kmh=data.speed_kmh,
                best_lap=data.best_lap,
                last_lap=data.last_lap,
                current_lap=data.current_lap,
                total_laps=data.total_laps,
                current_position=data.current_position,
                total_cars=data.total_cars,
                )

            ts = datetime.now().isoformat(timespec="milliseconds")

            thr_s = f"{data.throttle:.3f}"
            br_s = f"{data.brake:.3f}"
            spd_s = f"{data.speed_kmh:.1f}"
            str_s = f"{data.steering:.3f}" if data.steering is not None else "N/A"
            rpm_s = f"{data.rpm}" if data.rpm is not None else "N/A"
            gear_s = f"{data.gear}" if data.gear is not None else "N/A"
            fuel_s = f"{data.fuel:.2f}" if data.fuel is not None else "N/A"
            first16 = packet[:16].hex()

            # print(
            #     f"[{ts}] thr={thr_s} br={br_s} spd={spd_s} "
            #     f"str={str_s} rpm={rpm_s} gear={gear_s} fuel={fuel_s} "
            #     f"len={len(packet)} first16={first16}",
            #     flush=True,
            # )

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False