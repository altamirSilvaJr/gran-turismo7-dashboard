from dataclasses import dataclass
import time


@dataclass
class GameState:
    # Meta
    timestamp: float = 0.0

    # Dinâmica
    speed_kmh: float = 0.0
    throttle: float = 0.0
    brake: float = 0.0
    

    def update(
        self,
        *,
        speed_kmh: float,
        throttle: float,
        brake: float,
    ):
        self.timestamp = time.time()
        self.throttle = throttle
        self.brake = brake
        self.speed_kmh = speed_kmh
