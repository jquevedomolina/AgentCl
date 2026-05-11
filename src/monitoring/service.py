import numpy as np
import pandas as pd
import os
import json
from datetime import datetime
from typing import List

from src.monitoring.models import DriftReport, PredictionLog

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")


class MonitoringService:

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.reference_data: pd.DataFrame = None
        self.current_data: List[dict] = []
        self._load_reference_data()

    def _load_reference_data(self):
        ref_path = os.path.join(DATA_DIR, "reference_data.csv")
        if os.path.exists(ref_path):
            self.reference_data = pd.read_csv(ref_path)
        else:
            self._generate_reference_data()

    def _generate_reference_data(self):
        np.random.seed(42)
        self.reference_data = pd.DataFrame({
            "turbidity": np.random.uniform(0, 50, 500),
            "ph": np.random.uniform(6.5, 8.5, 500),
            "conductivity": np.random.uniform(100, 1500, 500),
            "temperature": np.random.uniform(10, 30, 500),
            "residual_chlorine": np.random.uniform(0.2, 2.0, 500),
            "pipeline_length": np.random.uniform(50, 3000, 500),
            "flow_rate": np.random.uniform(1, 50, 500),
            "buffer_concentration": np.random.uniform(10, 100, 500),
        })
        self.reference_data.to_csv(os.path.join(DATA_DIR, "reference_data.csv"), index=False)

    def log_prediction(self, features: dict):
        self.current_data.append(features)
        if len(self.current_data) > 1000:
            self.current_data = self.current_data[-500:]

    def check_drift(self) -> DriftReport:
        if len(self.current_data) < 50:
            return DriftReport(
                drift_detected=False, drift_score=0.0, feature_drifts={},
                recommended_action="insufficient_data", timestamp=datetime.now()
            )

        current_df = pd.DataFrame(self.current_data[-200:])

        try:
            from evidently.report import Report
            from evidently.metric_preset import DataDriftPreset

            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=self.reference_data, current_data=current_df)
            report_json = json.loads(report.json())

            metrics = report_json.get("metrics", [])
            result = {"drift_detected": False, "drift_score": 0.0, "feature_drifts": {}}

            for metric in metrics:
                if metric.get("metric") == "DataDriftTable":
                    drift_by_columns = metric.get("result", {}).get("drift_by_columns", {})
                    drifted_count = 0
                    total = 0
                    for col_name, col_data in drift_by_columns.items():
                        total += 1
                        drift_detected = col_data.get("drift_detected", False)
                        drift_score = col_data.get("drift_score", 0.0)
                        result["feature_drifts"][col_name] = {
                            "drift_detected": drift_detected,
                            "drift_score": drift_score
                        }
                        if drift_detected:
                            drifted_count += 1
                    result["drift_score"] = drifted_count / max(total, 1)
                    result["drift_detected"] = result["drift_score"] > 0.3

            return DriftReport(
                drift_detected=result["drift_detected"],
                drift_score=result["drift_score"],
                feature_drifts=result["feature_drifts"],
                recommended_action="retrain_recommended" if result["drift_detected"] else "no_action_needed",
                timestamp=datetime.now()
            )
        except Exception as e:
            return DriftReport(
                drift_detected=False, drift_score=0.0, feature_drifts={},
                recommended_action=f"error: {str(e)}", timestamp=datetime.now()
            )

    def update_reference(self, new_data: pd.DataFrame):
        self.reference_data = new_data
        new_data.to_csv(os.path.join(DATA_DIR, "reference_data.csv"), index=False)


monitoring_service = MonitoringService()
