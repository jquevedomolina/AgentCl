import numpy as np
import math
from datetime import datetime, timedelta


class WaterDataGenerator:
    """Generates realistic, trending water quality data for simulation."""

    def __init__(self, seed: int = None):
        self.rng = np.random.default_rng(seed)
        self.tick = 0

        # Base values
        self.base_turbidity = 15.0
        self.base_ph = 7.2
        self.base_conductivity = 500.0
        self.base_temperature = 22.0
        self.base_flow_rate = 10.0

        # Random walk state
        self.turbidity_rw = 0.0
        self.ph_rw = 0.0
        self.conductivity_rw = 0.0
        self.flow_rate_rw = 0.0

        # Fixed parameters
        self.pipeline_length = 800.0
        self.pipe_diameter = 50.0
        self.target_residual = 2.0

        # Current residual (simulated — decays over time, boosted by dosing)
        self.current_residual = 1.2

        # Last applied dose for residual simulation
        self.last_applied_dose_mgl = 0.0

    def _random_walk(self, current: float, step_std: float, bounds: tuple) -> float:
        step = self.rng.normal(0, step_std)
        new_val = current + step
        return max(bounds[0], min(bounds[1], new_val))

    def _daily_pattern(self, base: float, amplitude: float) -> float:
        """Simulate time-of-day variation using a sine wave (period = 1440 min / 24h)."""
        phase = (self.tick % 720) / 720.0 * 2.0 * math.pi
        return base + amplitude * math.sin(phase)

    def generate(self) -> dict:
        self.tick += 1

        # Random walks with bounds
        self.turbidity_rw = self._random_walk(self.turbidity_rw, 1.5, (-15, 100))
        self.ph_rw = self._random_walk(self.ph_rw, 0.05, (-0.8, 1.2))
        self.conductivity_rw = self._random_walk(self.conductivity_rw, 15.0, (-300, 1000))
        self.flow_rate_rw = self._random_walk(self.flow_rate_rw, 0.3, (-5, 12))

        # Turbidity: base + random walk + occasional spike (5% chance)
        turbidity = self.base_turbidity + self.turbidity_rw
        if self.rng.random() < 0.10:
            turbidity += self.rng.uniform(30, 120)
        turbidity = max(0.5, round(turbidity, 1))

        # pH: base + random walk
        ph = round(self.base_ph + self.ph_rw, 2)
        ph = max(5.5, min(9.0, ph))

        # Conductivity: base + random walk
        conductivity = round(self.base_conductivity + self.conductivity_rw, 1)
        conductivity = max(50.0, min(2000.0, conductivity))

        # Temperature: daily pattern + slow drift
        temperature = round(self._daily_pattern(self.base_temperature, 3.0), 1)

        # Flow rate: base + random walk
        flow_rate = round(self.base_flow_rate + self.flow_rate_rw, 2)
        flow_rate = max(1.0, min(50.0, flow_rate))

        # Residual chlorine: random walk + decay + dosing boost
        self.current_residual += self.rng.normal(0, 0.08)
        decay_per_tick = self.rng.uniform(0.01, 0.04)
        self.current_residual = max(0.0, self.current_residual - decay_per_tick)
        self.current_residual = max(0.5, min(2.1, self.current_residual))
        self.current_residual = round(self.current_residual, 3)

        return {
            "turbidity": turbidity,
            "ph": ph,
            "conductivity": conductivity,
            "temperature": temperature,
            "residual_chlorine": self.current_residual,
            "pipeline_length": self.pipeline_length,
            "flow_rate": flow_rate,
            "target_residual_chlorine": self.target_residual,
            "pipe_diameter": self.pipe_diameter,
        }

    def apply_dose(self, dose_mgl: float):
        """Simulate applying chlorine dose — boosts residual chlorine."""
        self.last_applied_dose_mgl = dose_mgl
        self.current_residual += dose_mgl * 0.7
        self.current_residual = min(2.1, self.current_residual)
