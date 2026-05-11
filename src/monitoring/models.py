from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DriftReport(BaseModel):
    drift_detected: bool
    drift_score: float
    feature_drifts: dict
    recommended_action: str
    timestamp: datetime


class PredictionLog(BaseModel):
    turbidity: float
    ph: float
    conductivity: float
    temperature: float
    residual_chlorine: float
    pipeline_length: float
    flow_rate: float
    buffer_concentration: float
