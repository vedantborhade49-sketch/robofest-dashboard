import json
import logging
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtWebSockets import QWebSocket

logger = logging.getLogger(__name__)

class RealtimeClient(QObject):
    connected = Signal()
    disconnected = Signal()
    event_received = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = QUrl(url)
        self.websocket = QWebSocket()
        self.websocket.connected.connect(self._on_connected)
        self.websocket.disconnected.connect(self._on_disconnected)
        self.websocket.textMessageReceived.connect(self._on_message)
        self.websocket.errorOccurred.connect(self._on_error)
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setSingleShot(True)
        self.reconnect_timer.timeout.connect(self.connect_to_server)
        
        self._reconnect_attempts = 0
        self._reconnect_intervals = [1000, 2000, 5000, 10000] # ms
        self._is_connected = False
        self._mock_mode = False

    def set_mock_mode(self, mock_mode: bool):
        self._mock_mode = mock_mode
        if mock_mode:
            self.disconnect_from_server()

    def connect_to_server(self):
        if self._mock_mode:
            return
            
        if not self._is_connected:
            logger.info(f"Connecting to realtime server at {self.url.toString()}")
            self.websocket.open(self.url)

    def disconnect_from_server(self):
        self.reconnect_timer.stop()
        if self.websocket.isValid():
            self.websocket.close()

    def _on_connected(self):
        logger.info("Realtime client connected")
        self._is_connected = True
        self._reconnect_attempts = 0
        self.connected.emit()

    def _on_disconnected(self):
        if not hasattr(self, '_logged_disconnect') or not self._logged_disconnect:
            logger.info("Realtime client disconnected (backend unavailable)")
            self._logged_disconnect = True
        self._is_connected = False
        self.disconnected.emit()
        self._schedule_reconnect()

    def _on_error(self, error):
        error_msg = self.websocket.errorString()
        if not hasattr(self, '_last_error') or self._last_error != error_msg:
            logger.debug(f"Realtime client error: {error_msg}")
            self._last_error = error_msg
        self.error_occurred.emit(error_msg)
        # _on_disconnected is usually called after error, but if not we might need to schedule reconnect here too

    def _on_message(self, message: str):
        try:
            data = json.loads(message)
            self.event_received.emit(data)
        except json.JSONDecodeError:
            logger.error("Failed to parse realtime message")

    def _schedule_reconnect(self):
        if self._mock_mode:
            return
            
        interval = self._reconnect_intervals[min(self._reconnect_attempts, len(self._reconnect_intervals) - 1)]
        logger.info(f"Scheduling reconnect in {interval}ms")
        self.reconnect_timer.start(interval)
        self._reconnect_attempts += 1
