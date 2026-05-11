from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedbackInput(BaseModel):
    prediction_id: str
    actual_dosing_rate: float
    was_correct: bool
    operator_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str
    message: str
    retrain_recommended: bool
    total_feedback: int
    incorrect_count: int
