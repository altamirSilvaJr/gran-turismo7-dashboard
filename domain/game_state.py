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
    rpm: float = 0.0
    rpm_warn: float = 0.0
    rpm_rev_limiter: float = 0.0
    fuel_ratio: float = 0.0
    gear: int = 0
    suggested_gear: int = 0
    best_lap: int = 0
    last_lap: int = 0
    current_lap: int = 0
    total_laps: int = 0
    current_position: int = 0
    total_cars: int = 0
    

    def update(
        self,
        *,
        speed_kmh: float,
        throttle: float,
        brake: float,
        rpm: float = 0.0,
        rpm_warn: float = 0.0,
        rpm_rev_limiter: float = 0.0,
        fuel_ratio: float = 0.0,
        gear: int = 0,
        suggested_gear: int = 0,
        best_lap: int = 0,
        last_lap: int = 0,
        current_lap: int = 0,
        total_laps: int = 0,
        current_position: int = 0,
        total_cars: int = 0,
    ):
        self.timestamp = time.time()
        self.throttle = throttle
        self.brake = brake
        self.rpm = rpm
        self.rpm_warn = rpm_warn
        self.rpm_rev_limiter = rpm_rev_limiter
        self.fuel_ratio = fuel_ratio
        self.gear = gear
        self.speed_kmh = speed_kmh
        self.best_lap = best_lap
        self.last_lap = last_lap
        self.current_lap = current_lap
        self.total_laps = total_laps
        self.current_position = current_position
        self.total_cars = total_cars
        self.suggested_gear = suggested_gear


