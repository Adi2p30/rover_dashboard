"""Reusable stochastic-signal primitives for synthesizing realistic telemetry."""
from __future__ import annotations

import math
import random


def sine_with_noise(t: float, base: float, amplitude: float, period: float, noise_std: float) -> float:
    """Periodic-ish signal, e.g. joint position oscillation or IMU orientation while driving."""
    return base + amplitude * math.sin(2 * math.pi * t / period) + random.gauss(0, noise_std)


def random_walk(prev: float, drift: float, noise_std: float, lo: float, hi: float) -> float:
    """Bounded random walk, e.g. battery voltage/SoC decay, slow temperature drift."""
    value = prev + drift + random.gauss(0, noise_std)
    return min(max(value, lo), hi)


def ou_process(prev: float, mean: float, theta: float, sigma: float, dt: float) -> float:
    """Ornstein-Uhlenbeck mean-reverting process for noisy-but-bounded signals (torque, current)."""
    return prev + theta * (mean - prev) * dt + sigma * math.sqrt(dt) * random.gauss(0, 1)


# Realistic nominal ranges used across the generator.
JOINT_TEMP_NOMINAL = (20.0, 45.0)
JOINT_TORQUE_RANGE = (-5.0, 5.0)
BATTERY_VOLTAGE_RANGE = (22.0, 25.2)  # 6S li-ion pack
WHEEL_SPEED_RANGE = (0.0, 3.0)  # rad/s
