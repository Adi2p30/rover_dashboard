---
type: Playbook
title: Run tests
description: Run the pytest suite covering fault detectors, the alert manager, and the generator's signal primitives.
tags: [playbook, testing]
generated: { by: claude-code/claude-sonnet-5, at: 2026-10-13T17:30:43Z }
---

# Steps

```bash
pytest tests/
```

# Coverage

| File | Covers |
|------|--------|
| [`tests/test_detectors.py`](../../tests/test_detectors.py) | [Threshold](../detectors/threshold.md), [rolling z-score](../detectors/rolling-zscore.md), [rate-of-change](../detectors/rate-of-change.md), and [staleness](../detectors/staleness.md) detectors. |
| [`tests/test_alert_manager.py`](../../tests/test_alert_manager.py) | [Alert manager](../alerting/alert-manager.md) severity transitions, dedupe, and safe-state triggering. |
| [`tests/test_signals.py`](../../tests/test_signals.py) | The generator's stochastic primitives in `generator/signals.py`. |

# Related

* [Fault detectors](../detectors/index.md)
* [Alerting](../alerting/index.md)
