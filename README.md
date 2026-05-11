# 💧 Chlorine Dosing Agent

<div align="center">

**ML-powered calcium hypochlorite dosing agent for deep well water treatment**

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red.svg)](https://streamlit.io/)
[![MLflow](https://img.shields.io/badge/MLflow-2.19-orange.svg)](https://mlflow.org/)
[![Evidently](https://img.shields.io/badge/Evidently-0.6-purple.svg)](https://www.evidentlyai.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

</div>

---

## 📖 Overview

Intelligent system that predicts the optimal calcium hypochlorite dosing rate for deep well water disinfection. Combines water quality parameters with a machine learning model to deliver real-time, explainable dosing recommendations with drift monitoring and a human feedback loop.

### 🎯 Key Features

- **ML-Powered Predictions** — Linear regression model trained on water quality parameters
- **Chlorine Decay Kinetics** — First-order decay model calculates contact time and initial dose needed
- **Autonomous Decision-Making** — Agent decides whether to dose based on water quality and target residual
- **Real-Time Simulator** — Generates trending water quality data; agent makes autonomous dosing decisions
- **Real-Time Alarms** — Automatic alerts for turbidity, pH, conductivity, temperature, and residual chlorine anomalies
- **Explainability** — SHAP-based feature contribution analysis for every prediction
- **Drift Monitoring** — Evidently AI detects data distribution shifts and recommends retraining
- **Human Feedback Loop** — Operators can validate or correct predictions; system auto-flags retraining
- **Batch Processing** — Upload CSV files for bulk predictions
- **Tank Maintenance** — Built-in maintenance scheduler with alerts
- **MLflow Integration** — Experiment tracking and model versioning

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│                    Port :8501                            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                       │
│                    Port :8000                            │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Dosing  │ │  Buffer  │ │  Model   │ │Monitoring │  │
│  │  Slice   │ │  Slice   │ │Mgmt Slice│ │  Slice    │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐               │
│  │ Feedback │ │Maintenance│ │Simulator │               │
│  │  Slice   │ │  Slice    │ │  Slice   │               │
│  └──────────┘ └───────────┘ └──────────┘               │
│                                                         │
│              ┌──────────────────────┐                   │
│              │    Shared Kernel     │                   │
│              │   (ML Core Model)    │                   │
│              └──────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                    MLflow Server                         │
│                    Port :5000                            │
└─────────────────────────────────────────────────────────┘
```

### Vertical Slice Architecture

Each feature is a self-contained slice with its own router, service, and models:

```
src/
├── app.py                  # FastAPI entry point
├── shared/                 # Shared kernel
│   └── ml_core.py          # ML model (LinearRegression + StandardScaler)
├── dosing/                 # Dosing prediction slice
│   ├── router.py           # POST /dosing/predict, /dosing/predict_batch
│   ├── service.py          # Business logic
│   └── models.py           # Pydantic schemas
├── buffer/                 # Buffer solution slice
├── model_mgmt/             # Model management slice (retrain, explain, info)
├── monitoring/             # Drift monitoring slice (Evidently)
├── feedback/               # Human feedback slice
├── maintenance/            # Tank maintenance slice
└── simulator/              # Real-time simulation slice
    ├── generator.py        # Water data generator with trends
    ├── service.py          # Simulation loop + autonomous agent
    ├── router.py           # Start/stop/status/config endpoints
    ├── config.py           # Station configuration persistence
    └── form_state.py       # Form data persistence
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip / virtualenv

### 1. Clone & Install

```bash
git clone https://github.com/your-username/chlorine-dosing-agent.git
cd chlorine-dosing-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

The model auto-trains on synthetic data if no saved model is found.

### 3. Start the Frontend (optional)

```bash
streamlit run frontend/app.py
```

### 4. Start MLflow (optional)

```bash
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlflow/artifacts
```

### Docker

```bash
docker compose up --build
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API overview and endpoint listing |
| `GET` | `/health` | Health check + model version |
| `POST` | `/dosing/predict` | Single dosing prediction |
| `POST` | `/dosing/predict_batch` | Batch dosing predictions |
| `POST` | `/buffer/calculate` | Buffer solution concentration |
| `GET` | `/model/info` | Model metadata and feature importance |
| `POST` | `/model/retrain` | Trigger model retraining |
| `GET` | `/model/explain` | SHAP explainability |
| `GET` | `/monitoring/drift` | Data drift analysis |
| `POST` | `/feedback/` | Submit operator feedback |
| `GET` | `/feedback/stats` | Feedback accuracy statistics |
| `GET` | `/maintenance/` | Tank maintenance status |
| `POST` | `/maintenance/reset` | Reset maintenance timer |
| `POST` | `/simulator/start` | Start real-time simulation |
| `POST` | `/simulator/stop` | Stop simulation |
| `GET` | `/simulator/status` | Simulation status + history |
| `GET` | `/simulator/config` | Get station configuration |
| `POST` | `/simulator/config` | Save station configuration |

Full interactive docs: `http://localhost:8000/docs`

### Example: Dosing Prediction

```bash
curl -X POST "http://localhost:8000/dosing/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "water": {
      "turbidity": 25.0,
      "ph": 7.4,
      "conductivity": 600.0,
      "temperature": 23.0,
      "residual_chlorine": 0.4,
      "pipeline_length": 800.0,
      "flow_rate": 15.0,
      "target_residual_chlorine": 2.0,
      "pipe_diameter": 50.0
    },
    "buffer": {
      "water_volume": 100.0,
      "hypochlorite_purity": 65.0,
      "hypochlorite_weight": 500.0
    }
  }'
```

### Example Response

```json
{
  "prediction_id": "a1b2c3d4-...",
  "buffer_concentration_gpl": 3.25,
  "buffer_concentration_ppm": 3250.0,
  "dosing_rate_ls": 0.006923,
  "dosing_rate_lh": 0.0249,
  "dosing_rate_gpm": 0.1097,
  "dosing_rate_gph": 0.3950,
  "solution_duration_hours": 4016.06,
  "contact_time_min": 2.59,
  "initial_chlorine_dose_mgl": 2.15,
  "target_residual_mgl": 2.0,
  "should_dose": true,
  "confidence": 0.8723,
  "reasoning": "Dosing decision (confidence: 87.2%): ...",
  "alarms": [],
  "model_version": "v20260510152154",
  "timestamp": "2026-05-10T15:21:54.123456"
}
```

---

## 📊 Input Parameters

| Parameter | Unit | Description |
|-----------|------|-------------|
| `turbidity` | NTU | Water turbidity |
| `ph` | — | pH level (0–14) |
| `conductivity` | µS/cm | Electrical conductivity |
| `temperature` | °C | Water temperature |
| `residual_chlorine` | mg/L | Current residual chlorine |
| `pipeline_length` | m | Pipeline distance to tank |
| `flow_rate` | L/s | Raw water flow rate |
| `target_residual_chlorine` | mg/L | Target residual at pipeline end |
| `pipe_diameter` | mm | Pipe internal diameter |
| `water_volume` | L | Buffer solution volume |
| `hypochlorite_purity` | % | Calcium hypochlorite purity |
| `hypochlorite_weight` | g | Hypochlorite mass |

---

## 🧠 Model

- **Algorithm**: Linear Regression
- **Preprocessing**: StandardScaler (z-score normalization)
- **Training data**: 1,000 synthetic samples covering realistic water quality ranges
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Versioning**: MLflow with automatic version tracking

### Retraining

```bash
python train.py
```

This generates fresh synthetic data, trains a new model, logs metrics to MLflow, and saves artifacts to `models/`.

---

## 📈 Monitoring

Evidently AI checks for data drift between reference and current prediction distributions. When drift exceeds a 30% threshold across features, the system recommends retraining.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI + Pydantic v2 |
| Frontend | Streamlit |
| ML Model | scikit-learn (LinearRegression) |
| Explainability | SHAP |
| Experiment Tracking | MLflow |
| Drift Monitoring | Evidently AI |
| Containerization | Docker + Docker Compose |

---

## 📁 Project Structure

```
chlorine-dosing-agent/
├── src/
│   ├── app.py
│   ├── shared/ml_core.py
│   ├── dosing/{router,service,models}.py
│   ├── buffer/{router,service,models}.py
│   ├── model_mgmt/{router,service,models}.py
│   ├── monitoring/{router,service,models}.py
│   ├── feedback/{router,service,models}.py
│   ├── maintenance/{router,service,models}.py
│   └── simulator/{generator,service,router,config,form_state}.py
├── frontend/app.py
├── data/
│   ├── station_setup.json
│   └── last_dosing_form.json
├── models/
├── train.py
├── simulate.py
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── requirements.txt
└── .env
```

---

## 📄 License

MIT © 2026
