from fastapi import APIRouter
from src.monitoring.models import DriftReport
from src.monitoring.service import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/drift", response_model=DriftReport)
async def check_drift():
    return monitoring_service.check_drift()
