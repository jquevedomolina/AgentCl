from datetime import datetime
from src.feedback.models import FeedbackInput, FeedbackResponse


class FeedbackService:

    def __init__(self):
        self.store: dict = {}

    def submit(self, feedback: FeedbackInput) -> FeedbackResponse:
        self.store[feedback.prediction_id] = {
            "actual_dosing_rate": feedback.actual_dosing_rate,
            "was_correct": feedback.was_correct,
            "operator_notes": feedback.operator_notes,
            "timestamp": datetime.now()
        }

        incorrect_count = sum(1 for f in self.store.values() if not f["was_correct"])
        retrain = incorrect_count >= 10

        return FeedbackResponse(
            status="received",
            message="Feedback recorded. Retraining recommended." if retrain else "Feedback recorded successfully.",
            retrain_recommended=retrain,
            total_feedback=len(self.store),
            incorrect_count=incorrect_count
        )

    def get_stats(self) -> dict:
        total = len(self.store)
        if total == 0:
            return {"total": 0, "correct": 0, "incorrect": 0, "accuracy": 0.0}
        correct = sum(1 for f in self.store.values() if f["was_correct"])
        return {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
            "accuracy": round(correct / total, 4)
        }


feedback_service = FeedbackService()
