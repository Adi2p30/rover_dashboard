"""Maps a DetectorResult's state to an Alert severity."""
from __future__ import annotations

from dataclasses import dataclass

from backend.fault_detection.base import DetectorResult

SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}

_STATE_TO_SEVERITY = {
    "normal": None,
    "warning": "WARNING",
    "fault": "CRITICAL",
}


@dataclass
class Alert:
    point_id: str
    severity: str
    detector_name: str
    message: str
    ts: float


def result_to_alert(result: DetectorResult) -> Alert | None:
    severity = _STATE_TO_SEVERITY.get(result.state)
    if severity is None:
        return None
    return Alert(
        point_id=result.point_id,
        severity=severity,
        detector_name=result.detector_name,
        message=f"{result.point_id}: {result.detector_name} -> {result.state} ({result.detail})",
        ts=result.ts,
    )
