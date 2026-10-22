"""In-memory latest-value store + bounded history per telemetry point."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from backend.config import HISTORY_MAXLEN


def topic_to_point_id(topic: str) -> str:
    """rover/joints/0/temperature -> joints/0/temperature"""
    return topic[len("rover/"):] if topic.startswith("rover/") else topic


@dataclass
class StateStore:
    latest: dict[str, dict] = field(default_factory=dict)
    last_seen: dict[str, float] = field(default_factory=dict)
    history: dict[str, deque] = field(default_factory=dict)

    def update(self, topic: str, payload: dict) -> str:
        point_id = topic_to_point_id(topic)
        self.latest[point_id] = payload
        self.last_seen[point_id] = time.time()

        scalar = self._as_scalar(payload.get("value"))
        if scalar is not None:
            hist = self.history.setdefault(point_id, deque(maxlen=HISTORY_MAXLEN))
            hist.append((payload.get("ts", time.time()), scalar))

        return point_id

    def seconds_since_seen(self, point_id: str) -> float | None:
        last = self.last_seen.get(point_id)
        if last is None:
            return None
        return time.time() - last

    def snapshot(self) -> dict[str, dict]:
        return dict(self.latest)

    @staticmethod
    def _as_scalar(value) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return None
