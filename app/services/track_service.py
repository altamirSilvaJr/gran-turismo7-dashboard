import math
import time
from typing import Optional

from domain.lap_telemetry import LapTelemetryState


class TrackService:
    def __init__(
        self,
        lap_state: LapTelemetryState,
        min_distance_m: float = 1.5,
        sample_interval_ms: int = 80,
        invert_x: bool = False,
        invert_z: bool = False,
    ):
        self.lap_state = lap_state
        self.min_distance_m = min_distance_m
        self.sample_interval_s = sample_interval_ms / 1000.0
        self.invert_x = invert_x
        self.invert_z = invert_z
        self._capture_paused = False

        self._last_x: Optional[float] = None
        self._last_z: Optional[float] = None
        self._last_ts: float = 0.0
        self._current_lap: Optional[int] = None

    def ingest_position(
        self,
        x: float,
        z: float,
        current_lap: Optional[int],
        last_lap_time: Optional[str],
        current_fuel: Optional[float],
        throttle: Optional[float] = None,
        brake: Optional[float] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        if self._capture_paused:
            return

        if current_lap is None or current_lap <= 0:
            return

        self._handle_lap_transition(
            current_lap=current_lap,
            last_lap_time=last_lap_time,
            current_fuel=current_fuel,
        )

        x, z = self._transform_position(x=x, z=z)

        ts = timestamp if timestamp is not None else time.time()
        if not self._should_add_point(x=x, z=z, timestamp=ts):
            return

        added = self.lap_state.add_point(
            lap_number=current_lap,
            x=x,
            z=z,
            timestamp=ts,
            throttle=throttle if throttle is not None else 0.0,
            brake=brake if brake is not None else 0.0,
        )
        if not added:
            return

        self._last_x = x
        self._last_z = z
        self._last_ts = ts
        self._current_lap = current_lap

    def _handle_lap_transition(
        self,
        current_lap: int,
        last_lap_time: Optional[str],
        current_fuel: Optional[float],
    ) -> None:
        if self._current_lap is None:
            self._current_lap = current_lap
            return

        if current_lap == self._current_lap:
            return

        self.lap_state.set_lap_summary(
            lap_number=self._current_lap,
            lap_time=last_lap_time,
            fuel_end=current_fuel,
        )
        self._current_lap = current_lap
        self._last_x = None
        self._last_z = None
        self._last_ts = 0.0

    def _transform_position(self, x: float, z: float) -> tuple[float, float]:
        if self.invert_x:
            x = -x
        if self.invert_z:
            z = -z
        return x, z

    def _should_add_point(self, x: float, z: float, timestamp: float) -> bool:
        if self._last_x is None or self._last_z is None:
            return True

        if (timestamp - self._last_ts) < self.sample_interval_s:
            return False

        dx = x - self._last_x
        dz = z - self._last_z
        distance = math.hypot(dx, dz)
        return distance >= self.min_distance_m

    def clear_track(self) -> None:
        self.lap_state.reset()
        self._last_x = None
        self._last_z = None
        self._last_ts = 0.0
        self._current_lap = None

    def pause_capture(self) -> None:
        self._capture_paused = True
        self.lap_state.set_enabled(False)

    def resume_capture(self) -> None:
        self._capture_paused = False
        self.lap_state.set_enabled(True)
