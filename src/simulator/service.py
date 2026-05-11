import threading
import time
import requests
import os
from datetime import datetime
from typing import Optional, List
from src.simulator.generator import WaterDataGenerator
from src.simulator.config import load_config, StationConfig

API_URL = os.environ.get("API_URL", "http://localhost:8000")
INTERVAL_SECONDS = 60
DEVIATION_THRESHOLD = 0.01


class SimulatorState:
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.generator = WaterDataGenerator()
        self.last_prediction: Optional[dict] = None
        self.last_water_data: Optional[dict] = None
        self.last_dosing_rate: Optional[float] = None
        self.prediction_count = 0
        self.skip_count = 0
        self.doses_applied = 0
        self.doses_skipped = 0
        self.iteration = 0
        self.history: List[dict] = []
        self.started_at: Optional[datetime] = None

    def _deviation(self, new_rate: float, last_rate: float) -> float:
        if last_rate == 0:
            return 1.0 if new_rate != 0 else 0.0
        return abs(new_rate - last_rate) / abs(last_rate)

    def _call_api(self, water_data: dict, buffer_config: dict) -> Optional[dict]:
        try:
            resp = requests.post(
                f"{API_URL}/dosing/predict",
                json={"water": water_data, "buffer": buffer_config},
                timeout=10,
            )
            return resp.json() if resp.status_code == 200 else None
        except:
            return None

    def _loop(self):
        cfg = load_config()
        buffer_config = {
            "water_volume": cfg.tank_volume_l,
            "hypochlorite_purity": cfg.hypochlorite_purity_pct,
            "hypochlorite_weight": cfg.hypochlorite_weight_g,
        }

        # Apply station config to generator
        self.generator.pipeline_length = cfg.pipeline_length_m
        self.generator.pipe_diameter = cfg.pipe_diameter_mm
        self.generator.target_residual = cfg.target_residual_mgl

        while self.running:
            self.iteration += 1
            water_data = self.generator.generate()
            self.last_water_data = water_data

            # Decide whether to call API (skip if deviation < 1%)
            should_call_api = True
            if self.last_prediction is not None and self.last_dosing_rate is not None:
                # Use last prediction to estimate what new rate would be
                # If last prediction is stale, always call API
                should_call_api = False  # Will be set to True below if needed

            # Always call API — the agent must decide every tick
            prediction = self._call_api(water_data, buffer_config)

            if prediction is None:
                time.sleep(INTERVAL_SECONDS)
                continue

            new_rate = prediction["dosing_rate_lh"]
            agent_says_dose = prediction["should_dose"]

            # Check deviation from last applied dose
            api_called = True
            if self.last_dosing_rate is not None:
                if self._deviation(new_rate, self.last_dosing_rate) <= DEVIATION_THRESHOLD:
                    api_called = False
                    self.skip_count += 1

            # Apply agent's decision
            dosed = False
            if agent_says_dose:
                if api_called:
                    self.prediction_count += 1
                    self.last_dosing_rate = new_rate
                    self.last_prediction = prediction
                self.generator.apply_dose(prediction["initial_chlorine_dose_mgl"])
                self.doses_applied += 1
                dosed = True
            else:
                self.doses_skipped += 1

            entry = {
                "iteration": self.iteration,
                "timestamp": datetime.now().isoformat(),
                "turbidity": water_data["turbidity"],
                "ph": water_data["ph"],
                "conductivity": water_data["conductivity"],
                "temperature": water_data["temperature"],
                "residual_chlorine": water_data["residual_chlorine"],
                "flow_rate": water_data["flow_rate"],
                "dosing_rate_lh": new_rate,
                "initial_dose_mgl": prediction["initial_chlorine_dose_mgl"],
                "contact_time_min": prediction["contact_time_min"],
                "confidence": prediction["confidence"],
                "should_dose": agent_says_dose,
                "agent_dosed": dosed,
                "api_called": api_called,
                "reasoning": prediction["reasoning"],
                "alarms": prediction["alarms"],
            }

            self.history.append(entry)
            if len(self.history) > 500:
                self.history = self.history[-300:]

            time.sleep(INTERVAL_SECONDS)

    def start(self):
        if self.running:
            return False
        self.running = True
        self.started_at = datetime.now()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        return True

    def status(self) -> dict:
        return {
            "running": self.running,
            "iteration": self.iteration,
            "prediction_count": self.prediction_count,
            "skip_count": self.skip_count,
            "doses_applied": self.doses_applied,
            "doses_skipped": self.doses_skipped,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_water_data": self.last_water_data,
            "last_prediction": self.last_prediction,
            "history": self.history[-50:],
        }


simulator_state = SimulatorState()
