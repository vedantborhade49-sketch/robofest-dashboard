# UI Responsiveness Guidelines

This document outlines the architecture, principles, and testing procedures for the responsiveness of the STALLION AEROSAR Ground Station Dashboard.

## Architecture

The dashboard is designed to be responsive across different screen sizes (from 1024x768 to 1920x1080) using a breakpoint-based approach. 

### Breakpoints (`ScreenSize` enum)
- `MINIMUM`: Below 1100px. The UI collapses to essential components. Grid layouts become 1-column. Headers and labels may be hidden to save space.
- `COMPACT`: 1100px - 1400px. Splitters may orient vertically or favor tighter packing of side-by-side elements. 
- `STANDARD`: 1400px - 1600px. The standard layout with horizontal panels where possible.
- `WIDE`: Above 1600px. Optimized for large displays, leveraging maximum grid columns and wide layout views.

### Implementation Details
- `MainWindow` listens to `resizeEvent` and computes the current `ScreenSize` state based on its `width()`.
- State changes are broadcasted to all active views via the `set_responsive_state(state: ScreenSize)` method.
- Views reconfigure their layouts dynamically using:
  - `QSplitter.setOrientation()` (switching between horizontal/vertical)
  - `QGridLayout.removeWidget()` and `QGridLayout.addWidget()` (reflowing grid columns)
  - `QWidget.hide()` / `QWidget.show()` (hiding non-essential elements like subtitles on MINIMUM sizes)

## Views Implemented

1. **OverviewView**: Reflows standard cards using a 1, 2, or 3-column grid depending on screen width.
2. **LiveFeedView**: Splitters toggle vertically in compact modes to ensure both the map and the feed are visible.
3. **IncidentsView**: The main horizontal layout converts to a vertical splitter on compact screens to maintain readability.
4. **MapView**: Left and right panels dynamically stack or adjust proportions to maximize the map canvas.
5. **TelemetryView**: Switches from a 3-column dense read-out to a 1-column vertically scrollable layout.
6. **ReportsView**: The report list and details panel switch from horizontal side-by-side to vertical top-and-bottom. Counters bar subtitles are hidden on minimum widths.
7. **EventLogView**: Hides some filter buttons/separators on minimum width and adjusts margins.
8. **SettingsView**: Reflows settings category cards from 2 columns to 1 column.

## Manual Testing Protocol

To validate responsiveness, developers and QA must perform the following manual test cases across target resolutions (1024x768, 1280x720, 1920x1080) and varying DPI scales (100%, 125%, 150%).

1. **Startup Validation**: Launch the dashboard on a 1920x1080 display. Observe that all views operate in `WIDE` or `STANDARD` modes.
2. **Dynamic Resize**:
   - Slowly resize the window down horizontally.
   - Verify that at ~1400px, the UI gracefully enters `COMPACT` mode. (e.g. TelemetryView 3-col -> 2-col).
   - Continue resizing down to ~1024px. Verify that the UI enters `MINIMUM` mode (e.g., SettingsView drops to 1-col, headers condense).
3. **Splitter State Verification**: 
   - Check `ReportsView` and `IncidentsView`. The List-Detail panels should be horizontally adjacent in `STANDARD` but stack vertically in `COMPACT`/`MINIMUM`.
4. **Scroll Area Safety**: 
   - Shrink the window vertically. Ensure that `QScrollArea`s (in Settings, Telemetry, and Overview) display scrollbars correctly and do not clip vital information.
5. **DPI Scaling (Windows)**:
   - Close the app. Go to Windows Display Settings and change scaling to 125% and 150%.
   - Relaunch the app. Ensure font sizes scale correctly and elements do not overlap.

## Known Limitations
- When resizing very rapidly, the `resizeEvent` throttle (via `QTimer` in `MainWindow`) may cause a slight layout delay (50-150ms). This is expected and prevents rapid re-layouts from blocking the main thread.
- `SettingsView` cards might jump slightly when switching from 2-col to 1-col due to `QGridLayout` widget removal and re-addition.
