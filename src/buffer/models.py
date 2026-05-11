from pydantic import BaseModel, Field


class BufferRequest(BaseModel):
    water_volume: float = Field(..., description="Water volume for solution (L)")
    hypochlorite_purity: float = Field(..., ge=0, le=100, description="Hypochlorite purity (%)")
    hypochlorite_weight: float = Field(..., description="Hypochlorite weight (g)")


class BufferResponse(BaseModel):
    concentration_gpl: float
    concentration_ppm: float
    concentration_mll: float
    active_chlorine_g: float
