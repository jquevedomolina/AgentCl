import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
from datetime import datetime

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("chlorine_dosing_agent")


def generate_synthetic_data(n_samples: int = 2000) -> tuple:
    np.random.seed(42)

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

    feature_names = [
        "turbidity", "ph", "conductivity", "temperature",
        "residual_chlorine", "pipeline_length", "flow_rate",
        "buffer_concentration"
    ]

    df = pd.DataFrame(X, columns=feature_names)
    df["target_dose"] = y

    return X, y, feature_names, df


def train():
    print("Generating synthetic training data...")
    X, y, feature_names, df = generate_synthetic_data(2000)

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(os.path.join(DATA_DIR, "reference_data.csv"), index=False)
    print(f"Saved reference data to {DATA_DIR}/reference_data.csv")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    with mlflow.start_run(run_name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = LinearRegression()
        model.fit(X_train_scaled, y_train)

        y_pred = model.predict(X_test_scaled)

        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"Model metrics:")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAE: {mae:.4f}")
        print(f"  R²: {r2:.4f}")

        mlflow.log_params({
            "model_type": "LinearRegression",
            "n_features": len(feature_names),
            "n_train_samples": len(X_train),
            "n_test_samples": len(X_test),
            "random_seed": 42
        })

        mlflow.log_metrics({
            "rmse": rmse,
            "mae": mae,
            "r2": r2
        })

        for name, coef in zip(feature_names, model.coef_):
            mlflow.log_metric(f"coef_{name}", coef)
        mlflow.log_metric("intercept", model.intercept_)

        mlflow.sklearn.log_model(model, "model")

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, os.path.join(MODEL_DIR, "dosing_model.pkl"))
        joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))

        version = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"
        with open(os.path.join(MODEL_DIR, "version.txt"), "w") as f:
            f.write(version)

        print(f"\nModel saved: {version}")
        print(f"MLflow run ID: {mlflow.active_run().info.run_id}")

        return model, scaler, version


if __name__ == "__main__":
    train()
