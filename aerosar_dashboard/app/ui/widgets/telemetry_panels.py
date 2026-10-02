from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt
from app.ui.theme import Theme
from app.models.telemetry import (
    FlightTelemetry, PositionTelemetry, PowerTelemetry,
    CommunicationTelemetry, SensorStatus, FlightControllerStatus,
    CompanionComputerStatus
)

class BaseTelemetryPanel(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setStyleSheet(f"""
            BaseTelemetryPanel {{
                background-color: {Theme.BG_PANEL};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
            }}
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(10)

        # Panel Header
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 0.8px;")
        self.layout.addWidget(t_lbl)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"border: none; border-top: 1px solid {Theme.BORDER};")
        self.layout.addWidget(div)


class FlightTelemetryPanel(BaseTelemetryPanel):
    """
    Displays live flight telemetry: Altitude, Speed, Heading, Vertical Speed, Roll, Pitch, Yaw.
    """
    def __init__(self):
        super().__init__("FLIGHT TELEMETRY")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_alt = self._add_item(grid, 0, 0, "ALTITUDE", "N/A", Theme.ACCENT)
        self.val_spd = self._add_item(grid, 0, 1, "SPEED", "N/A", Theme.TEXT_PRIMARY)
        self.val_vs = self._add_item(grid, 1, 0, "VERTICAL SPEED", "N/A", Theme.TEXT_PRIMARY)
        self.val_heading = self._add_item(grid, 1, 1, "HEADING", "N/A", Theme.ACCENT)
        self.val_roll = self._add_item(grid, 2, 0, "ROLL", "N/A", Theme.TEXT_SECONDARY)
        self.val_pitch = self._add_item(grid, 2, 1, "PITCH", "N/A", Theme.TEXT_SECONDARY)
        self.val_yaw = self._add_item(grid, 3, 0, "YAW", "N/A", Theme.TEXT_SECONDARY)

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, f: FlightTelemetry):
        self.val_alt.setText(f"{f.altitude:.1f} m")
        self.val_spd.setText(f"{f.speed:.1f} m/s")
        sign = "+" if f.vertical_speed >= 0 else ""
        self.val_vs.setText(f"{sign}{f.vertical_speed:.1f} m/s")
        self.val_heading.setText(f"{int(f.heading)}°")
        self.val_roll.setText(f"{f.roll:+.1f}°")
        self.val_pitch.setText(f"{f.pitch:+.1f}°")
        self.val_yaw.setText(f"{f.yaw:.1f}°")


class PositionPanel(BaseTelemetryPanel):
    """
    Displays local 3D spatial position (X, Y, Z in meters) within the LOCAL / SLAM frame.
    """
    def __init__(self):
        super().__init__("POSITION & COORDINATES")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_x = self._add_item(grid, 0, 0, "X (LOCAL)", "N/A")
        self.val_y = self._add_item(grid, 0, 1, "Y (LOCAL)", "N/A")
        self.val_z = self._add_item(grid, 1, 0, "Z (ALTITUDE)", "N/A")
        self.val_head = self._add_item(grid, 1, 1, "HEADING", "N/A")

        self.layout.addLayout(grid)

        # Coordinate Frame Notice
        f_box = QFrame()
        f_box.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        fl = QVBoxLayout(f_box)
        fl.setContentsMargins(8, 6, 8, 6)
        fl.setSpacing(2)

        fl_title = QLabel("COORDINATE FRAME: LOCAL / SLAM")
        fl_title.setStyleSheet(f"color: {Theme.ACCENT}; font-size: 10px; font-weight: bold; font-family: monospace;")
        fl_desc = QLabel("Relative robotics metric space — GPS-denied localization")
        fl_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-style: italic;")

        fl.addWidget(fl_title)
        fl.addWidget(fl_desc)
        self.layout.addWidget(f_box)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 14px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, p: PositionTelemetry):
        self.val_x.setText(f"{p.x:.1f} m")
        self.val_y.setText(f"{p.y:.1f} m")
        self.val_z.setText(f"{p.z:.1f} m")
        self.val_head.setText(f"{int(p.heading)}°")


class PowerPanel(BaseTelemetryPanel):
    """
    Displays battery state of charge, voltage, current draw, and power consumption.
    """
    def __init__(self):
        super().__init__("POWER & BATTERY")
        self._setup_content()

    def _setup_content(self):
        # Battery percentage & visual charge bar
        top_row = QHBoxLayout()
        t_lbl = QLabel("BATTERY")
        t_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        self.val_battery = QLabel("0%")
        self.val_battery.setStyleSheet(f"color: {Theme.STATUS_SUCCESS}; font-size: 16px; font-weight: bold; font-family: monospace;")
        top_row.addWidget(t_lbl)
        top_row.addStretch()
        top_row.addWidget(self.val_battery)
        self.layout.addLayout(top_row)

        self.bar_battery = QProgressBar()
        self.bar_battery.setFixedHeight(6)
        self.bar_battery.setTextVisible(False)
        self.bar_battery.setValue(0)
        self._apply_battery_bar_style(0)
        self.layout.addWidget(self.bar_battery)

        # Metrics grid
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_volts = self._add_item(grid, 0, 0, "VOLTAGE", "N/A")
        self.val_amps = self._add_item(grid, 0, 1, "CURRENT", "N/A")
        self.val_watts = self._add_item(grid, 1, 0, "POWER", "N/A")
        self.val_status = self._add_item(grid, 1, 1, "STATUS", "UNKNOWN", Theme.STATUS_SUCCESS)

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _apply_battery_bar_style(self, val: float):
        chunk_col = Theme.STATUS_SUCCESS
        if val < 25:
            chunk_col = Theme.STATUS_WARNING
        elif val < 15:
            chunk_col = Theme.STATUS_CRITICAL

        self.bar_battery.setStyleSheet(f"""
            QProgressBar {{
                background-color: {Theme.BG_BASE};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_col};
                border-radius: 3px;
            }}
        """)

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str = Theme.TEXT_PRIMARY) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, p: PowerTelemetry):
        self.val_battery.setText(f"{p.battery_percent:.1f}%")
        self.bar_battery.setValue(int(p.battery_percent))
        self._apply_battery_bar_style(p.battery_percent)

        self.val_volts.setText(f"{p.voltage:.1f} V")
        self.val_amps.setText(f"{p.current:.1f} A")
        self.val_watts.setText(f"{p.power_watts:.0f} W")

        # Warning alerts
        st_color = Theme.STATUS_SUCCESS
        if p.battery_percent < 25.0:
            st_color = Theme.STATUS_WARNING
            p.status = "WARNING"
        self.val_status.setText(p.status)
        self.val_status.setStyleSheet(f"color: {st_color}; font-size: 13px; font-weight: bold; font-family: monospace;")


class CommunicationPanel(BaseTelemetryPanel):
    """
    Displays communication link telemetry: Signal, Latency, Packet Loss, Uplink, Downlink.
    """
    def __init__(self):
        super().__init__("COMMUNICATION LINK")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_link = self._add_item(grid, 0, 0, "LINK STATUS", "DISCONNECTED", Theme.STATUS_WARNING)
        self.val_sig = self._add_item(grid, 0, 1, "SIGNAL", "0%", Theme.TEXT_PRIMARY)
        self.val_lat = self._add_item(grid, 1, 0, "LATENCY", "0 ms", Theme.TEXT_PRIMARY)
        self.val_hb = self._add_item(grid, 1, 1, "HEARTBEAT AGE", "N/A", Theme.STATUS_WARNING)
        self.val_loss = self._add_item(grid, 2, 0, "PACKET LOSS", "0.0%", Theme.STATUS_WARNING)
        self.val_up = self._add_item(grid, 2, 1, "UPLINK", "DISCONNECTED", Theme.TEXT_SECONDARY)
        self.val_down = self._add_item(grid, 3, 0, "DOWNLINK", "DISCONNECTED", Theme.TEXT_SECONDARY)

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str = Theme.TEXT_PRIMARY) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, c: CommunicationTelemetry):
        self.val_link.setText(c.link_status)
        sig_col = Theme.TEXT_PRIMARY if c.signal_percent >= 30 else Theme.STATUS_WARNING
        self.val_sig.setText(f"{int(c.signal_percent)}%")
        self.val_sig.setStyleSheet(f"color: {sig_col}; font-size: 13px; font-weight: bold; font-family: monospace;")

        self.val_lat.setText(f"{int(c.latency_ms)} ms")
        
        hb_col = Theme.STATUS_SUCCESS if c.heartbeat_age < 1.0 else Theme.STATUS_WARNING
        self.val_hb.setText(f"{c.heartbeat_age:.1f} s")
        self.val_hb.setStyleSheet(f"color: {hb_col}; font-size: 13px; font-weight: bold; font-family: monospace;")

        loss_col = Theme.STATUS_SUCCESS if c.packet_loss_percent < 5.0 else Theme.STATUS_WARNING
        self.val_loss.setText(f"{c.packet_loss_percent:.1f}%")
        self.val_loss.setStyleSheet(f"color: {loss_col}; font-size: 13px; font-weight: bold; font-family: monospace;")

        self.val_up.setText(c.uplink)
        self.val_down.setText(c.downlink)


class SensorStatusPanel(BaseTelemetryPanel):
    """
    Displays modular sensor hardware health and state indicators.
    """
    def __init__(self):
        super().__init__("SENSOR SUBSYSTEM STATUS")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.p_imu = self._add_sensor_pill(grid, 0, 0, "IMU", "UNKNOWN", Theme.TEXT_SECONDARY)
        self.p_baro = self._add_sensor_pill(grid, 0, 1, "BAROMETER", "UNKNOWN", Theme.TEXT_SECONDARY)
        self.p_cam = self._add_sensor_pill(grid, 0, 2, "CAMERA", "UNKNOWN", Theme.TEXT_SECONDARY)

        self.p_lidar = self._add_sensor_pill(grid, 1, 0, "LIDAR", "UNKNOWN", Theme.TEXT_SECONDARY)
        self.p_gps = self._add_sensor_pill(grid, 1, 1, "GPS", "UNKNOWN", Theme.TEXT_SECONDARY)
        self.p_slam = self._add_sensor_pill(grid, 1, 2, "SLAM", "UNKNOWN", Theme.TEXT_SECONDARY)

        self.layout.addLayout(grid)

        # Architecture note
        note = QLabel("Note: Confined/GPS-denied architecture utilizes optical/thermal perception & LiDAR SLAM.")
        note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-style: italic;")
        self.layout.addWidget(note)
        self.layout.addStretch()

    def _add_sensor_pill(self, grid: QGridLayout, r: int, c: int, name: str, status: str, color: str) -> QLabel:
        box = QFrame()
        box.setStyleSheet(f"background-color: {Theme.BG_SECONDARY}; border: 1px solid {Theme.BORDER}; border-radius: 4px;")
        l = QHBoxLayout(box)
        l.setContentsMargins(8, 6, 8, 6)
        l.setSpacing(6)

        t = QLabel(name)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        s = QLabel(f"● {status}")
        s.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addStretch()
        l.addWidget(s)
        grid.addWidget(box, r, c)
        return s

    def update_data(self, s: SensorStatus):
        self.p_imu.setText(f"● {s.imu}")
        self.p_baro.setText(f"● {s.barometer}")
        self.p_cam.setText(f"● {s.camera}")
        self.p_lidar.setText(f"● {s.lidar}")
        self.p_gps.setText(f"● {s.gps}")
        self.p_slam.setText(f"● {s.slam}")


class FlightControllerPanel(BaseTelemetryPanel):
    """
    Displays ArduPilot flight controller telemetry and states (DISPLAY ONLY).
    """
    def __init__(self):
        super().__init__("FLIGHT CONTROLLER (DISPLAY ONLY)")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_fc_st = self._add_item(grid, 0, 0, "STATUS", "DISCONNECTED", Theme.STATUS_WARNING)
        self.val_auto = self._add_item(grid, 0, 1, "AUTOPILOT", "N/A")
        self.val_mode = self._add_item(grid, 1, 0, "MODE", "N/A", Theme.ACCENT)
        self.val_armed = self._add_item(grid, 1, 1, "ARMED", "N/A", Theme.TEXT_SECONDARY)
        self.val_link = self._add_item(grid, 2, 0, "MAVLINK", "DISCONNECTED", Theme.STATUS_WARNING)

        self.layout.addLayout(grid)

        # Safety notice
        notice = QLabel("SAFETY: Display-only console. Active flight control commands disabled in Ground Station.")
        notice.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-style: italic;")
        self.layout.addWidget(notice)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str = Theme.TEXT_PRIMARY) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, fc: FlightControllerStatus):
        self.val_fc_st.setText(fc.status)
        self.val_auto.setText(fc.autopilot)
        self.val_mode.setText(fc.mode)
        armed_str = "YES" if fc.armed else "NO"
        armed_col = Theme.STATUS_CRITICAL if fc.armed else Theme.TEXT_SECONDARY
        self.val_armed.setText(armed_str)
        self.val_armed.setStyleSheet(f"color: {armed_col}; font-size: 13px; font-weight: bold; font-family: monospace;")
        self.val_link.setText(fc.link)


class CompanionComputerPanel(BaseTelemetryPanel):
    """
    Displays companion computer (Raspberry Pi 5) resource usage and component states.
    """
    def __init__(self):
        super().__init__("COMPANION COMPUTER")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_dev = self._add_item(grid, 0, 0, "DEVICE", "RASPBERRY PI 5")
        self.val_status = self._add_item(grid, 0, 1, "STATUS", "ONLINE", Theme.STATUS_SUCCESS)
        self.val_cpu = self._add_item(grid, 1, 0, "CPU USAGE", "34%")
        self.val_ram = self._add_item(grid, 1, 1, "RAM USAGE", "42%")
        self.val_temp = self._add_item(grid, 2, 0, "TEMPERATURE", "51°C")
        self.val_ai = self._add_item(grid, 2, 1, "AI MODEL", "READY", Theme.ACCENT)

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str = Theme.TEXT_PRIMARY) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, cc: CompanionComputerStatus):
        self.val_dev.setText(cc.device)
        self.val_status.setText(cc.status)
        self.val_cpu.setText(f"{int(cc.cpu_percent)}%")
        self.val_ram.setText(f"{int(cc.ram_percent)}%")

        temp_col = Theme.TEXT_PRIMARY if cc.temperature_c < 70.0 else Theme.STATUS_WARNING
        self.val_temp.setText(f"{cc.temperature_c:.1f}°C")
        self.val_temp.setStyleSheet(f"color: {temp_col}; font-size: 13px; font-weight: bold; font-family: monospace;")
        self.val_ai.setText(cc.ai_status)

from app.models.telemetry import GPSTelemetry

class GPSTelemetryPanel(BaseTelemetryPanel):
    def __init__(self):
        super().__init__("GPS TELEMETRY (GLOBAL)")
        self._setup_content()

    def _setup_content(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setHorizontalSpacing(16)

        self.val_lat = self._add_item(grid, 0, 0, "LATITUDE", "N/A")
        self.val_lon = self._add_item(grid, 0, 1, "LONGITUDE", "N/A")
        self.val_sats = self._add_item(grid, 1, 0, "SATELLITES", "0", Theme.TEXT_SECONDARY)
        self.val_alt = self._add_item(grid, 1, 1, "ALTITUDE (MSL)", "N/A")

        self.layout.addLayout(grid)
        self.layout.addStretch()

    def _add_item(self, grid: QGridLayout, r: int, c: int, title: str, init_val: str, color: str = Theme.TEXT_PRIMARY) -> QLabel:
        box = QWidget()
        l = QVBoxLayout(box)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(2)

        t = QLabel(title)
        t.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 9px; font-weight: bold; letter-spacing: 0.5px;")
        v = QLabel(init_val)
        v.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; font-family: monospace;")

        l.addWidget(t)
        l.addWidget(v)
        grid.addWidget(box, r, c)
        return v

    def update_data(self, g: GPSTelemetry):
        self.val_lat.setText(f"{g.latitude:.6f}°" if g.latitude is not None else "N/A")
        self.val_lon.setText(f"{g.longitude:.6f}°" if g.longitude is not None else "N/A")
        self.val_sats.setText(str(g.satellites))
        self.val_alt.setText(f"{g.altitude:.1f} m" if g.altitude is not None else "N/A")
