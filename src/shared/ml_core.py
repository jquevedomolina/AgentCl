import numpy as np
import joblib
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "models")


class DosingModelCore:
    def __init__(self):
        self.model: LinearRegression = None
        self.scaler: StandardScaler = None
        self.model_version: str = None
        self.feature_names = [
            "turbidity", "ph", "conductivity", "temperature",
            "residual_chlorine", "pipeline_length", "flow_rate",
            "buffer_concentration"
        ]
        self._load_or_create()

    def _load_or_create(self):
        model_path = os.path.join(MODEL_DIR, "dosing_model.pkl")
        scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
        version_path = os.path.join(MODEL_DIR, "version.txt")

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            if os.path.exists(version_path):
                with open(version_path) as f:
                    self.model_version = f.read().strip()
        else:
            self._train_initial_model()

    def _train_initial_model(self):
        np.random.seed(42)
        n_samples = 1000
        X = np.random.uniform(
            low=[0, 5, 50, 5, 0, 50, 1, 10],
            high=[100, 9, 2000, 35, 2, 5000, 100, 200],
            size=(n_samples, 8)
        )
        target_chlorine = 1.5
        y = (0.02 * X[:, 0] + 0.5 * (8.5 - X[:, 1]) + 0.001 * X[:, 2] +
             0.01 * X[:, 3] - 0.3 * X[:, 4] + 0.0005 * X[:, 5] +
             0.01 * X[:, 6] + 0.005 * X[:, 7] + target_chlorine +
             np.random.normal(0, 0.1, n_samples))
        y = np.maximum(y, 0.1)

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)
        self.model_version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._save()

    def _save(self):
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.model, os.path.join(MODEL_DIR, "dosing_model.pkl"))
        joblib.dump(self.scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
        with open(os.path.join(MODEL_DIR, "version.txt"), "w") as f:
            f.write(self.model_version)

    def predict(self, features: np.ndarray) -> tuple:
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        prediction = float(self.model.predict(features_scaled)[0])
        residuals = features_scaled - self.scaler.mean_
        confidence = 1.0 / (1.0 + np.abs(residuals).mean())
        confidence = max(0.5, min(0.99, confidence))
        return prediction, confidence

    def retrain(self, X: np.ndarray, y: np.ndarray) -> str:
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)
        self.model_version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._save()
        return self.model_version

    def get_feature_importance(self) -> dict:
        if self.model is None:
            return {}
        return dict(zip(self.feature_names, self.model.coef_.tolist()))


ml_core = DosingModelCore()
