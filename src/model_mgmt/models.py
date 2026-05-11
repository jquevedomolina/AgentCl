from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ModelInfo(BaseModel):
    model_version: str
    feature_names: list
    feature_importance: dict
    trained_at: datetime


class RetrainResponse(BaseModel):
    status: str
    model_version: str
    message: Optional[str] = None


class ExplainResponse(BaseModel):
    method: str
    feature_contributions: dict
    base_value: float
