import json
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OnboardEventBuffer:
    """
    Offline local storage buffer for the Raspberry Pi.
    Ensures that when communication is lost, events are retained and
    can be synchronized with the ground station later.
    """
    def __init__(self, db_path: str = "onboard_buffer.db", max_size: int = 10000):
        self.db_path = db_path
        self.max_size = max_size
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._init_db()

    def _get_conn(self):
        if self._shared_conn:
            return self._shared_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    sent BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()

    def enqueue(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Adds an event to the local buffer."""
        try:
            payload_str = json.dumps(payload, default=str)
            with self._get_conn() as conn:
                # Check size limit
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM buffer WHERE sent = 0")
                count = cursor.fetchone()[0]
                
                if count >= self.max_size:
                    # Drop oldest unsent message to make room
                    cursor.execute("DELETE FROM buffer WHERE id = (SELECT MIN(id) FROM buffer WHERE sent = 0)")
                    
                cursor.execute(
                    "INSERT INTO buffer (event_type, payload) VALUES (?, ?)",
                    (event_type, payload_str)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue event {event_type}: {e}")
            return False

    def retrieve_pending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves unsent events from the buffer."""
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, event_type, payload, timestamp FROM buffer WHERE sent = 0 ORDER BY id ASC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append({
                        "id": row["id"],
                        "event_type": row["event_type"],
                        "payload": json.loads(row["payload"]),
                        "timestamp": row["timestamp"]
                    })
                return result
        except Exception as e:
            logger.error(f"Failed to retrieve pending events: {e}")
            return []

    def mark_sent(self, event_ids: List[int]) -> bool:
        """Marks specific events as sent and successfully synced."""
        if not event_ids:
            return True
            
        try:
            with self._get_conn() as conn:
                placeholders = ",".join("?" * len(event_ids))
                conn.execute(
                    f"UPDATE buffer SET sent = 1 WHERE id IN ({placeholders})",
                    event_ids
                )
                # Cleanup sent events to prevent infinite growth
                conn.execute("DELETE FROM buffer WHERE sent = 1")
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark events as sent: {e}")
            return False

    def clear(self):
        """Clears the entire buffer."""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM buffer")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear buffer: {e}")

    def count(self) -> int:
        """Returns the number of pending events."""
        try:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM buffer WHERE sent = 0")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to count buffer: {e}")
            return 0
