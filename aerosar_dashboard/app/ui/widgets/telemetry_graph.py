from typing import List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import pyqtgraph as pg
from app.ui.theme import Theme
from app.models.telemetry import TelemetryHistoryPoint

# Configure global PyQtGraph settings for dark mission-control aesthetic
pg.setConfigOption('background', '#0A0E15')
pg.setConfigOption('foreground', Theme.TEXT_SECONDARY)
pg.setConfigOption('antialias', True)

class SingleTelemetryGraph(QFrame):
    """
    A single compact telemetry history plot with header, current value readout,
    and responsive PyQtGraph curve.
    """
    def __init__(self, title: str, unit: str, line_color: str, fill_color_rgba: Tuple[int, int, int, int]):
        super().__init__()
        self.title_str = title
        self.unit_str = unit
        self.line_color = line_color
        self.fill_color_rgba = fill_color_rgba

        self.setStyleSheet(f"""
            SingleTelemetryGraph {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header bar
        hbar = QHBoxLayout()
        hbar.setContentsMargins(0, 0, 0, 0)

        t_lbl = QLabel(self.title_str)
        t_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; letter-spacing: 0.8px;")
        hbar.addWidget(t_lbl)
        hbar.addStretch()

        self.val_lbl = QLabel(f"-- {self.unit_str}")
        self.val_lbl.setStyleSheet(f"color: {self.line_color}; font-size: 13px; font-weight: bold; font-family: monospace;")
        hbar.addWidget(self.val_lbl)

        layout.addLayout(hbar)

        # PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setFixedHeight(120)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideButtons()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.12)

        # Style axes
        plot_item = self.plot_widget.getPlotItem()
        plot_item.getAxis('left').setStyle(showValues=True, tickLength=4)
        plot_item.getAxis('left').setTextPen(pg.mkPen(Theme.TEXT_SECONDARY))
        plot_item.getAxis('bottom').setStyle(showValues=False, tickLength=0)

        # Curve
        fill_brush = pg.mkBrush(QColor(*self.fill_color_rgba))
        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(self.line_color, width=1.8),
            brush=fill_brush
        )

        layout.addWidget(self.plot_widget)

    def set_data(self, y_values: List[float]):
        if not y_values:
            return
        x_values = list(range(len(y_values)))
        self.curve.setData(x_values, y_values)
        current_val = y_values[-1]
        self.val_lbl.setText(f"{current_val:.1f} {self.unit_str}")


class TelemetryGraphSection(QFrame):
    """
    Compact historical graph section featuring three synchronized time-series plots:
    1. Altitude (m)
    2. Speed (m/s)
    3. Battery (%)
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            TelemetryGraphSection {{
                background-color: transparent;
                border: none;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Section Header
        sec_title = QLabel("TELEMETRY HISTORY (TIME-SERIES)")
        sec_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        main_layout.addWidget(sec_title)

        # Row of 3 compact graphs
        graphs_row = QHBoxLayout()
        graphs_row.setSpacing(14)

        # 1. Altitude Graph
        self.alt_graph = SingleTelemetryGraph(
            title="ALTITUDE",
            unit="m",
            line_color=Theme.ACCENT,
            fill_color_rgba=(0, 180, 216, 30)
        )
        graphs_row.addWidget(self.alt_graph, 1)

        # 2. Speed Graph
        self.spd_graph = SingleTelemetryGraph(
            title="SPEED",
            unit="m/s",
            line_color=Theme.STATUS_SUCCESS,
            fill_color_rgba=(34, 197, 94, 30)
        )
        graphs_row.addWidget(self.spd_graph, 1)

        # 3. Battery Graph
        self.bat_graph = SingleTelemetryGraph(
            title="BATTERY",
            unit="%",
            line_color=Theme.STATUS_WARNING,
            fill_color_rgba=(245, 158, 11, 30)
        )
        graphs_row.addWidget(self.bat_graph, 1)

        main_layout.addLayout(graphs_row)

    def update_history(self, history: List[TelemetryHistoryPoint]):
        if not history:
            return
        alt_data = [pt.altitude for pt in history]
        spd_data = [pt.speed for pt in history]
        bat_data = [pt.battery for pt in history]

        self.alt_graph.set_data(alt_data)
        self.spd_graph.set_data(spd_data)
        self.bat_graph.set_data(bat_data)
