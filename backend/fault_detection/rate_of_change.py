"""Flags sudden jumps in a signal (|delta value| / delta t) that exceed a configured
max rate -- useful for catching sensor glitches or unrealistic step changes."""
from __future__ import annotations

from backend.fault_detection.base import DetectorResult


class RateOfChangeDetector:
    def __init__(self, warn_rate: float, fault_rate: float):
        self.warn_rate = warn_rate
        self.fault_rate = fault_rate
        self._prev_value: float | None = None
        self._prev_ts: float | None = None

    def update(self, point_id: str, value: float, ts: float) -> DetectorResult:
        if self._prev_value is None or self._prev_ts is None:
            self._prev_value, self._prev_ts = value, ts
            return DetectorResult(point_id, "rate_of_change", "normal", value, "warming up", ts)

        dt = max(ts - self._prev_ts, 1e-3)
        rate = abs(value - self._prev_value) / dt
        self._prev_value, self._prev_ts = value, ts

        if rate >= self.fault_rate:
            state = "fault"
        elif rate >= self.warn_rate:
            state = "warning"
        else:
            state = "normal"

        return DetectorResult(point_id, "rate_of_change", state, value, f"rate={rate:.3f}/s", ts)
