from generator import signals


def test_sine_with_noise_bounded_by_amplitude_and_noise():
    values = [signals.sine_with_noise(t, base=10.0, amplitude=2.0, period=5.0, noise_std=0.01) for t in range(50)]
    assert all(7.5 < v < 12.5 for v in values)


def test_random_walk_stays_within_bounds():
    value = 50.0
    for _ in range(1000):
        value = signals.random_walk(value, drift=1.0, noise_std=0.5, lo=0.0, hi=100.0)
        assert 0.0 <= value <= 100.0


def test_ou_process_mean_reverts():
    value = 20.0
    for _ in range(5000):
        value = signals.ou_process(value, mean=0.0, theta=0.5, sigma=0.1, dt=0.05)
    assert abs(value) < 2.0
