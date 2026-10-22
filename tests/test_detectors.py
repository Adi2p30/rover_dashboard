from backend.fault_detection.rate_of_change import RateOfChangeDetector
from backend.fault_detection.staleness import StalenessDetector
from backend.fault_detection.threshold import ThresholdDetector
from backend.fault_detection.zscore import ZScoreDetector


def test_threshold_detector_transitions_and_hysteresis():
    d = ThresholdDetector(warn_hi=50.0, fault_hi=75.0, hysteresis=3.0)
    assert d.update("p", 40.0, 0).state == "normal"
    assert d.update("p", 60.0, 1).state == "warning"
    assert d.update("p", 80.0, 2).state == "fault"
    # Must clear fault_hi by hysteresis margin before dropping out of fault.
    assert d.update("p", 73.0, 3).state == "fault"
    assert d.update("p", 60.0, 4).state == "warning"
    assert d.update("p", 40.0, 5).state == "normal"


def test_zscore_detector_flags_outliers():
    d = ZScoreDetector(warn_z=3.0, fault_z=5.0, alpha=0.1)
    for i in range(50):
        d.update("p", 1.0, i)
    result = d.update("p", 50.0, 51)
    assert result.state == "fault"


def test_rate_of_change_detector_flags_jump():
    d = RateOfChangeDetector(warn_rate=2.0, fault_rate=4.0)
    d.update("p", 0.0, 0.0)
    result = d.update("p", 5.0, 1.0)  # rate = 5/s
    assert result.state == "fault"


def test_staleness_detector_warns_and_faults():
    d = StalenessDetector(warn_timeout=3.0, fault_timeout=8.0)
    assert d.check("p", 1.0, 0).state == "normal"
    assert d.check("p", 4.0, 0).state == "warning"
    assert d.check("p", 9.0, 0).state == "fault"
    assert d.check("p", None, 0).state == "fault"
