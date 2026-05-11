import numpy as np
import pandas as pd
import os
from datetime import datetime

from src.shared.ml_core import ml_core
from src.model_mgmt.models import ModelInfo, RetrainResponse, ExplainResponse

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")


class ModelMgmtService:

    def get_info(self) -> ModelInfo:
        return ModelInfo(
            model_version=ml_core.model_version,
            feature_names=ml_core.feature_names,
            feature_importance=ml_core.get_feature_importance(),
            trained_at=datetime.now()
        )

    def retrain(self) -> RetrainResponse:
        data_path = os.path.join(DATA_DIR, "reference_data.csv")
        if not os.path.exists(data_path):
            return RetrainResponse(
                status="skipped",
                model_version=ml_core.model_version,
                message="No training data available"
            )

        df = pd.read_csv(data_path)
        X = df.values
        y = (0.02 * X[:, 0] + 0.5 * (8.5 - X[:, 1]) + 0.001 * X[:, 2] +
             0.01 * X[:, 3] - 0.3 * X[:, 4] + 0.0005 * X[:, 5] +
             0.01 * X[:, 6] + 0.005 * X[:, 7] + 1.5)

        new_version = ml_core.retrain(X, y)
        return RetrainResponse(status="retrained", model_version=new_version)

    def explain(self, features: np.ndarray, method: str = "shap") -> ExplainResponse:
        try:
            import shap
            features_scaled = ml_core.scaler.transform(features.reshape(1, -1))
            explainer = shap.LinearExplainer(
                ml_core.model,
                np.zeros((1, features_scaled.shape[1]))
            )
            shap_values = explainer.shap_values(features_scaled)
            return ExplainResponse(
                method="SHAP",
                feature_contributions=dict(zip(ml_core.feature_names, shap_values[0].tolist())),
                base_value=float(explainer.expected_value)
            )
        except Exception:
            return ExplainResponse(
                method="coefficients",
                feature_contributions=ml_core.get_feature_importance(),
                base_value=ml_core.model.intercept_
            )


model_mgmt_service = ModelMgmtService()
