"""Threshold detector with hysteresis: once a severity is raised, the value must
clear the threshold by `hysteresis` before severity drops, avoiding chatter at the
boundary."""
from __future__ import annotations

from backend.fault_detection.base import DetectorResult


class ThresholdDetector:
    def __init__(
        self,
        warn_lo: float | None = None,
        warn_hi: float | None = None,
        fault_lo: float | None = None,
        fault_hi: float | None = None,
        hysteresis: float = 0.0,
    ):
        self.warn_lo = warn_lo
        self.warn_hi = warn_hi
        self.fault_lo = fault_lo
        self.fault_hi = fault_hi
        self.hysteresis = hysteresis
        self._state = "normal"

    def update(self, point_id: str, value: float, ts: float) -> DetectorResult:
        h = self.hysteresis
        state = self._state

        def below(threshold, margin=0.0):
            return threshold is not None and value < threshold + margin

        def above(threshold, margin=0.0):
            return threshold is not None and value > threshold - margin

        if state == "fault":
            still_fault = below(self.fault_lo, h) or above(self.fault_hi, h)
        else:
            still_fault = below(self.fault_lo) or above(self.fault_hi)

        if still_fault:
            state = "fault"
        else:
            if state in ("fault", "warning"):
                still_warn = below(self.warn_lo, h) or above(self.warn_hi, h)
            else:
                still_warn = below(self.warn_lo) or above(self.warn_hi)
            state = "warning" if still_warn else "normal"

        self._state = state
        detail = f"value={value:.3f}"
        return DetectorResult(point_id, "threshold", state, value, detail, ts)
