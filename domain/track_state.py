from collections import deque
from dataclasses import dataclass
import threading
from typing import Optional


@dataclass(frozen=True)
class TrackPoint:
    x: float
    z: float
    timestamp: float
    throttle: float = 0.0
    brake: float = 0.0


@dataclass(frozen=True)
class TrackBounds:
    min_x: float
    max_x: float
    min_z: float
    max_z: float


class TrackState:
    def __init__(self, max_points: int = 20000):
        self._points: deque[TrackPoint] = deque(maxlen=max_points)
        self._enabled = True
        self._lock = threading.Lock()

    def add_point(self, x: float, z: float, timestamp: float) -> bool:
        with self._lock:
            if not self._enabled:
                return False

            point = TrackPoint(x=x, z=z, timestamp=timestamp)
            self._points.append(point)
            return True

    def get_points_snapshot(self) -> list[TrackPoint]:
        with self._lock:
            return list(self._points)

    def has_points(self) -> bool:
        with self._lock:
            return bool(self._points)

    def get_bounds(self) -> Optional[TrackBounds]:
        with self._lock:
            if not self._points:
                return None
            min_x = min(p.x for p in self._points)
            max_x = max(p.x for p in self._points)
            min_z = min(p.z for p in self._points)
            max_z = max(p.z for p in self._points)
            return TrackBounds(
                min_x=min_x,
                max_x=max_x,
                min_z=min_z,
                max_z=max_z,
            )

    def reset(self) -> None:
        with self._lock:
            self._points.clear()

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled
