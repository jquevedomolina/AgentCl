import time
import requests
import json
from datetime import datetime
from typing import Optional
from src.simulator.generator import WaterDataGenerator

API_URL = "http://localhost:8000"
INTERVAL_SECONDS = 60  # 1 minute
DEVIATION_THRESHOLD = 0.01  # 1%


class DosingSimulator:
    def __init__(self):
        self.generator = WaterDataGenerator()
        self.last_prediction: Optional[dict] = None
        self.last_dosing_rate: Optional[float] = None
        self.prediction_count = 0
        self.skip_count = 0
        self.start_time = datetime.now()

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
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[{self._ts()}] API error: {resp.status_code} {resp.text}")
                return None
        except requests.ConnectionError:
            print(f"[{self._ts()}] API not reachable")
            return None
        except Exception as e:
            print(f"[{self._ts()}] Error: {e}")
            return None

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _log(self, msg: str):
        print(f"[{self._ts()}] {msg}")

    def run(self, max_iterations: int = 0):
        buffer_config = {
            "water_volume": 100.0,
            "hypochlorite_purity": 65.0,
            "hypochlorite_weight": 500.0,
        }

        self._log("=== Chlorine Dosing Simulator Started ===")
        self._log(f"Interval: {INTERVAL_SECONDS}s | Threshold: {DEVIATION_THRESHOLD*100:.0f}%")
        self._log(f"Buffer: {buffer_config['water_volume']}L, {buffer_config['hypochlorite_purity']}%, {buffer_config['hypochlorite_weight']}g")

        iteration = 0
        try:
            while max_iterations == 0 or iteration < max_iterations:
                iteration += 1
                water_data = self.generator.generate()

                prediction = self._call_api(water_data, buffer_config)
                if prediction is None:
                    time.sleep(INTERVAL_SECONDS)
                    continue

                new_rate = prediction["dosing_rate_lh"]
                should_recalculate = True

                if self.last_dosing_rate is not None:
                    dev = self._deviation(new_rate, self.last_dosing_rate)
                    if dev <= DEVIATION_THRESHOLD:
                        should_recalculate = False
                        self.skip_count += 1

                if should_recalculate:
                    self.prediction_count += 1
                    self.last_dosing_rate = new_rate
                    self.last_prediction = prediction

                    # Apply dose to simulator
                    self.generator.apply_dose(prediction["initial_chlorine_dose_mgl"])

                    self._log(
                        f"#{iteration:04d} | "
                        f"Turb={water_data['turbidity']:.1f} "
                        f"pH={water_data['ph']:.2f} "
                        f"Cond={water_data['conductivity']:.0f} "
                        f"T={water_data['temperature']:.1f}°C "
                        f"Cl_res={water_data['residual_chlorine']:.3f} | "
                        f"DOSE={new_rate:.4f} L/h "
                        f"(init={prediction['initial_chlorine_dose_mgl']:.2f} mg/L, "
                        f"contact={prediction['contact_time_min']:.1f}min) "
                        f"conf={prediction['confidence']:.1%}"
                    )

                    if prediction["alarms"]:
                        for alarm in prediction["alarms"]:
                            self._log(f"  🚨 {alarm}")
                else:
                    self._log(
                        f"#{iteration:04d} | "
                        f"SKIP (dev={self._deviation(new_rate, self.last_dosing_rate)*100:.2f}%) | "
                        f"Turb={water_data['turbidity']:.1f} "
                        f"Cl_res={water_data['residual_chlorine']:.3f}"
                    )

                time.sleep(INTERVAL_SECONDS)

        except KeyboardInterrupt:
            self._log("Simulation stopped by user.")
        finally:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self._log(f"=== Summary ===")
            self._log(f"Runtime: {elapsed/60:.1f} min")
            self._log(f"Iterations: {iteration}")
            self._log(f"Recalculations: {self.prediction_count}")
            self._log(f"Skipped: {self.skip_count}")
            self._log(f"Efficiency: {self.skip_count/max(1,iteration)*100:.1f}% skipped")


def run_simulator():
    sim = DosingSimulator()
    sim.run()


if __name__ == "__main__":
    run_simulator()
