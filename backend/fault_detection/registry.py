"""Builds detector instances from backend.config.DETECTOR_CONFIG and runs them
against incoming values (or, for staleness, against elapsed time)."""
from __future__ import annotations

import time

from backend.config import DETECTOR_CONFIG
from backend.fault_detection.base import DetectorResult
from backend.fault_detection.rate_of_change import RateOfChangeDetector
from backend.fault_detection.staleness import StalenessDetector
from backend.fault_detection.threshold import ThresholdDetector
from backend.fault_detection.zscore import ZScoreDetector

_DETECTOR_CLASSES = {
    "threshold": ThresholdDetector,
    "zscore": ZScoreDetector,
    "rate_of_change": RateOfChangeDetector,
    "staleness": StalenessDetector,
}


class DetectorRegistry:
    def __init__(self, config: dict[str, list[dict]] = DETECTOR_CONFIG):
        self._detectors: dict[str, list] = {}
        self._staleness_points: list[str] = []
        for point_id, specs in config.items():
            instances = []
            for spec in specs:
                kwargs = {k: v for k, v in spec.items() if k != "type"}
                detector = _DETECTOR_CLASSES[spec["type"]](**kwargs)
                instances.append(detector)
                if spec["type"] == "staleness":
                    self._staleness_points.append(point_id)
            self._detectors[point_id] = instances

    def points_with_staleness(self) -> list[str]:
        return list(self._staleness_points)

    def evaluate_value(self, point_id: str, value: float, ts: float) -> list[DetectorResult]:
        results = []
        for detector in self._detectors.get(point_id, []):
            if isinstance(detector, StalenessDetector):
                continue
            results.append(detector.update(point_id, value, ts))
        return results

    def evaluate_staleness(self, point_id: str, seconds_since_seen: float | None) -> list[DetectorResult]:
        results = []
        ts = time.time()
        for detector in self._detectors.get(point_id, []):
            if isinstance(detector, StalenessDetector):
                results.append(detector.check(point_id, seconds_since_seen, ts))
        return results
