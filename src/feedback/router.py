from fastapi import APIRouter
from src.feedback.models import FeedbackInput, FeedbackResponse
from src.feedback.service import feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackInput):
    return feedback_service.submit(feedback)


@router.get("/stats")
async def feedback_stats():
    return feedback_service.get_stats()
