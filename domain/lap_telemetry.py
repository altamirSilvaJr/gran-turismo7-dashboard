from collections import deque
from dataclasses import dataclass
import threading
from typing import Optional

from domain.track_state import TrackBounds, TrackPoint


@dataclass(frozen=True)
class LapTelemetry:
    lap_number: int
    lap_time: Optional[str]
    fuel_end: Optional[float]
    fuel_consumed: Optional[float]
    color: tuple[int, int, int]
    points: list[TrackPoint]


class LapTelemetryState:
    def __init__(self, max_laps: int = 10, max_points_per_lap: int = 8000):
        self._max_laps = max_laps
        self._max_points_per_lap = max_points_per_lap
        self._laps: dict[int, dict[str, object]] = {}
        self._enabled = True
        self._lock = threading.Lock()
        self._version = 0

    def add_point(
        self,
        lap_number: int,
        x: float,
        z: float,
        timestamp: float,
        throttle: float = 0.0,
        brake: float = 0.0,
    ) -> bool:
        if lap_number <= 0:
            return False

        with self._lock:
            if not self._enabled:
                return False

            if lap_number not in self._laps:
                self._laps[lap_number] = {
                    "lap_time": None,
                    "lap_time_ms": None,
                    "fuel_end": None,
                    "color": self._color_for_lap(lap_number),
                    "points": deque(maxlen=self._max_points_per_lap),
                }
                self._trim_old_laps()
                self._version += 1

            lap = self._laps[lap_number]
            lap_points = lap["points"]
            if not isinstance(lap_points, deque):
                return False
            lap_points.append(
                TrackPoint(
                    x=x,
                    z=z,
                    timestamp=timestamp,
                    throttle=throttle,
                    brake=brake,
                )
            )
            self._version += 1
            return True

    def set_lap_summary(
        self,
        lap_number: int,
        lap_time: Optional[str] = None,
        fuel_end: Optional[float] = None,
    ) -> None:
        if lap_number <= 0:
            return
        with self._lock:
            lap = self._laps.get(lap_number)
            if lap is not None:
                if lap_time:
                    lap["lap_time"] = lap_time
                    lap["lap_time_ms"] = self._lap_time_to_ms(lap_time)
                if fuel_end is not None:
                    lap["fuel_end"] = fuel_end
                self._version += 1

    def get_laps_snapshot(self) -> list[LapTelemetry]:
        with self._lock:
            laps: list[LapTelemetry] = []
            consumptions = self._fuel_consumption_by_lap()
            for lap_number in sorted(self._laps.keys()):
                lap = self._laps[lap_number]
                lap_points = lap["points"]
                if not isinstance(lap_points, deque):
                    continue
                color = lap["color"]
                if not isinstance(color, tuple):
                    color = (0, 220, 255)
                lap_time = lap["lap_time"]
                fuel_end = lap["fuel_end"]
                laps.append(
                    LapTelemetry(
                        lap_number=lap_number,
                        lap_time=lap_time if isinstance(lap_time, str) else None,
                        fuel_end=fuel_end if isinstance(fuel_end, (float, int)) else None,
                        fuel_consumed=consumptions.get(lap_number),
                        color=color,
                        points=list(lap_points),
                    )
                )
            return laps

    def get_last_lap_consumption(self) -> Optional[float]:
        with self._lock:
            consumptions = self._fuel_consumption_by_lap()
            if not consumptions:
                return None
            last_lap = max(consumptions.keys())
            return consumptions[last_lap]

    def get_average_consumption_per_lap(self) -> Optional[float]:
        with self._lock:
            consumptions = self._fuel_consumption_by_lap()
            values = [value for value in consumptions.values() if value > 0]
            if not values:
                return None
            return sum(values) / len(values)

    def estimate_remaining_laps(self, current_fuel: Optional[float]) -> Optional[float]:
        if current_fuel is None or current_fuel <= 0:
            return None
        avg = self.get_average_consumption_per_lap()
        if avg is None or avg <= 0:
            return None
        return current_fuel / avg

    def get_bounds(self, visible_laps: Optional[set[int]] = None) -> Optional[TrackBounds]:
        with self._lock:
            points: list[TrackPoint] = []
            selected = visible_laps if visible_laps is not None else set(self._laps.keys())
            for lap_number in selected:
                lap = self._laps.get(lap_number)
                if lap is None:
                    continue
                lap_points = lap["points"]
                if isinstance(lap_points, deque):
                    points.extend(lap_points)

            if not points:
                return None

            min_x = min(p.x for p in points)
            max_x = max(p.x for p in points)
            min_z = min(p.z for p in points)
            max_z = max(p.z for p in points)
            return TrackBounds(min_x=min_x, max_x=max_x, min_z=min_z, max_z=max_z)

    def reset(self) -> None:
        with self._lock:
            self._laps.clear()
            self._version += 1

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled

    def get_version(self) -> int:
        with self._lock:
            return self._version

    def _trim_old_laps(self) -> None:
        while len(self._laps) > self._max_laps:
            timed_laps: list[tuple[int, int]] = []
            for lap_number, lap in self._laps.items():
                lap_time_ms = lap.get("lap_time_ms")
                if isinstance(lap_time_ms, int):
                    timed_laps.append((lap_number, lap_time_ms))

            if timed_laps:
                worst_lap_number = max(timed_laps, key=lambda item: item[1])[0]
                self._laps.pop(worst_lap_number, None)
            else:
                oldest_lap_number = min(self._laps.keys())
                self._laps.pop(oldest_lap_number, None)

    @staticmethod
    def _lap_time_to_ms(lap_time: str) -> Optional[int]:
        try:
            parts = lap_time.split(":")
            if len(parts) != 3:
                return None
            minutes = int(parts[0])
            seconds = int(parts[1])
            milliseconds = int(parts[2])
            return (minutes * 60_000) + (seconds * 1000) + milliseconds
        except (ValueError, TypeError):
            return None

    def _fuel_consumption_by_lap(self) -> dict[int, float]:
        consumptions: dict[int, float] = {}
        ordered = sorted(self._laps.keys())
        prev_lap_number: Optional[int] = None
        prev_fuel_end: Optional[float] = None
        for lap_number in ordered:
            lap = self._laps[lap_number]
            fuel_end = lap.get("fuel_end")
            if isinstance(fuel_end, (int, float)):
                fuel_end = float(fuel_end)
                if prev_lap_number is not None and prev_fuel_end is not None:
                    consumed = prev_fuel_end - fuel_end
                    if consumed > 0:
                        consumptions[lap_number] = consumed
                prev_lap_number = lap_number
                prev_fuel_end = fuel_end
        return consumptions

    @staticmethod
    def _color_for_lap(lap_number: int) -> tuple[int, int, int]:
        palette = [
            (0, 220, 255),
            (255, 170, 0),
            (80, 220, 100),
            (255, 90, 90),
            (165, 120, 255),
            (255, 255, 90),
            (90, 220, 220),
            (255, 120, 220),
        ]
        return palette[(lap_number - 1) % len(palette)]
