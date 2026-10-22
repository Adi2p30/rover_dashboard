from backend.alerting.alert_manager import AlertManager
from backend.fault_detection.base import DetectorResult


def make_result(state: str, point_id: str = "battery/voltage", ts: float = 0.0) -> DetectorResult:
    return DetectorResult(point_id, "threshold", state, 1.0, "detail", ts)


def test_new_alert_is_logged_and_active():
    mgr = AlertManager()
    alerts = mgr.process([make_result("warning")])
    assert len(alerts) == 1
    assert "battery/voltage" in mgr.active_alerts
    assert len(mgr.alert_log) == 1


def test_repeated_same_severity_does_not_duplicate_log():
    mgr = AlertManager()
    mgr.process([make_result("warning", ts=0)])
    mgr.process([make_result("warning", ts=1)])
    assert len(mgr.alert_log) == 1


def test_clearing_removes_active_alert():
    mgr = AlertManager()
    mgr.process([make_result("fault", ts=0)])
    assert "battery/voltage" in mgr.active_alerts
    mgr.process([make_result("normal", ts=1)])
    assert "battery/voltage" not in mgr.active_alerts


def test_safe_state_triggers_on_critical_and_clears():
    events = []
    mgr = AlertManager(on_safe_state_change=lambda active, reasons: events.append((active, list(reasons))))

    mgr.process([make_result("fault", ts=0)])
    assert events[-1][0] is True
    assert "battery/voltage" in events[-1][1]

    mgr.process([make_result("normal", ts=1)])
    assert events[-1][0] is False


def test_safe_state_does_not_flap_between_multiple_criticals():
    events = []
    mgr = AlertManager(on_safe_state_change=lambda active, reasons: events.append(active))

    mgr.process([make_result("fault", point_id="battery/voltage", ts=0)])
    mgr.process([make_result("fault", point_id="joints/2/temperature", ts=1)])
    # Still just one "became active" transition, not two.
    assert events == [True]
