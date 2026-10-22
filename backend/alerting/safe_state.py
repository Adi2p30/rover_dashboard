"""Publishes rover/command/safe_state (retained) whenever the AlertManager's
critical-alert count transitions to/from zero."""
from __future__ import annotations

import json
import time
from typing import Callable

from backend.config import SAFE_STATE_TOPIC


class SafeStatePublisher:
    def __init__(self, publish_fn: Callable[[str, str, bool], None]):
        """publish_fn(topic, json_payload, retain) -- typically mqtt_bridge's publish."""
        self._publish_fn = publish_fn

    def on_change(self, active: bool, reasons: list[str]) -> None:
        payload = json.dumps({"active": active, "reasons": reasons, "ts": time.time()})
        self._publish_fn(SAFE_STATE_TOPIC, payload, True)
