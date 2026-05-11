import json
import os
from pydantic import BaseModel, Field

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "station_setup.json")


class StationConfig(BaseModel):
    pipe_diameter_mm: float = Field(default=50.0, description="Pipe internal diameter (mm)")
    pipeline_length_m: float = Field(default=800.0, description="Pipeline length (m)")
    target_residual_mgl: float = Field(default=2.0, description="Target residual chlorine at endpoint (mg/L)")
    tank_volume_l: float = Field(default=100.0, description="Buffer tank volume (L)")
    hypochlorite_purity_pct: float = Field(default=65.0, description="Hypochlorite purity (%)")
    hypochlorite_weight_g: float = Field(default=500.0, description="Hypochlorite weight per batch (g)")


def load_config() -> StationConfig:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return StationConfig(**json.load(f))
    cfg = StationConfig()
    save_config(cfg)
    return cfg


def save_config(cfg: StationConfig):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg.model_dump(), f, indent=2)
