"""Shared Detector interface. Any class implementing `update` can be registered
against a telemetry point in registry.py -- swapping in an ML-based detector later
(e.g. IsolationForest) means adding a class here, no pipeline changes elsewhere."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

State = Literal["normal", "warning", "fault"]


@dataclass
class DetectorResult:
    point_id: str
    detector_name: str
    state: State
    value: float | None
    detail: str
    ts: float


class Detector(Protocol):
    def update(self, point_id: str, value: float, ts: float) -> DetectorResult: ...
