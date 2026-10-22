"""Rolling EWMA mean/variance z-score detector: flags values that deviate sharply
from the point's recent statistical behaviour, useful for noisy-but-bounded signals
like torque or current draw where a fixed threshold would be too rigid."""
from __future__ import annotations

import math

from backend.fault_detection.base import DetectorResult


class ZScoreDetector:
    def __init__(self, warn_z: float = 3.0, fault_z: float = 5.0, alpha: float = 0.05):
        self.warn_z = warn_z
        self.fault_z = fault_z
        self.alpha = alpha
        self._mean: float | None = None
        self._var: float = 1.0

    def update(self, point_id: str, value: float, ts: float) -> DetectorResult:
        if self._mean is None:
            self._mean = value
            return DetectorResult(point_id, "zscore", "normal", value, "warming up", ts)

        diff = value - self._mean
        std = math.sqrt(max(self._var, 1e-6))
        z = abs(diff) / std if std > 0 else 0.0

        # Update mean/variance after computing z so a single outlier can't inflate
        # its own variance estimate and mask itself.
        self._mean += self.alpha * diff
        self._var = (1 - self.alpha) * (self._var + self.alpha * diff * diff)

        if z >= self.fault_z:
            state = "fault"
        elif z >= self.warn_z:
            state = "warning"
        else:
            state = "normal"

        return DetectorResult(point_id, "zscore", state, value, f"z={z:.2f}", ts)
