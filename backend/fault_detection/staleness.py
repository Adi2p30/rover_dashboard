"""Heartbeat/staleness detector. Unlike the other detectors this isn't driven by
new message values -- it's polled periodically against `seconds since last message`,
which is exactly what catches a topic that stops publishing entirely (comms loss,
sensor dropout)."""
from __future__ import annotations

from backend.fault_detection.base import DetectorResult


class StalenessDetector:
    def __init__(self, warn_timeout: float, fault_timeout: float):
        self.warn_timeout = warn_timeout
        self.fault_timeout = fault_timeout

    def check(self, point_id: str, seconds_since_seen: float | None, ts: float) -> DetectorResult:
        if seconds_since_seen is None:
            return DetectorResult(point_id, "staleness", "fault", None, "never seen", ts)

        if seconds_since_seen >= self.fault_timeout:
            state = "fault"
        elif seconds_since_seen >= self.warn_timeout:
            state = "warning"
        else:
            state = "normal"

        return DetectorResult(point_id, "staleness", state, seconds_since_seen, f"age={seconds_since_seen:.1f}s", ts)

    # Not message-driven; present so it satisfies ad-hoc duck typing if ever used generically.
    def update(self, point_id: str, value: float, ts: float) -> DetectorResult:
        return self.check(point_id, value, ts)
