import time

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np

from domain.track_state import TrackBounds
from domain.lap_telemetry import LapTelemetry


class TrackCanvas(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._auto_fit = True
        self._follow_car = True
        self._brake_threshold = 0.10
        self._throttle_threshold = 0.10

        self._lap_curves: dict[int, dict[str, pg.PlotDataItem]] = {}
        self._hover_by_lap: dict[int, dict[str, np.ndarray]] = {}
        self._hover_downsample_step = 3
        self._hover_interval_s = 0.04
        self._last_hover_ts = 0.0

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget(background="k")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("bottom", "X")
        self.plot.setLabel("left", "Z")
        self.plot.setAspectLocked(True, ratio=1)

        self._car_point = self.plot.plot(
            pen=None,
            symbol="o",
            symbolBrush=(255, 80, 80),
            symbolPen=pg.mkPen(color=(255, 255, 255), width=1),
            symbolSize=9,
        )

        layout.addWidget(self.plot)
        self.plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def set_auto_fit(self, enabled: bool) -> None:
        self._auto_fit = enabled

    def set_follow_car(self, enabled: bool) -> None:
        self._follow_car = enabled

    def set_laps(self, laps: list[LapTelemetry], bounds: TrackBounds | None, visible_laps: set[int]) -> None:
        self._clear_hover_cache()

        if not laps:
            self._remove_all_curves()
            self._car_point.setData([], [])
            return

        active_laps = {lap.lap_number for lap in laps}
        self._sync_curve_pool(active_laps)

        visible = [lap for lap in laps if lap.lap_number in visible_laps]
        self._build_hover_cache(visible)

        for lap in visible:
            self._draw_lap_segments(lap)

        for lap_number in active_laps - visible_laps:
            self._clear_lap_curves(lap_number)

        latest_point = None
        for lap in sorted(visible, key=lambda item: item.lap_number, reverse=True):
            if lap.points:
                latest_point = lap.points[-1]
                break

        if latest_point is None:
            self._car_point.setData([], [])
            return

        self._car_point.setData([latest_point.x], [latest_point.z])

        if self._auto_fit and bounds is not None:
            self.plot.setXRange(bounds.min_x, bounds.max_x, padding=0.08)
            self.plot.setYRange(bounds.min_z, bounds.max_z, padding=0.08)
            return

        if self._follow_car:
            span = 120.0
            x = latest_point.x
            z = latest_point.z
            self.plot.setXRange(x - span, x + span, padding=0.0)
            self.plot.setYRange(z - span, z + span, padding=0.0)

    def _sync_curve_pool(self, active_laps: set[int]) -> None:
        for lap_number in list(self._lap_curves.keys()):
            if lap_number not in active_laps:
                curve_group = self._lap_curves.pop(lap_number)
                for item in curve_group.values():
                    self.plot.removeItem(item)

        for lap_number in active_laps:
            if lap_number in self._lap_curves:
                continue
            self._lap_curves[lap_number] = {
                "solid": self.plot.plot(),
                "dash": self.plot.plot(),
                "dot": self.plot.plot(),
            }

    def _remove_all_curves(self) -> None:
        for lap_number in list(self._lap_curves.keys()):
            curve_group = self._lap_curves.pop(lap_number)
            for item in curve_group.values():
                self.plot.removeItem(item)

    def _clear_lap_curves(self, lap_number: int) -> None:
        curve_group = self._lap_curves.get(lap_number)
        if curve_group is None:
            return
        for item in curve_group.values():
            item.setData([], [])

    def _draw_lap_segments(self, lap: LapTelemetry) -> None:
        curve_group = self._lap_curves.get(lap.lap_number)
        if curve_group is None:
            return
        if len(lap.points) < 2:
            for item in curve_group.values():
                item.setData([], [])
            return

        series = self._build_style_series(lap)
        for style_name in ("solid", "dash", "dot"):
            xs, zs = series[style_name]
            item = curve_group[style_name]
            item.setPen(self._build_pen(lap.color, style_name))
            item.setData(xs, zs, connect="finite")
            item.setZValue(self._style_z(style_name))

    def _build_style_series(self, lap: LapTelemetry):
        points = lap.points
        series = {
            "solid": ([], []),
            "dash": ([], []),
            "dot": ([], []),
        }
        for idx in range(1, len(points)):
            p0 = points[idx - 1]
            p1 = points[idx]
            style_name = self._segment_style_name(p1.throttle, p1.brake)
            xs, zs = series[style_name]
            xs.extend([p0.x, p1.x, np.nan])
            zs.extend([p0.z, p1.z, np.nan])
        return series

    def _build_pen(self, color, style_name: str):
        style_color, width, line_style = self._segment_visual(color=color, style_name=style_name)
        return pg.mkPen(color=style_color, width=width, style=line_style)

    def _style_z(self, style_name: str) -> int:
        if style_name == "dot":
            return 30
        if style_name == "dash":
            return 10
        return 20

    def _segment_style_name(self, throttle: float, brake: float) -> str:
        if brake > self._brake_threshold:
            return "dot"
        if throttle > self._throttle_threshold:
            return "solid"
        return "dash"

    def _segment_visual(self, color, style_name: str):
        base = self._normalize_color(color)
        if style_name == "dot":
            brake_color = self._blend(base, (255, 70, 70), 0.55)
            return (*brake_color, 255), 4, QtCore.Qt.DotLine
        if style_name == "dash":
            coast_color = self._blend(base, (180, 180, 180), 0.55)
            return (*coast_color, 130), 1, QtCore.Qt.DashLine
        return (*base, 255), 2, QtCore.Qt.SolidLine

    def _normalize_color(self, color):
        if isinstance(color, tuple) and len(color) >= 3:
            return (int(color[0]), int(color[1]), int(color[2]))
        return (0, 220, 255)

    def _blend(self, source, target, ratio: float):
        ratio = max(0.0, min(1.0, ratio))
        return (
            int(source[0] * (1.0 - ratio) + target[0] * ratio),
            int(source[1] * (1.0 - ratio) + target[1] * ratio),
            int(source[2] * (1.0 - ratio) + target[2] * ratio),
        )

    def _clear_hover_cache(self) -> None:
        self._hover_by_lap.clear()

    def _build_hover_cache(self, laps: list[LapTelemetry]) -> None:
        step = max(1, self._hover_downsample_step)
        for lap in laps:
            if not lap.points:
                continue
            sampled_points = lap.points[::step]
            self._hover_by_lap[lap.lap_number] = {
                "x": np.array([p.x for p in sampled_points], dtype=float),
                "z": np.array([p.z for p in sampled_points], dtype=float),
                "throttle": np.array([p.throttle for p in sampled_points], dtype=float),
                "brake": np.array([p.brake for p in sampled_points], dtype=float),
            }

    def _on_mouse_moved(self, scene_pos) -> None:
        now = time.monotonic()
        if now - self._last_hover_ts < self._hover_interval_s:
            return
        self._last_hover_ts = now

        if not self._hover_by_lap:
            QtWidgets.QToolTip.hideText()
            return

        if not self.plot.sceneBoundingRect().contains(scene_pos):
            QtWidgets.QToolTip.hideText()
            return

        mouse_point = self.plot.plotItem.vb.mapSceneToView(scene_pos)
        mx = mouse_point.x()
        mz = mouse_point.y()

        view = self.plot.plotItem.viewRange()
        x_span = float(view[0][1] - view[0][0])
        z_span = float(view[1][1] - view[1][0])
        hover_radius = (max(x_span, z_span) * 0.02) ** 2

        rows = []
        for lap_number in sorted(self._hover_by_lap.keys()):
            lap_data = self._hover_by_lap[lap_number]
            dx = lap_data["x"] - mx
            dz = lap_data["z"] - mz
            distances = dx * dx + dz * dz
            idx = int(np.argmin(distances))
            nearest = float(distances[idx])
            if nearest > hover_radius:
                continue

            throttle_pct = float(lap_data["throttle"][idx]) * 100.0
            brake_pct = float(lap_data["brake"][idx]) * 100.0
            rows.append((lap_number, throttle_pct, brake_pct))

        if not rows:
            QtWidgets.QToolTip.hideText()
            return

        lines = ["Volta | Acel. | Freio", "----------------------"]
        for lap_number, throttle_pct, brake_pct in rows:
            lines.append(f"{lap_number:>5} | {throttle_pct:>5.1f}% | {brake_pct:>5.1f}%")
        text = "<pre>" + "\n".join(lines) + "</pre>"
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), text, self.plot)
