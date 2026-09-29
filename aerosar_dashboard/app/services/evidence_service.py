from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional, Union

from app.models.evidence import Evidence, EvidenceType
from app.models.incident import Incident, IncidentStatus


class EvidenceService:
    """Dedicated evidence handling for incident capture metadata and filesystem storage."""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2] / "data" / "evidence"
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, incident_id: str) -> str:
        return str(incident_id).strip().replace("\\", "/").replace("..", "").strip("/")

    def generate_evidence_id(self, incident_id: str) -> str:
        suffix = str(uuid.uuid4())[:8].upper()
        clean = str(incident_id).replace("INC-", "").replace("-", "")
        return f"EV-{clean}-{suffix}"

    def generate_evidence_path(self, incident_id: str, evidence_type: EvidenceType = EvidenceType.ANNOTATED_FRAME) -> str:
        clean_incident = self._safe_name(incident_id)
        evidence_dir = self.base_dir / "incidents" / clean_incident
        evidence_dir.mkdir(parents=True, exist_ok=True)

        file_name = {
            EvidenceType.FRAME: "frame.jpg",
            EvidenceType.ANNOTATED_FRAME: "annotated_frame.jpg",
            EvidenceType.CROP: "crop.jpg",
        }.get(evidence_type, "annotated_frame.jpg")

        return str((evidence_dir / file_name).resolve())

    def is_invalid_path(self, file_path: Union[str, Path]) -> bool:
        try:
            resolved = Path(file_path).resolve()
            resolved.relative_to(self.base_dir.resolve())
            return False
        except ValueError:
            return True
        except Exception:
            return True

    def save_evidence_image(
        self,
        incident_id: str,
        image_bytes: Optional[bytes] = None,
        frame=None,
        evidence_type: EvidenceType = EvidenceType.ANNOTATED_FRAME,
    ) -> str:
        file_path = Path(self.generate_evidence_path(incident_id, evidence_type))
        if self.is_invalid_path(file_path):
            raise ValueError("Evidence path is outside the controlled evidence directory.")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        if image_bytes is not None:
            file_path.write_bytes(image_bytes)
            return str(file_path)

        try:
            import cv2
            import numpy as np

            if frame is not None:
                cv2.imwrite(str(file_path), frame)
                return str(file_path)

            canvas = np.zeros((160, 240, 3), dtype=np.uint8)
            canvas[:] = (12, 18, 28)
            cv2.putText(canvas, "EVIDENCE", (28, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(canvas, "CAPTURED", (28, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 216), 2)
            cv2.imwrite(str(file_path), canvas)
            return str(file_path)
        except Exception:
            file_path.write_bytes(b"placeholder")
            return str(file_path)

    def create_evidence_metadata(
        self,
        incident: Incident,
        evidence_type: EvidenceType = EvidenceType.ANNOTATED_FRAME,
        file_path: Optional[Union[str, Path]] = None,
        mime_type: str = "image/jpeg",
        frame_id: Optional[int] = None,
        source: str = "camera-01",
        description: Optional[str] = None,
    ) -> Evidence:
        if file_path is None:
            file_path = self.generate_evidence_path(incident.incident_id, evidence_type)
        resolved_path = str(Path(file_path).resolve())
        if self.is_invalid_path(resolved_path):
            raise ValueError("Evidence path is outside the controlled evidence directory.")

        evidence = Evidence(
            evidence_id=self.generate_evidence_id(incident.incident_id),
            incident_id=incident.incident_id,
            timestamp=incident.timestamp,
            type=evidence_type,
            file_path=resolved_path,
            mime_type=mime_type,
            frame_id=frame_id,
            source=source,
            description=description or f"{incident.type} evidence for {incident.incident_id}",
        )
        return evidence

    def create_evidence_record(
        self,
        incident: Incident,
        evidence_type: EvidenceType = EvidenceType.ANNOTATED_FRAME,
        image_bytes: Optional[bytes] = None,
        frame=None,
        mime_type: str = "image/jpeg",
        frame_id: Optional[int] = None,
        source: str = "camera-01",
        description: Optional[str] = None,
    ) -> Evidence:
        file_path = self.save_evidence_image(
            incident_id=incident.incident_id,
            image_bytes=image_bytes,
            frame=frame,
            evidence_type=evidence_type,
        )
        evidence = self.create_evidence_metadata(
            incident=incident,
            evidence_type=evidence_type,
            file_path=file_path,
            mime_type=mime_type,
            frame_id=frame_id,
            source=source,
            description=description,
        )
        return evidence
