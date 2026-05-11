from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class WaterQualityInput(BaseModel):
    turbidity: float = Field(..., description="Turbidity (NTU)")
    ph: float = Field(..., ge=0, le=14, description="pH level")
    conductivity: float = Field(..., description="Conductivity (µS/cm)")
    temperature: float = Field(..., description="Water temperature (°C)")
    residual_chlorine: float = Field(..., description="Current residual chlorine at source (mg/L)")
    pipeline_length: float = Field(..., description="Pipeline length to tank (m)")
    flow_rate: float = Field(..., description="Raw water flow rate (L/s)")
    target_residual_chlorine: float = Field(default=2.0, description="Target residual chlorine at pipeline end (mg/L)")
    pipe_diameter: float = Field(default=50.0, description="Pipe internal diameter (mm)")


class BufferConfig(BaseModel):
    water_volume: float = Field(..., description="Water volume for solution (L)")
    hypochlorite_purity: float = Field(..., ge=0, le=100, description="Hypochlorite purity (%)")
    hypochlorite_weight: float = Field(..., description="Hypochlorite weight (g)")


class DosingPrediction(BaseModel):
    prediction_id: str
    buffer_concentration_gpl: float
    buffer_concentration_ppm: float
    dosing_rate_ls: float
    dosing_rate_lh: float
    dosing_rate_gpm: float
    dosing_rate_gph: float
    solution_duration_hours: float
    contact_time_min: float
    initial_chlorine_dose_mgl: float
    target_residual_mgl: float
    should_dose: bool
    confidence: float
    reasoning: str
    alarms: List[str]
    model_version: str
    timestamp: datetime


class PredictRequest(BaseModel):
    water: WaterQualityInput
    buffer: BufferConfig


class BatchRequest(BaseModel):
    samples: List[WaterQualityInput]
    buffer_config: BufferConfig


class BatchResponse(BaseModel):
    predictions: List[DosingPrediction]
