"""Tracks active alerts per point and an append-only history log; triggers the
safe-state publisher whenever the count of active CRITICAL alerts changes."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict
from typing import Callable

from backend.alerting.rules import Alert, result_to_alert
from backend.fault_detection.base import DetectorResult

ALERT_LOG_MAXLEN = 200


class AlertManager:
    def __init__(self, on_safe_state_change: Callable[[bool, list[str]], None] | None = None):
        self.active_alerts: dict[str, Alert] = {}
        self.alert_log: deque[Alert] = deque(maxlen=ALERT_LOG_MAXLEN)
        self._on_safe_state_change = on_safe_state_change
        self._safe_state_active = False

    def process(self, results: list[DetectorResult]) -> list[Alert]:
        """Feed a batch of detector results through the rules; returns newly
        emitted alerts (for broadcasting) and updates active/critical bookkeeping."""
        new_alerts: list[Alert] = []

        for result in results:
            alert = result_to_alert(result)
            existing = self.active_alerts.get(result.point_id)

            if alert is None:
                if existing is not None:
                    del self.active_alerts[result.point_id]
                continue

            if existing is None or existing.severity != alert.severity:
                self.active_alerts[result.point_id] = alert
                self.alert_log.append(alert)
                new_alerts.append(alert)
            else:
                # Same severity as before: refresh detail without re-logging (dedupe).
                self.active_alerts[result.point_id] = alert

        self._update_safe_state()
        return new_alerts

    def _update_safe_state(self) -> None:
        critical_points = [p for p, a in self.active_alerts.items() if a.severity == "CRITICAL"]
        should_be_active = len(critical_points) > 0

        if should_be_active != self._safe_state_active:
            self._safe_state_active = should_be_active
            if self._on_safe_state_change:
                self._on_safe_state_change(should_be_active, critical_points)

    def snapshot(self) -> dict:
        return {
            "active_alerts": [asdict(a) for a in self.active_alerts.values()],
            "log": [asdict(a) for a in self.alert_log],
            "safe_state_active": self._safe_state_active,
        }
