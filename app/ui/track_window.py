from PyQt5 import QtCore, QtWidgets

from domain.lap_telemetry import LapTelemetryState
from app.ui.track_canvas import TrackCanvas


class TrackWindow(QtWidgets.QWidget):
    def __init__(self, lap_state: LapTelemetryState):
        super().__init__()
        self.lap_state = lap_state
        self._lap_buttons: dict[int, QtWidgets.QPushButton] = {}
        self._visible_laps: set[int] = set()
        self._last_data_version = -1
        self._dirty = True

        self.setWindowTitle("Track Map")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(
            "QWidget { background-color: black; color: white; }"
            "QPushButton { color: white; background-color: #1f1f1f; "
            "border: 1px solid #4a4a4a; padding: 6px 10px; }"
            "QPushButton:hover { background-color: #2c2c2c; }"
        )

        layout = QtWidgets.QVBoxLayout(self)
        controls = QtWidgets.QHBoxLayout()

        self.auto_fit_checkbox = QtWidgets.QCheckBox("Auto fit")
        self.auto_fit_checkbox.setChecked(True)
        self.auto_fit_checkbox.stateChanged.connect(self._on_auto_fit_changed)

        self.follow_checkbox = QtWidgets.QCheckBox("Follow car")
        self.follow_checkbox.setChecked(True)
        self.follow_checkbox.stateChanged.connect(self._on_follow_changed)

        self.clear_button = QtWidgets.QPushButton("Clear track")
        self.clear_button.clicked.connect(self.clear_track)

        controls.addWidget(self.auto_fit_checkbox)
        controls.addWidget(self.follow_checkbox)
        controls.addStretch(1)
        controls.addWidget(self.clear_button)

        self.laps_scroll = QtWidgets.QScrollArea()
        self.laps_scroll.setWidgetResizable(True)
        self.laps_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.laps_scroll_content = QtWidgets.QWidget()
        self.laps_buttons_layout = QtWidgets.QHBoxLayout(self.laps_scroll_content)
        self.laps_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.laps_buttons_layout.setSpacing(6)
        self.laps_buttons_layout.addStretch(1)
        self.laps_scroll.setWidget(self.laps_scroll_content)

        legend_layout = QtWidgets.QHBoxLayout()
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(12)
        legend_layout.addWidget(self._legend_item("Aceleração", "#2aaeff", "solid"))
        legend_layout.addWidget(self._legend_item("Sem pedal", "#bebebe", "dashed"))
        legend_layout.addWidget(self._legend_item("Frenagem", "#ff4646", "dotted"))
        legend_layout.addStretch(1)

        self.canvas = TrackCanvas()

        layout.addLayout(controls)
        layout.addWidget(self.laps_scroll)
        layout.addLayout(legend_layout)
        layout.addWidget(self.canvas, stretch=1)

        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(120)

    def _on_auto_fit_changed(self, state: int) -> None:
        self.canvas.set_auto_fit(state == QtCore.Qt.Checked)
        self._dirty = True

    def _on_follow_changed(self, state: int) -> None:
        self.canvas.set_follow_car(state == QtCore.Qt.Checked)
        self._dirty = True

    def refresh(self) -> None:
        data_version = self.lap_state.get_version()
        if data_version == self._last_data_version and not self._dirty:
            return

        laps = self.lap_state.get_laps_snapshot()
        self._sync_lap_buttons(laps)
        bounds = self.lap_state.get_bounds(visible_laps=self._visible_laps)
        self.canvas.set_laps(laps=laps, bounds=bounds, visible_laps=self._visible_laps)
        self._last_data_version = data_version
        self._dirty = False

    def clear_track(self) -> None:
        self.lap_state.reset()
        for button in self._lap_buttons.values():
            self.laps_buttons_layout.removeWidget(button)
            button.deleteLater()
        self._lap_buttons.clear()
        self._visible_laps.clear()
        self._dirty = True

    def _sync_lap_buttons(self, laps) -> None:
        current_laps = {lap.lap_number for lap in laps}

        for lap_number in list(self._lap_buttons.keys()):
            if lap_number not in current_laps:
                button = self._lap_buttons.pop(lap_number)
                self.laps_buttons_layout.removeWidget(button)
                button.deleteLater()
                self._visible_laps.discard(lap_number)

        for lap in laps:
            if lap.lap_number not in self._lap_buttons:
                button = QtWidgets.QPushButton()
                button.setCheckable(True)
                button.setChecked(True)
                button.clicked.connect(
                    lambda checked, lap_number=lap.lap_number: self._toggle_lap_visibility(
                        lap_number=lap_number,
                        visible=checked,
                    )
                )
                button.setStyleSheet(
                    f"QPushButton {{ color: white; border: 1px solid rgb({lap.color[0]}, {lap.color[1]}, {lap.color[2]}); "
                    "padding: 4px 8px; border-radius: 4px; background-color: #1c1c1c; }"
                    f"QPushButton:checked {{ background-color: rgba({lap.color[0]}, {lap.color[1]}, {lap.color[2]}, 140); }}"
                )
                self._lap_buttons[lap.lap_number] = button
                self.laps_buttons_layout.insertWidget(self.laps_buttons_layout.count() - 1, button)
                self._visible_laps.add(lap.lap_number)

            label = f"L{lap.lap_number}"
            if lap.lap_time:
                label = f"{label} {lap.lap_time}"
            self._lap_buttons[lap.lap_number].setText(label)

    def _toggle_lap_visibility(self, lap_number: int, visible: bool) -> None:
        if visible:
            self._visible_laps.add(lap_number)
        else:
            self._visible_laps.discard(lap_number)
        self._dirty = True

    def _legend_item(self, label: str, color: str, line_style: str) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        item_layout = QtWidgets.QHBoxLayout(container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(6)

        line = QtWidgets.QFrame()
        line.setFixedSize(28, 10)
        if line_style == "dotted":
            border_style = "dotted"
        elif line_style == "dashed":
            border_style = "dashed"
        else:
            border_style = "solid"
        line.setStyleSheet(
            f"QFrame {{ border-top: 3px {border_style} {color}; background: transparent; }}"
        )

        text = QtWidgets.QLabel(label)
        text.setStyleSheet("color: #e0e0e0;")

        item_layout.addWidget(line)
        item_layout.addWidget(text)
        return container
