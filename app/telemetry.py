import threading
from typing import Optional

from infrastructure.udp_client import GT7UdpClient
from infrastructure.crypto import decrypt
from infrastructure.packet_parser import parse_telemetry
from domain.game_state import GameState
from app.services.track_service import TrackService

class TelemetryService:
    def __init__(
        self,
        client: GT7UdpClient,
        state: GameState,
        track_service: Optional[TrackService] = None,
    ):
        self.client = client
        self.state = state
        self.track_service = track_service
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
                fuel=data.fuel,
                fuel_capacity=data.fuel_capacity,
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
            if self.track_service is not None and data.physics is not None:
                self.track_service.ingest_position(
                    x=data.physics.position_x,
                    z=data.physics.position_z,
                    current_lap=data.current_lap,
                    last_lap_time=data.last_lap,
                    current_fuel=data.fuel,
                    throttle=data.throttle,
                    brake=data.brake,
                )

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
