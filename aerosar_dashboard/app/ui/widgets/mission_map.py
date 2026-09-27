import math
from typing import List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath, QMouseEvent
)
from app.ui.theme import Theme
from app.models.incident import Incident, Location
from app.models.map import MapState, SearchBoundary

class MissionMap(QWidget):
    """
    Tactical 2D Local Robotics Map widget.
    Renders purely offline in a local SLAM coordinate system (meters).
    
    Features:
    - Meter-based coordinate grid (0-30m X, 0-25m Y) with isotropic scaling
    - Search area boundary and explored area representation
    - Drone position marker with orientation heading arrow and sensor FOV cone
    - Past flight trajectory with glowing path
    - Incident markers dynamically placed from Incident.location
    - Interactive incident marker selection with visual highlight
    - Compass/North indicator and tactical metric scale bar
    """
    incident_selected = Signal(str)  # Emits incident_id

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(450, 350)
        self.setMouseTracking(True)

        self._map_state: Optional[MapState] = None
        self._incidents: List[Incident] = []
        self._selected_incident_id: Optional[str] = None

        # Cached transform metrics
        self._offset_x = 50.0
        self._offset_y = 40.0
        self._scale = 15.0
        self._min_x = 0.0
        self._max_x = 30.0
        self._min_y = 0.0
        self._max_y = 25.0

    def update_map(self, map_state: MapState, incidents: List[Incident]):
        """Updates map telemetry and incidents, triggering repaint."""
        self._map_state = map_state
        self._incidents = incidents
        if map_state and map_state.search_boundary:
            self._min_x = map_state.search_boundary.min_x
            self._max_x = map_state.search_boundary.max_x
            self._min_y = map_state.search_boundary.min_y
            self._max_y = map_state.search_boundary.max_y
        self.update()

    def select_incident(self, incident_id: Optional[str]):
        """Selects and highlights an incident marker on the map."""
        if self._selected_incident_id != incident_id:
            self._selected_incident_id = incident_id
            self.update()

    def get_selected_incident_id(self) -> Optional[str]:
        return self._selected_incident_id

    # -------------------------------------------------------------
    # Coordinate Transforms (Local Meters <-> Screen Pixels)
    # -------------------------------------------------------------
    def _compute_transform(self, width: float, height: float):
        margin_left = 55.0
        margin_right = 35.0
        margin_top = 40.0
        margin_bottom = 40.0

        plot_w = max(50.0, width - margin_left - margin_right)
        plot_h = max(50.0, height - margin_top - margin_bottom)

        span_x = max(1.0, self._max_x - self._min_x)
        span_y = max(1.0, self._max_y - self._min_y)

        # Preserve 1:1 metric aspect ratio (1 meter X == 1 meter Y)
        scale_x = plot_w / span_x
        scale_y = plot_h / span_y
        self._scale = min(scale_x, scale_y)

        actual_w = span_x * self._scale
        actual_h = span_y * self._scale

        # Center in the available canvas
        self._offset_x = margin_left + (plot_w - actual_w) / 2.0
        self._offset_y = margin_top + (plot_h - actual_h) / 2.0

    def _to_screen(self, x: float, y: float) -> QPointF:
        """Converts local SLAM coordinates (meters) to screen pixels. (+Y is North/Up)."""
        px = self._offset_x + (x - self._min_x) * self._scale
        py = self._offset_y + (self._max_y - y) * self._scale
        return QPointF(px, py)

    def _to_world(self, px: float, py: float) -> Tuple[float, float]:
        """Converts screen pixels to local SLAM coordinates (meters)."""
        if self._scale <= 0:
            return 0.0, 0.0
        x = self._min_x + (px - self._offset_x) / self._scale
        y = self._max_y - (py - self._offset_y) / self._scale
        return x, y

    # -------------------------------------------------------------
    # Mouse Interaction (Hit Testing)
    # -------------------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            click_pt = event.position()
            clicked_id = None
            min_dist = 22.0  # Click tolerance in pixels

            for inc in self._incidents:
                sp = self._to_screen(inc.location.x, inc.location.y)
                dist = math.hypot(click_pt.x() - sp.x(), click_pt.y() - sp.y())
                if dist < min_dist:
                    min_dist = dist
                    clicked_id = inc.incident_id

            if clicked_id:
                self._selected_incident_id = clicked_id
                self.incident_selected.emit(clicked_id)
                self.update()
            else:
                # Clicked empty space
                if self._selected_incident_id is not None:
                    self._selected_incident_id = None
                    self.incident_selected.emit("")
                    self.update()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        hovering = False
        for inc in self._incidents:
            sp = self._to_screen(inc.location.x, inc.location.y)
            if math.hypot(pos.x() - sp.x(), pos.y() - sp.y()) < 20.0:
                hovering = True
                break

        if hovering:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.CrossCursor)
        super().mouseMoveEvent(event)

    # -------------------------------------------------------------
    # Painting
    # -------------------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        self._compute_transform(w, h)

        # 1. Canvas background
        painter.fillRect(0, 0, int(w), int(h), QColor("#090D14"))

        # 2. Search boundary area box
        tl = self._to_screen(self._min_x, self._max_y)
        br = self._to_screen(self._max_x, self._min_y)
        area_rect = QRectF(tl.x(), tl.y(), br.x() - tl.x(), br.y() - tl.y())

        # Area background tint
        painter.fillRect(area_rect, QColor("#0C1118"))

        # 3. Explored Area Polygon
        self._draw_explored_area(painter)

        # 4. Metric Grid lines & labels
        self._draw_grid(painter, area_rect)

        # 5. Search Area Outer Boundary & Corners
        self._draw_boundary_frame(painter, area_rect)

        # 6. Flight Trajectory
        self._draw_trajectory(painter)

        # 7. Incident Markers
        self._draw_incidents(painter)

        # 8. Drone Marker & Sensor FOV Cone
        self._draw_drone(painter)

        # 9. Tactical Overlays (North Arrow, Scale Bar, Frame Badge)
        self._draw_overlays(painter, w, h)

    def _draw_grid(self, painter: QPainter, area: QRectF):
        """Draws subtle grid lines and metric labels every 5 meters."""
        grid_pen = QPen(QColor(32, 44, 60, 90), 1, Qt.PenStyle.DotLine)
        axis_pen = QPen(QColor(Theme.BORDER), 1)
        font = QFont("Consolas, Courier New, monospace", 8)
        painter.setFont(font)

        # Vertical grid lines (X meters: 0, 5, 10, 15, 20, 25, 30)
        x_step = 5.0
        x_val = self._min_x
        while x_val <= self._max_x + 0.001:
            p_top = self._to_screen(x_val, self._max_y)
            p_bot = self._to_screen(x_val, self._min_y)

            painter.setPen(grid_pen)
            painter.drawLine(p_top, p_bot)

            # X-axis label below
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            lbl_text = f"{int(x_val)}m" if x_val > 0 else "0m"
            painter.drawText(
                QRectF(p_bot.x() - 25, p_bot.y() + 6, 50, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                lbl_text
            )
            x_val += x_step

        # Horizontal grid lines (Y meters: 0, 5, 10, 15, 20, 25)
        y_step = 5.0
        y_val = self._min_y
        while y_val <= self._max_y + 0.001:
            p_left = self._to_screen(self._min_x, y_val)
            p_right = self._to_screen(self._max_x, y_val)

            painter.setPen(grid_pen)
            painter.drawLine(p_left, p_right)

            # Y-axis label to the left
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            lbl_text = f"{int(y_val)}m" if y_val > 0 else "0m"
            painter.drawText(
                QRectF(p_left.x() - 44, p_left.y() - 8, 38, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                lbl_text
            )
            y_val += y_step

        # Axis title labels
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        painter.drawText(
            QRectF(area.right() - 80, area.bottom() + 18, 80, 16),
            Qt.AlignmentFlag.AlignRight,
            "LOCAL X (m) →"
        )
        painter.drawText(
            QRectF(self._offset_x - 48, area.top() - 24, 70, 16),
            Qt.AlignmentFlag.AlignLeft,
            "↑ Y (m)"
        )

    def _draw_boundary_frame(self, painter: QPainter, area: QRectF):
        """Draws the tactical search boundary rectangle with corner brackets."""
        bound_pen = QPen(QColor(45, 62, 85, 180), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(bound_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(area)

        # Tactical corner brackets
        corner_pen = QPen(QColor(Theme.ACCENT), 2)
        painter.setPen(corner_pen)
        c_len = 12.0
        # TL
        painter.drawLine(QPointF(area.left(), area.top()), QPointF(area.left() + c_len, area.top()))
        painter.drawLine(QPointF(area.left(), area.top()), QPointF(area.left(), area.top() + c_len))
        # TR
        painter.drawLine(QPointF(area.right(), area.top()), QPointF(area.right() - c_len, area.top()))
        painter.drawLine(QPointF(area.right(), area.top()), QPointF(area.right(), area.top() + c_len))
        # BL
        painter.drawLine(QPointF(area.left(), area.bottom()), QPointF(area.left() + c_len, area.bottom()))
        painter.drawLine(QPointF(area.left(), area.bottom()), QPointF(area.left(), area.bottom() - c_len))
        # BR
        painter.drawLine(QPointF(area.right(), area.bottom()), QPointF(area.right() - c_len, area.bottom()))
        painter.drawLine(QPointF(area.right(), area.bottom()), QPointF(area.right(), area.bottom() - c_len))

        # Boundary tag
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(Theme.TEXT_SECONDARY))
        tag_str = f"SEARCH BOUNDARY: {int(self._max_x)}m × {int(self._max_y)}m"
        painter.drawText(
            QRectF(area.left() + 10, area.top() + 8, 220, 16),
            Qt.AlignmentFlag.AlignLeft,
            tag_str
        )

    def _draw_explored_area(self, painter: QPainter):
        """Draws the semi-transparent polygon representing the explored area."""
        if not self._map_state or not self._map_state.explored_polygon:
            return

        poly = QPolygonF()
        for loc in self._map_state.explored_polygon:
            poly.append(self._to_screen(loc.x, loc.y))

        # Explored area fill: subtle cyan tint with dotted border
        fill_col = QColor(0, 180, 216, 22)
        border_pen = QPen(QColor(0, 180, 216, 70), 1, Qt.PenStyle.DashDotLine)

        painter.setPen(border_pen)
        painter.setBrush(QBrush(fill_col))
        painter.drawPolygon(poly)

        # Region tag inside polygon
        label_pt = self._to_screen(8.0, 14.0)
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(0, 180, 216, 140))
        painter.drawText(
            QRectF(label_pt.x() - 60, label_pt.y() - 10, 140, 20),
            Qt.AlignmentFlag.AlignCenter,
            "░ EXPLORED REGION (42%)"
        )

    def _draw_trajectory(self, painter: QPainter):
        """Draws the drone's past flight trajectory with glowing path."""
        if not self._map_state or len(self._map_state.trajectory) < 2:
            return

        path = QPainterPath()
        p0 = self._to_screen(self._map_state.trajectory[0].x, self._map_state.trajectory[0].y)
        path.moveTo(p0)

        for loc in self._map_state.trajectory[1:]:
            pt = self._to_screen(loc.x, loc.y)
            path.lineTo(pt)

        # Outer glow
        glow_pen = QPen(QColor(0, 180, 216, 50), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Core trajectory line
        core_pen = QPen(QColor(0, 180, 216, 190), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(core_pen)
        painter.drawPath(path)

        # Small breadcrumb dots along past waypoints
        dot_pen = QPen(QColor(0, 180, 216, 220), 1)
        dot_brush = QBrush(QColor(0, 180, 216, 180))
        painter.setPen(dot_pen)
        painter.setBrush(dot_brush)
        for loc in self._map_state.trajectory[:-1]:
            pt = self._to_screen(loc.x, loc.y)
            painter.drawEllipse(pt, 2.0, 2.0)

    def _draw_incidents(self, painter: QPainter):
        """Draws all detected incidents from Incident.location."""
        for inc in self._incidents:
            sp = self._to_screen(inc.location.x, inc.location.y)
            is_selected = (inc.incident_id == self._selected_incident_id)

            # Color by status
            st = inc.status.upper()
            if st == "CONFIRMED":
                col = QColor(Theme.STATUS_SUCCESS)
            elif st == "REVIEW":
                col = QColor(Theme.STATUS_WARNING)
            elif st == "NEW":
                col = QColor(Theme.ACCENT)
            else:
                col = QColor(Theme.TEXT_SECONDARY)

            # 1. Selected highlight rings & corner brackets
            if is_selected:
                # Outer pulse ring
                sel_ring_pen = QPen(col, 1.5, Qt.PenStyle.DashLine)
                painter.setPen(sel_ring_pen)
                painter.setBrush(QColor(col.red(), col.green(), col.blue(), 25))
                painter.drawEllipse(sp, 18.0, 18.0)

                # Corner targeting brackets
                b_pen = QPen(col, 2)
                painter.setPen(b_pen)
                b_size = 14.0
                b_len = 5.0
                bx = sp.x() - b_size
                by = sp.y() - b_size
                bw = b_size * 2
                bh = b_size * 2
                # TL
                painter.drawLine(QPointF(bx, by), QPointF(bx + b_len, by))
                painter.drawLine(QPointF(bx, by), QPointF(bx, by + b_len))
                # TR
                painter.drawLine(QPointF(bx + bw, by), QPointF(bx + bw - b_len, by))
                painter.drawLine(QPointF(bx + bw, by), QPointF(bx + bw, by + b_len))
                # BL
                painter.drawLine(QPointF(bx, by + bh), QPointF(bx + b_len, by + bh))
                painter.drawLine(QPointF(bx, by + bh), QPointF(bx, by + bh - b_len))
                # BR
                painter.drawLine(QPointF(bx + bw, by + bh), QPointF(bx + bw - b_len, by + bh))
                painter.drawLine(QPointF(bx + bw, by + bh), QPointF(bx + bw, by + bh - b_len))

            # 2. Main target ring
            ring_pen = QPen(col, 1.5)
            painter.setPen(ring_pen)
            painter.setBrush(QBrush(QColor(15, 22, 32, 210)))
            painter.drawEllipse(sp, 8.0, 8.0)

            # Crosshair ticks
            tick_len = 4.0
            painter.drawLine(QPointF(sp.x() - 11, sp.y()), QPointF(sp.x() - 7, sp.y()))
            painter.drawLine(QPointF(sp.x() + 7, sp.y()), QPointF(sp.x() + 11, sp.y()))
            painter.drawLine(QPointF(sp.x(), sp.y() - 11), QPointF(sp.x(), sp.y() - 7))
            painter.drawLine(QPointF(sp.x(), sp.y() + 7), QPointF(sp.x(), sp.y() + 11))

            # Center pip
            painter.setBrush(QBrush(col))
            painter.drawEllipse(sp, 3.0, 3.0)

            # 3. Label tag
            font = QFont("Segoe UI", 8, QFont.Weight.Bold if is_selected else QFont.Weight.Normal)
            painter.setFont(font)

            tag_text = f"{inc.incident_id} [{int(inc.confidence * 100)}%]"
            # Small background box for readability
            text_x = sp.x() + 12
            text_y = sp.y() - 16
            painter.fillRect(QRectF(text_x - 2, text_y - 2, 86, 16), QColor(10, 15, 22, 220))
            painter.setPen(QPen(col if is_selected else QColor(Theme.BORDER), 1))
            painter.drawRect(QRectF(text_x - 2, text_y - 2, 86, 16))

            painter.setPen(col)
            painter.drawText(QRectF(text_x + 2, text_y - 1, 80, 14), Qt.AlignmentFlag.AlignVCenter, tag_text)

    def _draw_drone(self, painter: QPainter):
        """Draws current drone position, orientation heading arrow, and sensor FOV cone."""
        if not self._map_state:
            return

        dp = self._map_state.drone_position
        sp = self._to_screen(dp.x, dp.y)
        heading_deg = self._map_state.drone_heading

        # In map coords (+Y is North = 0°):
        # Angle in math radians from North clockwise:
        # math angle 0 is +X (East = 90° heading).
        # Math angle = (90 - heading_deg)
        math_angle_rad = math.radians(90.0 - heading_deg)

        # 1. Sensor Field of View (FOV) cone (projecting forward ~3.5 meters)
        fov_len_m = 3.5
        fov_span_deg = 55.0
        fov_radius_px = fov_len_m * self._scale

        cone_path = QPainterPath()
        cone_path.moveTo(sp)
        half_span = math.radians(fov_span_deg / 2.0)
        start_rad = math_angle_rad - half_span
        end_rad = math_angle_rad + half_span

        p_left = QPointF(sp.x() + fov_radius_px * math.cos(start_rad), sp.y() - fov_radius_px * math.sin(start_rad))
        p_right = QPointF(sp.x() + fov_radius_px * math.cos(end_rad), sp.y() - fov_radius_px * math.sin(end_rad))

        cone_path.lineTo(p_left)
        # Approximate arc
        cone_path.lineTo(p_right)
        cone_path.closeSubpath()

        painter.setPen(QPen(QColor(0, 180, 216, 80), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(0, 180, 216, 25)))
        painter.drawPath(cone_path)

        # 2. Drone Marker (Rotated diamond/quadcopter icon)
        painter.save()
        painter.translate(sp.x(), sp.y())
        # Rotate canvas to match drone heading (0° is up)
        painter.rotate(heading_deg)

        # Drone diamond body
        body_col = QColor(Theme.ACCENT)
        d_size = 9.0

        # Rotor arm cross lines
        arm_pen = QPen(QColor(Theme.TEXT_SECONDARY), 1.5)
        painter.setPen(arm_pen)
        painter.drawLine(QPointF(-d_size, -d_size), QPointF(d_size, d_size))
        painter.drawLine(QPointF(-d_size, d_size), QPointF(d_size, -d_size))

        # Rotor motor pips
        painter.setBrush(QBrush(QColor(Theme.BG_BASE)))
        for rx, ry in [(-d_size, -d_size), (d_size, -d_size), (-d_size, d_size), (d_size, d_size)]:
            painter.drawEllipse(QPointF(rx, ry), 2.5, 2.5)

        # Center fuselage diamond
        diamond = QPolygonF([
            QPointF(0, -d_size - 3),    # Front tip
            QPointF(d_size - 1, 0),     # Right
            QPointF(0, d_size - 2),     # Rear
            QPointF(-d_size + 1, 0)     # Left
        ])
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.setBrush(QBrush(body_col))
        painter.drawPolygon(diamond)

        # Forward heading indicator arrow (pointing Up in rotated frame)
        arr_pen = QPen(QColor("#FFFFFF"), 2)
        painter.setPen(arr_pen)
        painter.drawLine(QPointF(0, -d_size - 2), QPointF(0, -d_size - 10))
        painter.drawLine(QPointF(0, -d_size - 10), QPointF(-3, -d_size - 7))
        painter.drawLine(QPointF(0, -d_size - 10), QPointF(3, -d_size - 7))

        painter.restore()

        # 3. Drone Telemetry Label next to marker
        painter.setFont(QFont("Consolas, Courier New, monospace", 8, QFont.Weight.Bold))
        info_str = f"AEROSAR-01 [{dp.x:.1f}, {dp.y:.1f}] {int(heading_deg)}°"
        lbl_w = 175
        lbl_x = sp.x() + 14
        lbl_y = sp.y() + 6

        # Clamp inside boundaries
        if lbl_x + lbl_w > self.width() - 10:
            lbl_x = sp.x() - lbl_w - 14

        painter.fillRect(QRectF(lbl_x, lbl_y, lbl_w, 16), QColor(11, 16, 24, 230))
        painter.setPen(QPen(QColor(Theme.ACCENT), 1))
        painter.drawRect(QRectF(lbl_x, lbl_y, lbl_w, 16))

        painter.drawText(QRectF(lbl_x + 4, lbl_y + 1, lbl_w - 8, 14), Qt.AlignmentFlag.AlignVCenter, info_str)

    def _draw_overlays(self, painter: QPainter, w: float, h: float):
        """Draws tactical compass rose, coordinate frame badge, and metric scale bar."""
        # 1. Compass Rose (Top-Right)
        cx = w - 45.0
        cy = 40.0
        r = 18.0

        # Outer dial
        dial_pen = QPen(QColor(Theme.BORDER), 1.5)
        painter.setPen(dial_pen)
        painter.setBrush(QBrush(QColor(15, 22, 32, 200)))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # North needle
        needle_pen = QPen(QColor(Theme.STATUS_CRITICAL), 2)
        painter.setPen(needle_pen)
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - r + 3))

        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.setPen(QColor(Theme.STATUS_CRITICAL))
        painter.drawText(QRectF(cx - 10, cy - r - 14, 20, 14), Qt.AlignmentFlag.AlignCenter, "N")

        # 2. Local Frame Badge (Top-Left)
        badge_rect = QRectF(14, 12, 185, 22)
        painter.fillRect(badge_rect, QColor(15, 22, 32, 220))
        painter.setPen(QPen(QColor(Theme.BORDER), 1))
        painter.drawRect(badge_rect)

        painter.setFont(QFont("Consolas, Courier New, monospace", 8, QFont.Weight.Bold))
        painter.setPen(QColor(Theme.ACCENT))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "FRAME: LOCAL / SLAM (METERS)")

        # 3. Metric Scale Bar (Bottom-Right)
        scale_meters = 5.0
        scale_px = scale_meters * self._scale
        sb_x = w - 35.0 - scale_px
        sb_y = h - 22.0

        if sb_x > self._offset_x:
            s_pen = QPen(QColor(Theme.TEXT_SECONDARY), 1.5)
            painter.setPen(s_pen)
            # Main horizontal bar
            painter.drawLine(QPointF(sb_x, sb_y), QPointF(sb_x + scale_px, sb_y))
            # Left and right vertical end caps
            painter.drawLine(QPointF(sb_x, sb_y - 4), QPointF(sb_x, sb_y + 4))
            painter.drawLine(QPointF(sb_x + scale_px, sb_y - 4), QPointF(sb_x + scale_px, sb_y + 4))

            # Scale label
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            painter.drawText(
                QRectF(sb_x, sb_y - 18, scale_px, 14),
                Qt.AlignmentFlag.AlignCenter,
                f"{int(scale_meters)} METERS"
            )
