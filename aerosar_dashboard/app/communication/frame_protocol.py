import struct
import time
from dataclasses import dataclass
from typing import Optional

# Distributor header format: [4 bytes frame_id] [8 bytes timestamp] [4 bytes payload_size]
# Using network byte order (big-endian)
HEADER_FORMAT = ">IQI"
HEADER_SIZE = 16

@dataclass
class FramePacket:
    frame_id: int
    timestamp_ms: int
    payload: bytes

    def serialize(self) -> bytes:
        header = struct.pack(
            HEADER_FORMAT,
            self.frame_id,
            self.timestamp_ms,
            len(self.payload)
        )
        return header + self.payload

    @classmethod
    def deserialize_header(cls, header_bytes: bytes) -> Optional[dict]:
        if len(header_bytes) < HEADER_SIZE:
            return None
            
        unpacked = struct.unpack(HEADER_FORMAT, header_bytes)
        frame_id, ts, size = unpacked
            
        return {
            "frame_id": frame_id,
            "timestamp_ms": ts,
            "payload_size": size,
            "encoding": "jpeg"  # Assumed from Distributor
        }
